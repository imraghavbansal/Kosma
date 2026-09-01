import uuid
from datetime import datetime

from pydantic import BaseModel


class ChangeProposalIn(BaseModel):
    agent_id: uuid.UUID
    baseline_config_id: uuid.UUID
    candidate_config_id: uuid.UUID
    description: str | None = None


class ChangeProposalOut(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    baseline_config_id: uuid.UUID
    candidate_config_id: uuid.UUID
    description: str | None
    status: str
    shipped_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeProposalListOut(BaseModel):
    items: list[ChangeProposalOut]
    total: int


class ImpactEvidenceOut(BaseModel):
    id: uuid.UUID
    segment: str | None
    baseline_trace_id: uuid.UUID
    replay_trace_id: uuid.UUID
    note: str | None

    model_config = {"from_attributes": True}


class ImpactReportOut(BaseModel):
    id: uuid.UUID
    change_proposal_id: uuid.UUID
    cohort_size: int
    sample_size: int
    recommendation: str
    confidence: float
    overall_metrics: dict
    segment_metrics: list[dict]
    evidence: list[ImpactEvidenceOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}
