import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from kosma_api.models.span import SpanType
from kosma_api.models.trace import TraceStatus


class ToolCallIn(BaseModel):
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    result: dict = Field(default_factory=dict)
    valid_arguments: bool = True
    success: bool = True


class RetrievalEventIn(BaseModel):
    query: str
    documents: list[dict] = Field(default_factory=list)


class SpanIn(BaseModel):
    ref: str
    parent_ref: str | None = None
    span_type: SpanType
    name: str
    input: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    latency_ms: int = 0
    error: str | None = None
    tool_call: ToolCallIn | None = None
    retrieval_event: RetrievalEventIn | None = None


class TraceIn(BaseModel):
    trace_ref: str
    agent_id: uuid.UUID
    agent_config_id: uuid.UUID
    workflow_tag: str | None = None
    segment_tags: dict = Field(default_factory=dict)
    input_text: str
    model_provider: str | None = None
    model_name: str | None = None
    status: TraceStatus = TraceStatus.completed
    success: bool | None = None
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    spans: list[SpanIn] = Field(default_factory=list)


class TraceAcceptedOut(BaseModel):
    trace_id: uuid.UUID
    status: str


class SpanOut(BaseModel):
    id: uuid.UUID
    parent_span_id: uuid.UUID | None
    span_type: SpanType
    name: str
    input: dict
    output: dict
    span_metadata: dict = Field(serialization_alias="metadata")
    latency_ms: int
    error: str | None
    created_at: datetime
    tool_calls: list[dict] = Field(default_factory=list)
    retrieval_events: list[dict] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TraceOut(BaseModel):
    id: uuid.UUID
    trace_ref: str
    agent_id: uuid.UUID
    agent_config_id: uuid.UUID
    workflow_tag: str | None
    segment_tags: dict
    input_text: str
    status: TraceStatus
    success: bool | None
    latency_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    model_provider: str | None
    model_name: str | None
    source: str
    created_at: datetime
    spans: list[SpanOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TraceListItemOut(BaseModel):
    id: uuid.UUID
    trace_ref: str
    workflow_tag: str | None
    status: TraceStatus
    success: bool | None
    latency_ms: int
    total_tokens: int
    estimated_cost: float
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceListOut(BaseModel):
    items: list[TraceListItemOut]
    total: int
