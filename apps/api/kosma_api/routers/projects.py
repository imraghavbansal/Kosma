"""Projects as the real unit a user works in: each one can optionally be
linked to a real GitHub repo (github_repo = "owner/name"), so its detail page
can show that repo's real commits/PRs next to Kosma's own real trace and
change-proposal history for it. Linking is explicit (PATCH) - nothing here
invents a connection that doesn't exist."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from kosma_api.auth import require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.agent import Agent
from kosma_api.models.change_proposal import ChangeProposal
from kosma_api.models.project import Project
from kosma_api.models.trace import Trace
from kosma_api.schemas.projects import ProjectDetailOut, ProjectPatchIn, ProjectSummaryListOut, ProjectSummaryOut

router = APIRouter(prefix="/v1/projects", tags=["projects"], dependencies=[Depends(require_dashboard_session)])


@router.get("", response_model=ProjectSummaryListOut)
def list_projects(db: Session = Depends(get_db)) -> ProjectSummaryListOut:
    projects = db.scalars(select(Project)).all()
    items = []
    for p in projects:
        agent_count = db.scalar(select(func.count()).select_from(Agent).where(Agent.project_id == p.id)) or 0
        trace_count = db.scalar(select(func.count()).select_from(Trace).where(Trace.project_id == p.id)) or 0
        cp_count = (
            db.scalar(select(func.count()).select_from(ChangeProposal).where(ChangeProposal.project_id == p.id))
            or 0
        )
        items.append(
            ProjectSummaryOut(
                id=p.id,
                name=p.name,
                github_repo=p.github_repo,
                agent_count=agent_count,
                trace_count=trace_count,
                change_proposal_count=cp_count,
                created_at=p.created_at,
            )
        )
    return ProjectSummaryListOut(items=items)


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
    )


@router.patch("/{project_id}", response_model=ProjectSummaryOut)
def patch_project(project_id: uuid.UUID, body: ProjectPatchIn, db: Session = Depends(get_db)) -> ProjectSummaryOut:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    repo = body.github_repo.strip() if body.github_repo else None
    if repo is not None and "/" not in repo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="github_repo must look like owner/name")

    project.github_repo = repo
    db.commit()
    db.refresh(project)

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
    )
