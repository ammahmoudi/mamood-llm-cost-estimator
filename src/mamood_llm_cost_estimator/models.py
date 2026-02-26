from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0

    @property
    def non_cached_input_tokens(self) -> int:
        return max(0, self.input_tokens - self.cached_input_tokens)


@dataclass(slots=True)
class CostBreakdown:
    model: str
    input_cost_usd: float
    cached_input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    currency: str = "USD"

    def as_dict(self) -> dict[str, str | float]:
        return {
            "model": self.model,
            "input_cost_usd": round(self.input_cost_usd, 10),
            "cached_input_cost_usd": round(self.cached_input_cost_usd, 10),
            "output_cost_usd": round(self.output_cost_usd, 10),
            "total_cost_usd": round(self.total_cost_usd, 10),
            "currency": self.currency,
        }
