import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class Evaluation(IDMixin, TimestampMixin, Base):
    __tablename__ = "evaluations"

    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluator_type: Mapped[str] = mapped_column(String, nullable=False)
