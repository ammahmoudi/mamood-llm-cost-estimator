# mamood-llm-cost-estimator

Realtime cost estimator for OpenRouter model calls.

It fetches live pricing from OpenRouter's public models endpoint and calculates input, cached-input, output, and total USD cost for any token usage.

## Why this package

- Live pricing: no hardcoded model price tables.
- Accurate token math: supports normal + cached prompt tokens.
- Easy integration: clean Python API and simple CLI.
- Fast repeated use: in-memory cache for model catalog data.
- Flexible input: pass token counts directly or pass raw text and auto-estimate tokens.

## Installation

```bash
uv add mamood-llm-cost-estimator
```

From source:

```bash
uv sync
```

## Python quick start

```python
from mamood_llm_cost_estimator import OpenRouterClient, TokenUsage

client = OpenRouterClient()
usage = TokenUsage(input_tokens=1500, output_tokens=700, cached_input_tokens=300)

cost = client.estimate_model_cost(model="openai/gpt-4o-mini", usage=usage)
print(cost.as_dict())
```

Example output:

```json
{
	"model": "openai/gpt-4o-mini",
	"input_cost_usd": 0.00018,
	"cached_input_cost_usd": 0.000045,
	"output_cost_usd": 0.00042,
	"total_cost_usd": 0.000645,
	"currency": "USD"
}
```

## Browse available models

```python
from mamood_llm_cost_estimator import OpenRouterClient

client = OpenRouterClient()
models = client.list_models()

for model in models[:5]:
		print(
				model.id,
				model.provider,
				model.context_window,
				model.input_price_per_million_usd,
				model.output_price_per_million_usd,
		)
```

## CLI usage

```bash
mamood-cost \
	--model openai/gpt-4o-mini \
	--input-tokens 1500 \
	--output-tokens 700 \
	--cached-input-tokens 300
```

Use text instead of token counts:

```bash
mamood-cost \
	--model openai/gpt-4o-mini \
	--input-text "Write a short summary of this transcript" \
	--output-text "Here is your concise summary..." \
	--chars-per-token 4
```

Mix mode (text for input, numeric for output):

```bash
mamood-cost \
	--model openai/gpt-4o-mini \
	--input-text "Tell me 5 ideas for a startup" \
	--output-tokens 450
```

## Notes

- Pricing source: `https://openrouter.ai/api/v1/models`.
- API key is optional for pricing fetch; if needed, set `OPENROUTER_API_KEY` or pass `--api-key`.
- Default model-catalog cache TTL is 1 hour (`cache_ttl_seconds=3600`).
- Text-based token counting uses an estimator (`chars_per_token`, default `4.0`).

## Development

```bash
uv sync
uv run python -m mamood_llm_cost_estimator --help
uv build
```

Created by Amirhossein Mahmoudi (@ammahmoudi)

