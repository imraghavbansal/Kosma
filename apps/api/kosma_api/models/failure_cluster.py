import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class FailureCluster(IDMixin, TimestampMixin, Base):
    __tablename__ = "failure_clusters"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FailureClusterMember(Base):
    __tablename__ = "failure_cluster_members"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("failure_clusters.id", ondelete="CASCADE"), primary_key=True
    )
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), primary_key=True
    )
