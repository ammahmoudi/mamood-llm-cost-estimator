from __future__ import annotations

import argparse
import json
import os

from .models import TokenUsage
from .openrouter import OpenRouterClient, OpenRouterError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mamood-cost",
        description="Estimate OpenRouter LLM call costs in real time.",
    )
    parser.add_argument("--model", required=True, help="OpenRouter model id")
    parser.add_argument(
        "--input-tokens", type=int, required=True, help="Prompt/input token count"
    )
    parser.add_argument(
        "--output-tokens", type=int, required=True, help="Completion/output token count"
    )
    parser.add_argument(
        "--cached-input-tokens",
        type=int,
        default=0,
        help="Cached input token count (optional)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENROUTER_API_KEY"),
        help="OpenRouter API key (or set OPENROUTER_API_KEY)",
    )
    parser.add_argument(
        "--app-name",
        default="mamood-llm-cost-estimator",
        help="Value sent in X-Title header",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    usage = TokenUsage(
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        cached_input_tokens=args.cached_input_tokens,
    )
    client = OpenRouterClient(api_key=args.api_key, app_name=args.app_name)

    try:
        result = client.estimate_model_cost(model=args.model, usage=usage)
    except OpenRouterError as exc:
        print(str(exc))
        return 1

    print(json.dumps(result.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
