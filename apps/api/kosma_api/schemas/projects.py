import uuid
from datetime import datetime

from pydantic import BaseModel

from kosma_api.schemas.agents import AgentOut
from kosma_api.schemas.change_engine import ChangeProposalOut


class ProjectSummaryOut(BaseModel):
    id: uuid.UUID
    name: str
    github_repo: str | None
    agent_count: int
    trace_count: int
    change_proposal_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummaryListOut(BaseModel):
    items: list[ProjectSummaryOut]


class ProjectDetailOut(BaseModel):
    id: uuid.UUID
    name: str
    github_repo: str | None
    trace_count: int
    created_at: datetime
    agents: list[AgentOut]
    change_proposals: list[ChangeProposalOut]

    model_config = {"from_attributes": True}


class ProjectPatchIn(BaseModel):
    github_repo: str | None = None


class ProjectCreateIn(BaseModel):
    name: str
    github_repo: str | None = None


class ProjectCreatedOut(BaseModel):
    id: uuid.UUID
    name: str
    github_repo: str | None
    api_key: str
    agent_id: uuid.UUID
    agent_config_id: uuid.UUID
