from __future__ import annotations

import math


def estimate_tokens_from_text(text: str, *, chars_per_token: float = 4.0) -> int:
    stripped = text.strip()
    if not stripped:
        return 0

    effective_chars_per_token = chars_per_token if chars_per_token > 0 else 4.0
    return max(1, math.ceil(len(stripped) / effective_chars_per_token))


def _normalize_openrouter_model_id(model: str | None) -> str | None:
    if model is None:
        return None

    normalized = model.strip()
    if not normalized:
        return None

    if "/" in normalized:
        provider, maybe_model = normalized.split("/", maxsplit=1)
        if provider and maybe_model:
            return maybe_model

    return normalized


def count_tokens(
    text: str,
    *,
    model: str | None = None,
    tokenizer: str = "tiktoken",
    chars_per_token: float = 4.0,
) -> int:
    if tokenizer != "tiktoken":
        return estimate_tokens_from_text(text, chars_per_token=chars_per_token)

    stripped = text.strip()
    if not stripped:
        return 0

    try:
        import tiktoken  # type: ignore[import-not-found]
    except Exception:
        return estimate_tokens_from_text(stripped, chars_per_token=chars_per_token)

    model_name = _normalize_openrouter_model_id(model)

    if model_name:
        try:
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(stripped))
        except Exception:
            pass

    try:
        fallback_encoding = tiktoken.get_encoding("o200k_base")
    except Exception:
        fallback_encoding = tiktoken.get_encoding("cl100k_base")

    return len(fallback_encoding.encode(stripped))
