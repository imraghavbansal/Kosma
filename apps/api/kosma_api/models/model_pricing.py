from datetime import date

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from kosma_api.db.base import Base
from kosma_api.models.mixins import IDMixin


class ModelPricing(IDMixin, Base):
    __tablename__ = "model_pricing"

    provider: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    input_price_per_1k: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    output_price_per_1k: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
