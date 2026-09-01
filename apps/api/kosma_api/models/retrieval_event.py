import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class RetrievalEvent(IDMixin, TimestampMixin, Base):
    __tablename__ = "retrieval_events"

    span_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    documents: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    span: Mapped["Span"] = relationship(back_populates="retrieval_events")
