"""Disease-aware chatbot backed by the configured provider.

The CNN stays responsible for the prediction; the chat only discusses
the detected condition. Guidance is general information, not a
definitive diagnosis.
"""

import hashlib
import json

import config
from services import llm, localization
from services.guidance import get_disease_info
from services.model import display_name as class_display_name

SYSTEM_PROMPT_TEMPLATE = (
    "You are a cautious potato-plant-disease assistant. The user has "
    "received a CNN prediction of '{display_name}' with {confidence_pct:.1f}% "
    "confidence. Discuss this detected condition and related potato "
    "plant-care questions.\n\n"
    "Reference information:\n{info_json}\n\n"
    "Rules:\n"
    "- Reply only in {language_name}.\n"
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


def _build_system_prompt(predicted_class, confidence, language):
    info, source = get_disease_info(predicted_class, language)
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        display_name=class_display_name(predicted_class, language),
        confidence_pct=confidence * 100,
        info_json=json.dumps(info, ensure_ascii=False),
        language_name=localization.language_name(language),
    )
    return prompt, source


def _trim_history(history):
    """Keep only valid alternating turns, capped and length-limited."""
    trimmed = []
    for turn in (history or [])[-MAX_HISTORY_TURNS * 2 :]:
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


def _session_id(predicted_class, history, message, language):
    """Stable id for one conversation so opencode can route and cache it."""
    first_user_message = message
    for turn in history or []:
        content = str(turn.get("content", "")).strip()
        if turn.get("role") == "user" and content:
            first_user_message = content
            break
    seed = f"{predicted_class}:{language}:{first_user_message[:200]}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:32]


def chat_reply(predicted_class, confidence, message, history, language):
    """Return (reply_text, guidance_source) for one chat turn."""
    system_prompt, source = _build_system_prompt(
        predicted_class, confidence, language
    )
    messages = (
        [{"role": "system", "content": system_prompt}]
        + _trim_history(history)
        + [{"role": "user", "content": message[:MAX_MESSAGE_CHARS]}]
    )

    reply = llm.chat_completion(
        messages,
        temperature=0.4,
        max_tokens=1024,
        session=_session_id(predicted_class, history, message, language),
    )
    if not reply:
        return (
            "Sorry, I could not generate a reply right now. Please try again in a moment.",
            source,
        )
    return reply, source


def chat_reply_stream(predicted_class, confidence, message, history, language):
    """Yield reply text chunks from the configured provider."""
    system_prompt, _ = _build_system_prompt(predicted_class, confidence, language)
    messages = (
        [{"role": "system", "content": system_prompt}]
        + _trim_history(history)
        + [{"role": "user", "content": message[:MAX_MESSAGE_CHARS]}]
    )

    yield from llm.chat_completion_stream(
        messages,
        temperature=0.4,
        max_tokens=1024,
        session=_session_id(predicted_class, history, message, language),
    )
