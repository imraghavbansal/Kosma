import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class Recommendation(str, enum.Enum):
    SHIP = "SHIP"
    MODIFY = "MODIFY"
    BLOCK = "BLOCK"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# A segment needs at least this many replayed samples before its delta counts
# as signal rather than noise - shared between change_engine/analysis.py (which
# enforces it) and this model's `limitations` property (which explains it).
MIN_SAMPLES_FOR_SIGNAL = 5


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

    evidence: Mapped[list["ImpactEvidence"]] = relationship(
        back_populates="impact_report", cascade="all, delete-orphan"
    )

    # Derived, not stored - computed from fields already on this row so there's
    # nothing to keep in sync. See PRODUCT-SPEC.md's evidence-first principle:
    # a verdict without a stated basis, limitation, and next action is exactly
    # the "unexplained magical recommendation" this product refuses to produce.
    @property
    def evidence_basis(self) -> str:
        return (
            "Predicted from counterfactual replay: the candidate config was run "
            "against comparable historical production traffic, not live traffic "
            "under the candidate config."
        )

    @property
    def limitations(self) -> list[str]:
        notes = [
            "Based on simulated replay against historical traffic, not observed "
            "live behavior under the candidate config - see the Prediction "
            "Scorecard once shipped for how this compares to what actually happened.",
        ]
        if self.recommendation == Recommendation.INSUFFICIENT_EVIDENCE:
            notes.append(
                f"No segment had at least {MIN_SAMPLES_FOR_SIGNAL} replayed samples, the "
                "minimum this product requires before treating a delta as signal rather than noise."
            )
        elif self.confidence < 0.6:
            notes.append("Confidence is limited by a small replayed sample size.")
        return notes

    @property
    def recommended_next_action(self) -> str:
        if self.recommendation == Recommendation.INSUFFICIENT_EVIDENCE:
            return (
                "Collect more production traffic for the affected workflow(s) before "
                "shipping, or manually review the change."
            )
        if self.recommendation == Recommendation.BLOCK:
            return "Do not ship - revisit the candidate config for the flagged segment(s)."
        if self.recommendation == Recommendation.MODIFY:
            return "Address the regressed segment(s) before shipping, or ship with monitoring on them."
        return "Safe to ship - check the Prediction Scorecard after deployment to confirm the prediction held."
