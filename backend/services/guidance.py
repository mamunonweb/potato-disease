"""Disease knowledge and OpenRouter-generated guidance.

Ported from the Streamlit app. The built-in DISEASE_INFO is the
fallback used automatically when OpenRouter is unavailable,
rate-limited, or not configured.
"""

import json
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import config

DISEASE_INFO = {
    "Potato___Early_blight": {
        "name": "Early Blight",
        "description": "A common potato leaf disease that can reduce plant growth and yield.",
        "symptoms": [
            "Brown or dark spots on leaves",
            "Circular or target-like patterns may appear",
            "Older leaves are often affected first",
            "Severely affected leaves can yellow and die",
        ],
        "causes": [
            "Fungal infection",
            "Warm and humid conditions",
            "Poor air circulation",
            "Infected plant debris",
        ],
        "actions": [
            "Remove severely affected leaves when practical",
            "Improve plant spacing and air circulation",
            "Avoid unnecessary overhead irrigation",
            "Remove infected plant debris",
            "Use locally recommended fungicide practices when appropriate",
        ],
        "prevention": [
            "Use healthy planting material",
            "Maintain field sanitation",
            "Avoid prolonged leaf wetness",
            "Monitor plants regularly",
        ],
    },
    "Potato___Late_blight": {
        "name": "Late Blight",
        "description": "A potentially fast-spreading potato disease, especially under cool and humid conditions.",
        "symptoms": [
            "Dark brown or black irregular lesions",
            "Water-soaked appearance may occur",
            "Lesions can expand quickly",
            "Leaves can collapse when infection becomes severe",
        ],
        "causes": [
            "Pathogen infection",
            "Cool and humid weather",
            "Extended leaf wetness",
            "Poor field sanitation",
        ],
        "actions": [
            "Remove severely infected plant material where practical",
            "Improve air circulation",
            "Avoid prolonged leaf wetness",
            "Monitor nearby plants carefully",
            "Follow locally recommended disease-management guidance",
        ],
        "prevention": [
            "Use disease-free planting material",
            "Inspect plants frequently",
            "Maintain field sanitation",
            "Avoid excessive irrigation",
            "Act early when symptoms appear",
        ],
    },
    "Potato___healthy": {
        "name": "Healthy",
        "description": "The model classified the uploaded potato leaf as healthy.",
        "symptoms": [
            "No strong disease pattern detected by the model",
            "Leaf appearance is generally consistent with a healthy class",
        ],
        "causes": [
            "No disease pattern was detected by the model",
        ],
        "actions": [
            "Continue regular monitoring",
            "Maintain proper irrigation",
            "Maintain balanced plant nutrition",
            "Keep the field clean",
        ],
        "prevention": [
            "Use healthy planting material",
            "Monitor leaves regularly",
            "Maintain appropriate plant spacing",
            "Control pests and weeds",
            "Maintain field hygiene",
        ],
    },
}

LLM_CONTENT_FIELDS = ("description", "symptoms", "causes", "actions", "prevention")

_guidance_cache = {}
_guidance_lock = threading.Lock()


def _valid_guidance(content):
    """Return only the expected, display-safe fields from an LLM response."""
    if not isinstance(content, dict):
        return None

    validated = {}
    if isinstance(content.get("description"), str) and content["description"].strip():
        validated["description"] = content["description"].strip()

    for field in ("symptoms", "causes", "actions", "prevention"):
        value = content.get(field)
        if not isinstance(value, list):
            return None
        items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if not items or len(items) > 8:
            return None
        validated[field] = items

    if len(validated) != len(LLM_CONTENT_FIELDS):
        return None
    return validated


def generate_disease_guidance(predicted_class):
    """Generate cached guidance, returning None when the provider is
    unavailable. Cached for GUIDANCE_TTL_SECONDS (default 24h)."""
    api_key = config.OPENROUTER_API_KEY
    if not api_key:
        return None

    now = time.time()
    with _guidance_lock:
        cached = _guidance_cache.get(predicted_class)
        if cached and now - cached[0] < config.GUIDANCE_TTL_SECONDS:
            return cached[1]

    try:
        from openrouter import OpenRouter

        base_info = DISEASE_INFO[predicted_class]
        with OpenRouter(api_key=api_key) as client:
            response = client.chat.send(
                model=config.OPENROUTER_MODEL,
                stream=False,
                temperature=0.2,
                max_tokens=700,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a cautious agricultural information assistant. "
                            "Return valid JSON only with exactly these fields: "
                            "description (string), symptoms (array of strings), "
                            "causes (array of strings), actions (array of strings), "
                            "prevention (array of strings). Provide general guidance "
                            "for potato plants. Do not claim certainty, invent facts, "
                            "or provide pesticide names, dosage, or application rates. "
                            "Recommend local agricultural guidance for treatment decisions."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Generate concise guidance for {base_info['name']}. "
                            "Use this existing reference as context, but improve its "
                            f"clarity without contradicting it:\n{json.dumps(base_info)}"
                        ),
                    },
                ],
            )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            return None

        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        guidance = _valid_guidance(json.loads(content))
    except Exception:
        # LLM content is an enhancement; prediction pages must remain available.
        return None

    if guidance:
        with _guidance_lock:
            _guidance_cache[predicted_class] = (now, guidance)
    return guidance


def get_disease_info(predicted_class):
    """Return display content and whether it came from OpenRouter."""
    fallback = DISEASE_INFO[predicted_class]
    generated = generate_disease_guidance(predicted_class)
    if not generated:
        return fallback, False

    info = dict(fallback)
    info.update(generated)
    return info, True


def check_openrouter_api_key():
    """Check the configured key without ever returning or displaying it."""
    api_key = config.OPENROUTER_API_KEY
    if not api_key:
        return False, "OPENROUTER_API_KEY is not configured."

    request = Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            key_data = payload.get("data", {})
            if key_data.get("disabled") is True:
                return False, "OpenRouter accepted the request, but this key is disabled."
            return True, "OpenRouter API key is valid and active."
    except HTTPError as exc:
        if exc.code == 401:
            return False, "OpenRouter rejected the API key (401 Unauthorized)."
        if exc.code == 429:
            return False, "OpenRouter rate-limited the key check (429 Too Many Requests)."
        return False, f"OpenRouter key check failed with HTTP {exc.code}."
    except URLError:
        return False, "Could not reach OpenRouter. Check the server network connection."
    except Exception:
        return False, "OpenRouter returned an unexpected response during the key check."
