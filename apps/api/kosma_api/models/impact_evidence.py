import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class ImpactEvidence(IDMixin, TimestampMixin, Base):
    __tablename__ = "impact_evidence"

    impact_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("impact_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    segment: Mapped[str | None] = mapped_column(String, nullable=True)
    baseline_trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False
    )
    replay_trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    impact_report: Mapped["ImpactReport"] = relationship(back_populates="evidence")

    @property
    def evidence_tier(self) -> str:
        # Always "replayed": every row here comes from counterfactual replay
        # (change_engine/analysis.py), never a live observation or an
        # unstated guess. See ImpactReport.evidence_basis for the report-level
        # statement of what that means.
        return "replayed"
