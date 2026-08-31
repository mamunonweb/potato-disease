"""Disease-aware chatbot backed by OpenRouter.

The CNN stays responsible for the prediction; the chat only discusses
the detected condition. Guidance is general information, not a
definitive diagnosis.
"""
import json

import config
from services.guidance import DISEASE_INFO, get_disease_info
from services.model import DISPLAY_NAMES

SYSTEM_PROMPT_TEMPLATE = (
    "You are a cautious potato-plant-disease assistant. The user has "
    "received a CNN prediction of '{display_name}' with {confidence_pct:.1f}% "
    "confidence. Discuss this detected condition and related potato "
    "plant-care questions.\n\n"
    "Reference information:\n{info_json}\n\n"
    "Rules:\n"
    "- Stay on topic: the detected condition, potato diseases, and potato "
    "plant care. Politely redirect unrelated questions.\n"
    "- Do not claim certainty, invent facts, or provide pesticide names, "
    "dosage, or application rates.\n"
    "- Recommend local agricultural guidance for treatment decisions.\n"
    "- Make clear this is general guidance, not a definitive diagnosis.\n"
    "- Keep answers concise and practical."
)

MAX_HISTORY_TURNS = config.CHAT_MAX_HISTORY_TURNS
MAX_MESSAGE_CHARS = config.CHAT_MAX_MESSAGE_CHARS


def _build_system_prompt(predicted_class, confidence):
    info, generated = get_disease_info(predicted_class)
    display_name = DISPLAY_NAMES.get(
        predicted_class, info.get("name", predicted_class)
    )
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        display_name=display_name,
        confidence_pct=confidence * 100,
        info_json=json.dumps(info),
    )
    source = "openrouter" if generated else "builtin"
    return prompt, source


def _trim_history(history):
    """Keep only valid alternating turns, capped and length-limited."""
    trimmed = []
    for turn in (history or [])[-MAX_HISTORY_TURNS * 2:]:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role")
        content = turn.get("content")
        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str) or not content.strip():
            continue
        trimmed.append({"role": role, "content": content.strip()[:MAX_MESSAGE_CHARS]})
    return trimmed


def chat_reply(predicted_class, confidence, message, history):
    """Return (reply_text, guidance_source) for one chat turn."""
    from openrouter import OpenRouter

    system_prompt, source = _build_system_prompt(predicted_class, confidence)
    messages = (
        [{"role": "system", "content": system_prompt}]
        + _trim_history(history)
        + [{"role": "user", "content": message[:MAX_MESSAGE_CHARS]}]
    )

    with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
        response = client.chat.send(
            model=config.OPENROUTER_MODEL,
            stream=False,
            temperature=0.4,
            max_tokens=600,
            messages=messages,
        )
    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        return (
            "Sorry, I could not generate a reply right now. Please try "
            "again in a moment.",
            source,
        )
    return content.strip(), source


def chat_reply_stream(predicted_class, confidence, message, history):
    """Yield reply text chunks as they arrive from OpenRouter."""
    from openrouter import OpenRouter

    system_prompt, source = _build_system_prompt(predicted_class, confidence)
    messages = (
        [{"role": "system", "content": system_prompt}]
        + _trim_history(history)
        + [{"role": "user", "content": message[:MAX_MESSAGE_CHARS]}]
    )

    with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
        response = client.chat.send(
            model=config.OPENROUTER_MODEL,
            stream=True,
            temperature=0.4,
            max_tokens=600,
            messages=messages,
        )
        for chunk in response:
            delta = getattr(chunk.choices[0].delta, "content", None) if chunk.choices else None
            if delta:
                yield delta
