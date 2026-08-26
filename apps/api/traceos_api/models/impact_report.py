import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from traceos_api.db.base import Base
from traceos_api.models.mixins import IDMixin, TimestampMixin


class Recommendation(str, enum.Enum):
    SHIP = "SHIP"
    MODIFY = "MODIFY"
    BLOCK = "BLOCK"


class ImpactReport(IDMixin, TimestampMixin, Base):
    __tablename__ = "impact_reports"

    change_proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("change_proposals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    cohort_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommendation: Mapped[Recommendation] = mapped_column(
        Enum(Recommendation, name="impact_recommendation"), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    overall_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    segment_metrics: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
