from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .estimator import estimate_cost
from .models import CostBreakdown, TokenUsage


class OpenRouterError(RuntimeError):
    pass


@dataclass(slots=True)
class ModelPricing:
    model: str
    input_price_per_token_usd: float
    output_price_per_token_usd: float
    cached_input_price_per_token_usd: float | None = None


@dataclass(slots=True)
class ModelCatalogEntry:
    id: str
    name: str
    provider: str
    context_window: int
    input_price_per_token_usd: float
    output_price_per_token_usd: float
    cached_input_price_per_token_usd: float | None = None

    @property
    def input_price_per_million_usd(self) -> float:
        return self.input_price_per_token_usd * 1_000_000

    @property
    def output_price_per_million_usd(self) -> float:
        return self.output_price_per_token_usd * 1_000_000


@dataclass(slots=True)
class CachedModelCatalog:
    timestamp: float
    models: list[ModelCatalogEntry]


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        app_name: str | None = None,
        cache_ttl_seconds: int = 3600,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._app_name = app_name
        self._cache_ttl_seconds = max(0, cache_ttl_seconds)
        self._cache: CachedModelCatalog | None = None

    @staticmethod
    def _parse_price(value: str | float | int | None) -> float:
        if value is None:
            return 0.0

        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return 0.0

        if parsed < 0:
            return 0.0
        return parsed

    @staticmethod
    def _parse_int(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, parsed)

    @staticmethod
    def _guess_provider(model_id: str, name: str) -> str:
        lower_id = model_id.lower()

        if lower_id.startswith("openai/"):
            return "OpenAI"
        if lower_id.startswith("google/"):
            return "Google"
        if lower_id.startswith("anthropic/"):
            return "Anthropic"
        if lower_id.startswith("mistral"):
            return "Mistral"
        if lower_id.startswith("meta-llama/") or lower_id.startswith("meta/"):
            return "Meta"
        if lower_id.startswith("cohere/"):
            return "Cohere"
        if lower_id.startswith("deepseek/"):
            return "DeepSeek"
        if lower_id.startswith("qwen/"):
            return "Alibaba"
        if lower_id.startswith("microsoft/"):
            return "Microsoft"
        if lower_id.startswith("perplexity/"):
            return "Perplexity"

        parts = model_id.split("/", maxsplit=1)
        if len(parts) > 1 and parts[0]:
            provider = parts[0].strip().lower()
            return provider[0].upper() + provider[1:]

        if name:
            return "Other"
        return "Other"

    def list_models(self, *, force_refresh: bool = False) -> list[ModelCatalogEntry]:
        now = time.time()
        cache = self._cache
        is_fresh = (
            cache is not None and (now - cache.timestamp) < self._cache_ttl_seconds
        )

        if cache is not None and is_fresh and not force_refresh:
            return cache.models

        try:
            models_payload = self._get_json(f"{self._base_url}/models")
            raw_data = models_payload.get("data", [])
            if not isinstance(raw_data, list):
                raise OpenRouterError("Invalid API response: 'data' is not an array.")

            models: list[ModelCatalogEntry] = []
            for item in raw_data:
                if not isinstance(item, dict):
                    continue

                model_id = item.get("id")
                if not isinstance(model_id, str) or not model_id:
                    continue

                model_name = item.get("name")
                if not isinstance(model_name, str):
                    model_name = model_id

                pricing = item.get("pricing")
                if not isinstance(pricing, dict):
                    pricing = {}

                models.append(
                    ModelCatalogEntry(
                        id=model_id,
                        name=model_name,
                        provider=self._guess_provider(model_id, model_name),
                        context_window=self._parse_int(item.get("context_length")),
                        input_price_per_token_usd=self._parse_price(pricing.get("prompt")),
                        output_price_per_token_usd=self._parse_price(
                            pricing.get("completion")
                        ),
                        cached_input_price_per_token_usd=self._parse_price(
                            pricing.get("cached_prompt")
                        )
                        if pricing.get("cached_prompt") is not None
                        else None,
                    )
                )

            self._cache = CachedModelCatalog(timestamp=now, models=models)
            return models
        except OpenRouterError:
            if cache is not None:
                return cache.models
            raise

    def fetch_models(self, *, force_refresh: bool = False) -> list[ModelPricing]:
        return [
            ModelPricing(
                model=item.id,
                input_price_per_token_usd=item.input_price_per_token_usd,
                output_price_per_token_usd=item.output_price_per_token_usd,
                cached_input_price_per_token_usd=item.cached_input_price_per_token_usd,
            )
            for item in self.list_models(force_refresh=force_refresh)
        ]

    def get_model_pricing(self, model: str) -> ModelPricing:
        for item in self.list_models():
            if item.id == model:
                return ModelPricing(
                    model=item.id,
                    input_price_per_token_usd=item.input_price_per_token_usd,
                    output_price_per_token_usd=item.output_price_per_token_usd,
                    cached_input_price_per_token_usd=item.cached_input_price_per_token_usd,
                )

        raise OpenRouterError(
            f"Model '{model}' was not found in OpenRouter model catalog."
        )

    def estimate_model_cost(self, *, model: str, usage: TokenUsage) -> CostBreakdown:
        pricing = self.get_model_pricing(model)
        return estimate_cost(
            model=model,
            usage=usage,
            input_price_per_token_usd=pricing.input_price_per_token_usd,
            output_price_per_token_usd=pricing.output_price_per_token_usd,
            cached_input_price_per_token_usd=pricing.cached_input_price_per_token_usd,
        )

    def _get_json(self, url: str) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "mamood-llm-cost-estimator/0.1.0",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        if self._app_name:
            headers["X-Title"] = self._app_name

        request = Request(url, headers=headers, method="GET")

        try:
            with urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise OpenRouterError(
                f"OpenRouter request failed with status {exc.code}."
            ) from exc
        except URLError as exc:
            raise OpenRouterError(f"OpenRouter request failed: {exc.reason}") from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise OpenRouterError("OpenRouter response was not valid JSON.") from exc

        if not isinstance(payload, dict):
            raise OpenRouterError("OpenRouter response had unexpected shape.")

        return payload
