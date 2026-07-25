"""Multi-provider AI generation with fallback + short-TTL response caching.

Flow:
  1. Cache hit -> serve cached result (no provider call, no credit).
  2. Try the primary provider; on failure/timeout, fall back to the next.
  3. If NO external provider is configured, use a deterministic local generator
     so the app remains fully functional in development without API keys.
  4. If external providers ARE configured but all fail -> raise
     ``AIGenerationError`` (controllers translate to ``502``).

SDKs are imported lazily so the API boots without them installed.
"""

import hashlib
import json
import random
import time

from flask import current_app


class AIGenerationError(Exception):
    """Raised when every configured external provider fails."""


_CACHE: dict[str, tuple[float, dict]] = {}


# --- Cache ------------------------------------------------------------------------


def _cache_key(generation_type: str, prompt_input: str) -> str:
    return hashlib.sha256(f"{generation_type}|{prompt_input}".encode()).hexdigest()


def peek_cache(generation_type: str, prompt_input: str) -> dict | None:
    entry = _CACHE.get(_cache_key(generation_type, prompt_input))
    if not entry:
        return None
    stored_at, value = entry
    ttl = current_app.config.get("AI_CACHE_TTL_SECONDS", 300)
    if time.time() - stored_at > ttl:
        _CACHE.pop(_cache_key(generation_type, prompt_input), None)
        return None
    return value


def _store_cache(generation_type: str, prompt_input: str, value: dict) -> None:
    _CACHE[_cache_key(generation_type, prompt_input)] = (time.time(), value)


# --- Prompt building --------------------------------------------------------------


def _build_prompt(generation_type: str, prompt_input: str) -> str:
    templates = {
        "caption": (
            "You are an expert social media copywriter. Write one scroll-stopping "
            "caption (with 1-2 tasteful emojis and a call to action) for:\n{input}"
        ),
        "hashtags": (
            "Suggest 12 high-reach, relevant hashtags (space separated, each "
            "starting with #) for the following post context:\n{input}"
        ),
        "content_idea": (
            "Generate 5 concrete, original content ideas as a numbered list for "
            "this niche/account:\n{input}"
        ),
        "viral_score": (
            "Rate the viral potential of this draft from 0-100 and give 3 concrete "
            "improvement tips. Respond as JSON with keys score, verdict, tips:\n{input}"
        ),
        "sentiment": (
            "Analyse audience sentiment for this account's recent comments. Respond "
            "as JSON with keys positive, neutral, negative (percent ints summing to "
            "100) and summary:\n{input}"
        ),
    }
    template = templates.get(generation_type, "{input}")
    return template.format(input=prompt_input)


# --- Provider chain ---------------------------------------------------------------


