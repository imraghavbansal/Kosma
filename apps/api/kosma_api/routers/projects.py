"""Projects as the real unit a user works in: each one can optionally be
linked to a real GitHub repo (github_repo = "owner/name"), so its detail page
can show that repo's real commits/PRs next to Kosma's own real trace and
change-proposal history for it. Linking is explicit (PATCH) - nothing here
invents a connection that doesn't exist."""

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from kosma_api.auth import hash_api_key, require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.agent import Agent
from kosma_api.models.agent_config import AgentConfig, AgentConfigKind
from kosma_api.models.change_proposal import ChangeProposal
from kosma_api.models.organization import Organization
from kosma_api.models.project import Project
from kosma_api.models.trace import Trace
from kosma_api.schemas.projects import (
    ApiKeyOut,
    ProjectCreateIn,
    ProjectCreatedOut,
    ProjectDetailOut,
    ProjectPatchIn,
    ProjectSummaryListOut,
    ProjectSummaryOut,
)

router = APIRouter(prefix="/v1/projects", tags=["projects"], dependencies=[Depends(require_dashboard_session)])


def _summary(project: Project, db: Session) -> ProjectSummaryOut:
    agent_count = db.scalar(select(func.count()).select_from(Agent).where(Agent.project_id == project.id)) or 0
    trace_count = db.scalar(select(func.count()).select_from(Trace).where(Trace.project_id == project.id)) or 0
    cp_count = (
        db.scalar(select(func.count()).select_from(ChangeProposal).where(ChangeProposal.project_id == project.id))
        or 0
    )
    return ProjectSummaryOut(
        id=project.id,
        name=project.name,
        github_repo=project.github_repo,
        agent_count=agent_count,
        trace_count=trace_count,
        change_proposal_count=cp_count,
        created_at=project.created_at,
        real_replay_configured=bool(project.llm_provider and project.llm_api_key),
        llm_provider=project.llm_provider,
    )


@router.post("", response_model=ProjectCreatedOut, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreateIn, db: Session = Depends(get_db)) -> ProjectCreatedOut:
    """Real self-serve onboarding: creates an org/project/agent/baseline
    config and returns a real, usable API key. This is the actual bridge
    from "seeded demo data" to "a real user's real traces" - without this,
    nobody could ever get real data into Kosma."""
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")

    repo = body.github_repo.strip() if body.github_repo else None
    if repo is not None and "/" not in repo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="github_repo must look like owner/name")

    raw_api_key = f"kosma_live_{secrets.token_urlsafe(32)}"

    org = Organization(name=name)
    db.add(org)
    db.flush()

    project = Project(organization_id=org.id, name=name, api_key_hash=hash_api_key(raw_api_key), github_repo=repo)
    db.add(project)
    db.flush()

    agent = Agent(project_id=project.id, name="Default Agent")
    db.add(agent)
    db.flush()

    config = AgentConfig(
        agent_id=agent.id,
        kind=AgentConfigKind.model,
        version_label="v1-baseline",
        is_baseline=True,
    )
    db.add(config)
    db.commit()
    db.refresh(project)
    db.refresh(agent)
    db.refresh(config)

    return ProjectCreatedOut(
        id=project.id,
        name=project.name,
        github_repo=project.github_repo,
        api_key=raw_api_key,
        agent_id=agent.id,
        agent_config_id=config.id,
    )


@router.get("", response_model=ProjectSummaryListOut)
def list_projects(db: Session = Depends(get_db)) -> ProjectSummaryListOut:
    projects = db.scalars(select(Project)).all()
    return ProjectSummaryListOut(items=[_summary(p, db) for p in projects])


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> ProjectDetailOut:
    project = db.get(Project, project_id, options=[selectinload(Project.agents).selectinload(Agent.configs)])
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    trace_count = db.scalar(select(func.count()).select_from(Trace).where(Trace.project_id == project.id)) or 0
    proposals = db.scalars(
        select(ChangeProposal).where(ChangeProposal.project_id == project.id).order_by(ChangeProposal.created_at.desc())
    ).all()

    return ProjectDetailOut(
        id=project.id,
        name=project.name,
        github_repo=project.github_repo,
        trace_count=trace_count,
        created_at=project.created_at,
        agents=project.agents,
        change_proposals=proposals,
        real_replay_configured=bool(project.llm_provider and project.llm_api_key),
        llm_provider=project.llm_provider,
    )


@router.post("/{project_id}/regenerate-key", response_model=ApiKeyOut)
def regenerate_key(project_id: uuid.UUID, db: Session = Depends(get_db)) -> ApiKeyOut:
    """Invalidates the project's current API key and issues a new one - for
    when a key is lost, since (like any real API key) it's never stored or
    shown in plaintext after creation."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    raw_api_key = f"kosma_live_{secrets.token_urlsafe(32)}"
    project.api_key_hash = hash_api_key(raw_api_key)
    db.commit()
    return ApiKeyOut(api_key=raw_api_key)


@router.patch("/{project_id}", response_model=ProjectSummaryOut)
def patch_project(project_id: uuid.UUID, body: ProjectPatchIn, db: Session = Depends(get_db)) -> ProjectSummaryOut:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Only touch fields the caller actually sent - e.g. linking a repo must
    # never silently wipe an already-configured llm_api_key just because
    # that request didn't mention it.
    fields_sent = body.model_fields_set

    if "github_repo" in fields_sent:
        repo = body.github_repo.strip() if body.github_repo else None
        if repo is not None and "/" not in repo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="github_repo must look like owner/name"
            )
        project.github_repo = repo

    if "llm_provider" in fields_sent:
        provider = body.llm_provider.strip() if body.llm_provider else None
        if provider is not None and provider not in ("openai", "anthropic"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="llm_provider must be 'openai' or 'anthropic'"
            )
        project.llm_provider = provider

    if "llm_api_key" in fields_sent:
        project.llm_api_key = body.llm_api_key.strip() if body.llm_api_key else None

    db.commit()
    db.refresh(project)
    return _summary(project, db)
