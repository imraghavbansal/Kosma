import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from traceos_api.db.base import Base
from traceos_api.models.mixins import IDMixin, TimestampMixin


class PredictionOutcome(IDMixin, TimestampMixin, Base):
    __tablename__ = "prediction_outcomes"

    change_proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("change_proposals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    predicted_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    actual_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    prediction_error: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
