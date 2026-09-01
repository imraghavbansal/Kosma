import uuid
from datetime import datetime

from pydantic import BaseModel


class AgentConfigOut(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    kind: str
    version_label: str
    prompt_text: str | None
    model_provider: str | None
    model_name: str | None
    is_baseline: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    configs: list[AgentConfigOut] = []

    model_config = {"from_attributes": True}


class AgentListOut(BaseModel):
    items: list[AgentOut]
