from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class User(IDMixin, TimestampMixin, Base):
    """A person who signed in via GitHub OAuth. Deliberately not linked to an
    Organization/Project - see the "second login method" scoping decision
    (2026-09-02): logged-in users explore the same shared seeded demo data
    that shared-secret sessions do, not a personal empty sandbox. Full
    per-user data isolation would mean re-scoping every existing endpoint by
    tenant, which is real V2-scale work (see PRODUCT-SPEC.md's original
    single-tenant decision) - this table exists so "who's signed in" is real,
    not that "each user's data" is separated yet."""

    __tablename__ = "users"

    github_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    github_username: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
