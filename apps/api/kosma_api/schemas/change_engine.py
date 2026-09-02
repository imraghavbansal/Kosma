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
    evidence_tier: str

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
    evidence_basis: str
    limitations: list[str]
    recommended_next_action: str

    model_config = {"from_attributes": True}


class RegressionTestOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    impact_report_id: uuid.UUID | None
    source_trace_id: uuid.UUID
    input_text: str
    context_snapshot: dict
    expected_condition: str
    baseline_output: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RegressionTestListOut(BaseModel):
    items: list[RegressionTestOut]
    total: int


class PredictionOutcomeOut(BaseModel):
    id: uuid.UUID
    change_proposal_id: uuid.UUID
    predicted_metrics: dict
    actual_metrics: dict
    prediction_error: dict
    evaluated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
