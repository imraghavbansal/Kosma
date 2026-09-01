from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.models.model_pricing import ModelPricing


def estimate_cost(db: Session, provider: str | None, model_name: str | None, input_tokens: int, output_tokens: int) -> Decimal:
    """Look up the most recent pricing row for (provider, model_name) and compute
    estimated cost. Returns 0 if no pricing is on file - cost is always an estimate,
    never fabricated (see docs/api-design.md, PRODUCT-SPEC.md)."""
    if provider is None or model_name is None:
        return Decimal("0")

    pricing = db.scalar(
        select(ModelPricing)
        .where(ModelPricing.provider == provider, ModelPricing.model_name == model_name)
        .order_by(ModelPricing.effective_date.desc())
        .limit(1)
    )
    if pricing is None:
        return Decimal("0")

    input_cost = (Decimal(input_tokens) / Decimal(1000)) * Decimal(pricing.input_price_per_1k)
    output_cost = (Decimal(output_tokens) / Decimal(1000)) * Decimal(pricing.output_price_per_1k)
    return input_cost + output_cost
