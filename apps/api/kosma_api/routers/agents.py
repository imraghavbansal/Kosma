from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from kosma_api.auth import require_dashboard_session
from kosma_api.db.session import get_db
from kosma_api.models.agent import Agent
from kosma_api.schemas.agents import AgentListOut, AgentOut

router = APIRouter(prefix="/v1/agents", tags=["agents"], dependencies=[Depends(require_dashboard_session)])


@router.get("", response_model=AgentListOut)
def list_agents(db: Session = Depends(get_db)) -> AgentListOut:
    agents = db.scalars(select(Agent).options(selectinload(Agent.configs))).all()
    return AgentListOut(items=agents)
