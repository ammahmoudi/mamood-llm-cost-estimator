from __future__ import annotations

import argparse
import json
import os

from .models import TokenUsage
from .openrouter import OpenRouterClient, OpenRouterError
from .tokens import estimate_tokens_from_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mamood-cost",
        description="Estimate OpenRouter LLM call costs in real time.",
    )
    parser.add_argument("--model", required=True, help="OpenRouter model id")

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input-tokens", type=int, help="Prompt/input token count"
    )
    input_group.add_argument(
        "--input-text",
        type=str,
        help="Prompt/input text to estimate token count automatically",
    )

    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument(
        "--output-tokens", type=int, help="Completion/output token count"
    )
    output_group.add_argument(
        "--output-text",
        type=str,
        help="Completion/output text to estimate token count automatically",
    )

    parser.add_argument(
        "--chars-per-token",
        type=float,
        default=4.0,
        help="Token estimation ratio when using text (default: 4.0 chars/token)",
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

    input_tokens = (
        args.input_tokens
        if args.input_tokens is not None
        else estimate_tokens_from_text(args.input_text, chars_per_token=args.chars_per_token)
    )
    output_tokens = (
        args.output_tokens
        if args.output_tokens is not None
        else estimate_tokens_from_text(
            args.output_text, chars_per_token=args.chars_per_token
        )
    )

    usage = TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=args.cached_input_tokens,
    )
    client = OpenRouterClient(api_key=args.api_key, app_name=args.app_name)

    try:
        result = client.estimate_model_cost(model=args.model, usage=usage)
    except OpenRouterError as exc:
        print(str(exc))
        return 1

    payload = result.as_dict()
    payload["input_tokens"] = usage.input_tokens
    payload["output_tokens"] = usage.output_tokens
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