def _configured_providers() -> list[str]:
    order = []
    primary = current_app.config.get("AI_PRIMARY_PROVIDER", "anthropic")
    for name in [primary, "nvidia", "openrouter", "anthropic", "openai", "gemini"]:
        if name not in order:
            order.append(name)
    key_map = {
        "nvidia": "NVIDIA_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }
    return [name for name in order if current_app.config.get(key_map.get(name, ""))]


def _call_nvidia(prompt: str) -> str:
    """Call NVIDIA NIM via its OpenAI-compatible chat completions API.

    Uses ``requests`` (not the OpenAI SDK) so a mismatched ``httpx`` version
    cannot break generation. Default model is DiffusionGemma on build.nvidia.com.
    """
    import requests

    base = (current_app.config.get("NVIDIA_BASE_URL") or "").rstrip("/")
    model = current_app.config.get("NVIDIA_MODEL") or "google/diffusiongemma-26b-a4b-it"
    resp = requests.post(
        f"{base}/chat/completions",
        headers={
            "Authorization": f"Bearer {current_app.config['NVIDIA_API_KEY']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.7,
            "stream": False,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("NVIDIA NIM returned no choices.")
    message = choices[0].get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        raise RuntimeError("NVIDIA NIM returned an empty response.")
    return content


def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter's OpenAI-compatible chat completions API."""
    import requests

    base = (current_app.config.get("OPENROUTER_BASE_URL") or "").rstrip("/")
    model = current_app.config.get("OPENROUTER_MODEL") or "openrouter/auto-beta"
    resp = requests.post(
        f"{base}/chat/completions",
        headers={
            "Authorization": f"Bearer {current_app.config['OPENROUTER_API_KEY']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "HTTP-Referer": current_app.config.get("OPENROUTER_SITE_URL", ""),
            "X-OpenRouter-Title": current_app.config.get(
                "OPENROUTER_APP_NAME", "Pulse Social AI"
            ),
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.7,
            "stream": False,
        },
        timeout=60,
    )
    resp.raise_for_status()
    choices = (resp.json().get("choices") or [])
    if not choices:
        raise RuntimeError("OpenRouter returned no choices.")
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("OpenRouter returned an empty response.")
    return content


def _call_anthropic(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content.strip()


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini via the generateContent REST API.

    Uses ``requests`` instead of ``google-generativeai`` so generation works on
    Python builds where the protobuf-backed SDK fails to import.
    """
    import requests

    api_key = current_app.config.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured.")

    base = (current_app.config.get("GEMINI_BASE_URL") or "").rstrip("/")
    model = current_app.config.get("GEMINI_MODEL") or "gemini-2.0-flash"
    url = f"{base}/models/{model}:generateContent"
    resp = requests.post(
        url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-goog-api-key": api_key,
        },
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        # Surface Gemini block/safety feedback when present.
        feedback = data.get("promptFeedback") or {}
        raise RuntimeError(
            f"Gemini returned no candidates: {feedback or data}"
        )
    parts = ((candidates[0].get("content") or {}).get("parts")) or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
    content = "".join(texts).strip()
    if not content:
        raise RuntimeError("Gemini returned an empty response.")
    return content


_PROVIDER_FUNCS = {
    "nvidia": _call_nvidia,
    "openrouter": _call_openrouter,
    "anthropic": _call_anthropic,
    "openai": _call_openai,
    "gemini": _call_gemini,
}


# --- Public API -------------------------------------------------------------------


def generate(generation_type, prompt_input, workspace=None, social_account=None) -> dict:
    """Return ``{"result": str, "provider": str, "cached": bool}``."""
    cached = peek_cache(generation_type, prompt_input)
    if cached is not None:
        return {"result": cached["result"], "provider": cached["provider"], "cached": True}

    prompt = _build_prompt(generation_type, prompt_input)
    providers = _configured_providers()

    last_error = None
    for name in providers:
        try:
            result = _PROVIDER_FUNCS[name](prompt)
            if result:
                payload = {"result": result, "provider": name}
                _store_cache(generation_type, prompt_input, payload)
                return {**payload, "cached": False}
        except Exception as exc:  # noqa: BLE001 - fall through to next provider
            last_error = exc
            current_app.logger.warning("AI provider %s failed: %s", name, exc)

    if not providers:
        # No external providers configured — deterministic local fallback.
        result = _local_generate(generation_type, prompt_input, social_account)
        payload = {"result": result, "provider": "local-fallback"}
        _store_cache(generation_type, prompt_input, payload)
        return {**payload, "cached": False}

    raise AIGenerationError(str(last_error) if last_error else "All AI providers failed.")


# --- Local deterministic fallback -------------------------------------------------


def _topic_from(prompt_input: str) -> str:
    for line in prompt_input.splitlines():
        if line.lower().startswith("topic:"):
            return line.split(":", 1)[1].strip()
        if line.lower().startswith("niche:"):
            return line.split(":", 1)[1].strip()
    return prompt_input.strip().split("\n")[0][:80] or "your content"


def _local_generate(generation_type, prompt_input, social_account=None) -> str:
    rnd = random.Random(hashlib.sha256(prompt_input.encode()).hexdigest())
    topic = _topic_from(prompt_input)

    if generation_type == "caption":
        hooks = [
            f"Stop scrolling — {topic} just changed the game.",
            f"Here's what nobody tells you about {topic}.",
            f"{topic}, but make it unforgettable.",
        ]
        return f"{rnd.choice(hooks)} \n\nDrop a comment if you agree and save this for later. #creator"

    if generation_type == "hashtags":
        words = [w for w in topic.replace("#", "").split() if w.isalnum()][:4] or ["content"]
        base = [f"#{w.lower()}" for w in words]
        extra = ["#reels", "#viral", "#growth", "#creator", "#trending", "#fyp", "#socialmedia", "#tips"]
        rnd.shuffle(extra)
        return " ".join(base + extra[: 12 - len(base)])

    if generation_type == "content_idea":
        return "\n".join(
            f"{i}. {kind} about {topic}"
            for i, kind in enumerate(
                ["A myth-busting reel", "A before/after story", "A quick how-to", "A day-in-the-life", "A hot take"],
                start=1,
            )
        )

    if generation_type == "viral_score":
        score = rnd.randint(58, 92)
        verdict = "High potential" if score >= 80 else "Solid, with room to improve"
        return json.dumps(
            {
                "score": score,
                "verdict": verdict,
                "tips": [
                    "Lead with a stronger 3-second hook.",
                    "Add captions/subtitles for silent viewers.",
                    "End with a clear call to action.",
                ],
            }
        )

    if generation_type == "sentiment":
        positive = rnd.randint(55, 80)
        negative = rnd.randint(5, 20)
        neutral = max(0, 100 - positive - negative)
        return json.dumps(
            {
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
                "summary": "Audience response is largely positive, praising consistency and value.",
            }
        )

    return f"Generated content for: {topic}"
