from __future__ import annotations

import math


def estimate_tokens_from_text(text: str, *, chars_per_token: float = 4.0) -> int:
    stripped = text.strip()
    if not stripped:
        return 0

    effective_chars_per_token = chars_per_token if chars_per_token > 0 else 4.0
    return max(1, math.ceil(len(stripped) / effective_chars_per_token))
