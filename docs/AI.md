# AI Generation

## Providers & fallback

`app/services/ai_service.py` orchestrates generation across providers in order:

1. The configured primary (`AI_PRIMARY_PROVIDER`, default `anthropic`)
2. Anthropic → OpenAI → Gemini (whichever have API keys set)

If a provider errors or times out, the next is tried. With **no** external keys
configured, a deterministic **local fallback** generator produces plausible
content so the product is fully usable in development.

## Caching

Identical `(generation_type, prompt_input)` pairs are cached for
`AI_CACHE_TTL_SECONDS` (default 300s). **Cache hits are not charged** — the
controller only deducts a credit when a fresh, successful generation happens.

## Generation types

| Type | Endpoint | Output |
| --- | --- | --- |
| `caption` | `POST /api/generate/caption` | Caption text |
| `hashtags` | `POST /api/generate/hashtags` | Space-separated hashtags |
| `content_idea` | `POST /api/generate/content-idea` | Numbered idea list |
| `viral_score` | `POST /api/generate/viral-score` | JSON: score, verdict, tips |
| `sentiment` | `POST /api/generate/sentiment` | JSON: positive/neutral/negative + summary |

## Credit metering

Each successful generation consumes 1 credit from the workspace's monthly
`credit_usages` ledger. Free = 5, Pro = 500, Agency = 2000 (see `Config.PLAN_CREDITS`).
On exhaustion the API returns `402 Payment Required`.
