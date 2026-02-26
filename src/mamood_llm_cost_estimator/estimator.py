from __future__ import annotations

from .models import CostBreakdown, TokenUsage


def estimate_cost(
    *,
    model: str,
    usage: TokenUsage,
    input_price_per_token_usd: float,
    output_price_per_token_usd: float,
    cached_input_price_per_token_usd: float | None = None,
) -> CostBreakdown:
    cached_price = (
        cached_input_price_per_token_usd
        if cached_input_price_per_token_usd is not None
        else input_price_per_token_usd
    )

    input_cost = usage.non_cached_input_tokens * input_price_per_token_usd
    cached_input_cost = usage.cached_input_tokens * cached_price
    output_cost = usage.output_tokens * output_price_per_token_usd
    total = input_cost + cached_input_cost + output_cost

    return CostBreakdown(
        model=model,
        input_cost_usd=input_cost,
        cached_input_cost_usd=cached_input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=total,
    )
