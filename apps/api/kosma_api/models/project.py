import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class Project(IDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    # "owner/name" of a real GitHub repo this project is linked to - lets the
    # dashboard show a project's real commits/PRs alongside its Kosma trace
    # and change-proposal history. Nullable: most seeded demo projects have
    # no repo, and linking is an explicit user action (PATCH /v1/projects/{id}).
    github_repo: Mapped[str | None] = mapped_column(String, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="projects")
    agents: Mapped[list["Agent"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
