import enum
import uuid

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from traceos_api.db.base import Base
from traceos_api.models.mixins import IDMixin, TimestampMixin


class AgentConfigKind(str, enum.Enum):
    prompt = "prompt"
    model = "model"


class AgentConfig(IDMixin, TimestampMixin, Base):
    __tablename__ = "agent_configs"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[AgentConfigKind] = mapped_column(Enum(AgentConfigKind, name="agent_config_kind"), nullable=False)
    version_label: Mapped[str] = mapped_column(String, nullable=False)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_baseline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    agent: Mapped["Agent"] = relationship(back_populates="configs")
