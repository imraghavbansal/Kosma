import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class SpanType(str, enum.Enum):
    query_processing = "query_processing"
    retrieval = "retrieval"
    embedding = "embedding"
    vector_search = "vector_search"
    reranking = "reranking"
    llm = "llm"
    tool_call = "tool_call"
    citation_check = "citation_check"
    custom = "custom"


class Span(IDMixin, TimestampMixin, Base):
    __tablename__ = "spans"

    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_span_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spans.id", ondelete="CASCADE"), nullable=True
    )
    span_type: Mapped[SpanType] = mapped_column(Enum(SpanType, name="span_type"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    span_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    trace: Mapped["Trace"] = relationship(back_populates="spans")
    tool_calls: Mapped[list["ToolCall"]] = relationship(back_populates="span", cascade="all, delete-orphan")
    retrieval_events: Mapped[list["RetrievalEvent"]] = relationship(
        back_populates="span", cascade="all, delete-orphan"
    )
