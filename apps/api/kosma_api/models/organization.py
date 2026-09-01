from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin, TimestampMixin


class Organization(IDMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, nullable=False)

    projects: Mapped[list["Project"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
