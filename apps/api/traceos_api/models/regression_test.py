import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from traceos_api.db.base import Base
from traceos_api.models.mixins import IDMixin, TimestampMixin


class RegressionTestStatus(str, enum.Enum):
    pending = "pending"
    passed = "passed"
    failed = "failed"


class RegressionTest(IDMixin, TimestampMixin, Base):
    __tablename__ = "regression_tests"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    impact_report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("impact_reports.id", ondelete="SET NULL"), nullable=True
    )
    source_trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    context_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    expected_condition: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RegressionTestStatus] = mapped_column(
        Enum(RegressionTestStatus, name="regression_test_status"),
        nullable=False,
        default=RegressionTestStatus.pending,
    )
