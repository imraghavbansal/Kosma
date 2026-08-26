import enum
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from traceos_api.config import get_settings
from traceos_api.db.base import Base
from traceos_api.models.mixins import IDMixin, TimestampMixin

settings = get_settings()


class TraceStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    error = "error"


class TraceSource(str, enum.Enum):
    live = "live"
    replay = "replay"


class Trace(IDMixin, TimestampMixin, Base):
    __tablename__ = "traces"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False
    )
    trace_ref: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    workflow_tag: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    segment_tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    input_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )
    status: Mapped[TraceStatus] = mapped_column(
        Enum(TraceStatus, name="trace_status"), nullable=False, default=TraceStatus.pending
    )
    success: Mapped[bool | None] = mapped_column(nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False, default=0)
    model_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[TraceSource] = mapped_column(
        Enum(TraceSource, name="trace_source"), nullable=False, default=TraceSource.live
    )

    spans: Mapped[list["Span"]] = relationship(back_populates="trace", cascade="all, delete-orphan")
