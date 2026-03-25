"""Cost estimation utilities for provider/model usage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Pricing:
    input_per_1k: float
    output_per_1k: float


# Conservative defaults; override at runtime when exact provider pricing is known.
DEFAULT_PRICING: dict[str, Pricing] = {
    "default": Pricing(input_per_1k=0.0, output_per_1k=0.0),
    "openai:gpt-4o-mini": Pricing(input_per_1k=0.00015, output_per_1k=0.00060),
    "anthropic:claude-3-5-haiku": Pricing(input_per_1k=0.00025, output_per_1k=0.00125),
}


def estimate_call_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing_table: dict[str, Pricing] | None = None,
) -> float:
    table = pricing_table or DEFAULT_PRICING
    key = f"{provider}:{model}"
    p = table.get(key, table.get("default", Pricing(0.0, 0.0)))
    input_cost = (max(input_tokens, 0) / 1000.0) * p.input_per_1k
    output_cost = (max(output_tokens, 0) / 1000.0) * p.output_per_1k
    return round(input_cost + output_cost, 8)


def cost_metadata(provider: str, model: str, usage: dict[str, Any]) -> dict[str, Any]:
    in_tok = int(usage.get("prompt_tokens", 0))
    out_tok = int(usage.get("completion_tokens", 0))
    total = int(usage.get("total_tokens", in_tok + out_tok))
    return {
        "provider": provider,
        "model": model,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "total_tokens": total,
        "estimated_cost_usd": estimate_call_cost(provider, model, in_tok, out_tok),
    }
