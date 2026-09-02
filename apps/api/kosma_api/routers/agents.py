import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from kosma_api.auth import require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.agent import Agent
from kosma_api.models.agent_config import AgentConfig, AgentConfigKind
from kosma_api.schemas.agents import AgentConfigIn, AgentConfigOut, AgentListOut, AgentOut

router = APIRouter(prefix="/v1/agents", tags=["agents"], dependencies=[Depends(require_dashboard_session)])


@router.get("", response_model=AgentListOut)
def list_agents(db: Session = Depends(get_db)) -> AgentListOut:
    agents = db.scalars(select(Agent).options(selectinload(Agent.configs))).all()
    return AgentListOut(items=agents)


@router.post("/{agent_id}/configs", response_model=AgentConfigOut, status_code=status.HTTP_201_CREATED)
def create_agent_config(agent_id: uuid.UUID, body: AgentConfigIn, db: Session = Depends(get_db)) -> AgentConfig:
    """Registers a new prompt/model version for an agent - the actual missing
    piece behind "Propose a Change": a fresh self-serve project starts with
    only its baseline config, and without this endpoint there was no way to
    ever create a candidate to propose a change against."""
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    if body.kind not in (AgentConfigKind.prompt.value, AgentConfigKind.model.value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="kind must be 'prompt' or 'model'")

    version_label = body.version_label.strip()
    if not version_label:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="version_label is required")

    config = AgentConfig(
        agent_id=agent.id,
        kind=AgentConfigKind(body.kind),
        version_label=version_label,
        prompt_text=body.prompt_text,
        model_provider=body.model_provider,
        model_name=body.model_name,
        is_baseline=body.is_baseline,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config
