import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class ToolCall(IDMixin, TimestampMixin, Base):
    __tablename__ = "tool_calls"

    span_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    arguments: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    valid_arguments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    span: Mapped["Span"] = relationship(back_populates="tool_calls")
