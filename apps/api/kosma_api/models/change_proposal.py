import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class ChangeProposalStatus(str, enum.Enum):
    draft = "draft"
    analyzing = "analyzing"
    analyzed = "analyzed"
    shipped = "shipped"


class ChangeProposal(IDMixin, TimestampMixin, Base):
    __tablename__ = "change_proposals"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    baseline_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_configs.id"), nullable=False
    )
    candidate_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_configs.id"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ChangeProposalStatus] = mapped_column(
        Enum(ChangeProposalStatus, name="change_proposal_status"),
        nullable=False,
        default=ChangeProposalStatus.draft,
    )
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
