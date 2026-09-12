"""Provider-agnostic chat client for the guidance and chat services.

Both supported providers expose a `/chat/completions` endpoint, so a single
standard-library client handles either one. The active provider is selected
with the `CHAT_PROVIDER` environment variable ("openrouter" or "opencode").

Secrets are read from the environment only and are never logged or returned
to clients. Every function degrades gracefully: when a provider is not
configured or reachable, callers fall back to built-in guidance.
"""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import config

logger = logging.getLogger(__name__)

PROVIDERS = ("openrouter", "opencode")
DEFAULT_PROVIDER = "openrouter"


def resolve_provider(name=None):
    """Return a known provider name, falling back to the default."""
    candidate = (name or config.CHAT_PROVIDER or DEFAULT_PROVIDER).strip().lower()
    return candidate if candidate in PROVIDERS else DEFAULT_PROVIDER


def provider_settings(name=None):
    """Return connection settings for a provider (never logs the key)."""
    provider = resolve_provider(name)
    if provider == "opencode":
        return {
            "name": provider,
            "base_url": config.OPENCODE_BASE_URL,
            "api_key": config.OPENCODE_API_KEY,
            "model": config.OPENCODE_MODEL,
        }
    return {
        "name": provider,
        "base_url": config.OPENROUTER_BASE_URL,
        "api_key": config.OPENROUTER_API_KEY,
        "model": config.OPENROUTER_MODEL,
    }


def is_configured(name=None):
    return bool(provider_settings(name)["api_key"])


def _endpoint(settings):
    return settings["base_url"].rstrip("/") + "/chat/completions"


def _request(settings, body, session=None):
    stream = bool(body.get("stream"))
    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if stream else "application/json",
        "User-Agent": "potato-disease-backend/1.0",
    }
    if settings["name"] == "opencode" and session:
        # opencode routes and caches per conversation using this header.
        headers["x-opencode-session"] = session
    return Request(
        _endpoint(settings),
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )


def _body(settings, messages, temperature, max_tokens, stream):
    return {
        "model": settings["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }


def _error_detail(exc):
    """Read a short, non-secret snippet of an error body for logging."""
    try:
        return exc.read().decode("utf-8", errors="replace")[:300]
    except Exception:
        return ""


def chat_completion(messages, provider=None, temperature=0.4, max_tokens=600, session=None):
    """Return the assistant reply text, or None when unavailable."""
    settings = provider_settings(provider)
    if not settings["api_key"]:
        return None

    request = _request(
        settings, _body(settings, messages, temperature, max_tokens, False), session
    )
    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        logger.warning(
            "%s chat completion failed: HTTP %s %s",
            settings["name"],
            exc.code,
            _error_detail(exc),
        )
        return None
    except (URLError, TimeoutError, ValueError) as exc:
        logger.warning("%s chat completion failed: %s", settings["name"], exc)
        return None

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.warning("%s chat completion returned an unexpected payload.", settings["name"])
        return None
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None


def chat_completion_stream(
    messages, provider=None, temperature=0.4, max_tokens=600, session=None
):
    """Yield reply text chunks as they arrive; yields nothing when unavailable."""
    settings = provider_settings(provider)
    if not settings["api_key"]:
        return

    request = _request(
        settings, _body(settings, messages, temperature, max_tokens, True), session
    )
    try:
        with urlopen(request, timeout=120) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:") :].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except ValueError:
                    continue
                content = _delta_content(chunk)
                if content:
                    yield content
    except HTTPError as exc:
        logger.warning(
            "%s chat stream failed: HTTP %s %s",
            settings["name"],
            exc.code,
            _error_detail(exc),
        )
        return
    except (URLError, TimeoutError) as exc:
        logger.warning("%s chat stream failed: %s", settings["name"], exc)
        return


def _delta_content(chunk):
    try:
        delta = chunk["choices"][0]["delta"]
    except (KeyError, IndexError, TypeError):
        return None
    if not isinstance(delta, dict):
        return None
    content = delta.get("content")
    return content if isinstance(content, str) and content else None
