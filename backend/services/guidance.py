"""Disease knowledge and provider-generated guidance.

The built-in DISEASE_INFO is the fallback used automatically when the
configured provider is unavailable, rate-limited, or not configured.
"""

import json
import threading
import time

import config
from services import llm

DISEASE_INFO = {
    "Bacteria": {
        "name": "Bacterial Disease",
        "description": "A broad model category for potato leaves with visual patterns associated with bacterial disease. It does not identify a specific bacterium.",
        "symptoms": [
            "Water-soaked, brown, or dark leaf lesions",
            "Yellowing or wilting around affected tissue",
            "Lesions may enlarge under favorable conditions",
            "Severely affected tissue may collapse",
        ],
        "causes": [
            "Bacterial pathogens",
            "Wet or humid conditions",
            "Infected planting material or debris",
            "Contaminated tools, water, or handling",
        ],
        "actions": [
            "Remove severely affected material when practical",
            "Avoid unnecessary overhead irrigation",
            "Disinfect tools between plants",
            "Remove infected debris from the growing area",
            "Seek local agricultural advice before treatment decisions",
        ],
        "prevention": [
            "Use healthy planting material",
            "Maintain field sanitation",
            "Reduce prolonged leaf wetness",
            "Monitor nearby plants regularly",
        ],
    },
    "Fungi": {
        "name": "Fungal Disease",
        "description": "A broad model category for potato leaves with visual patterns associated with fungal disease. It does not identify a specific fungal species.",
        "symptoms": [
            "Spots or irregular lesions on leaves",
            "Yellowing around damaged tissue",
            "Powdery, fuzzy, or discolored growth may occur",
            "Severe infection can cause leaf loss",
        ],
        "causes": [
            "Fungal pathogens",
            "Warm, humid, or persistently wet conditions",
            "Poor air circulation",
            "Infected crop residue",
        ],
        "actions": [
            "Remove severely affected material when practical",
            "Improve plant spacing and air circulation",
            "Avoid prolonged leaf wetness",
            "Remove infected debris",
            "Follow locally recommended disease-management guidance",
        ],
        "prevention": [
            "Use healthy planting material",
            "Maintain field sanitation",
            "Avoid unnecessary overhead irrigation",
            "Inspect plants regularly",
        ],
    },
    "Healthy": {
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
    "Phytopthora": {
        "name": "Phytophthora Disease",
        "description": "A model category labeled Phytopthora in the dataset and displayed as Phytophthora. A leaf image cannot confirm the pathogen or distinguish every look-alike condition.",
        "symptoms": [
            "Dark or water-soaked leaf lesions",
            "Rapidly expanding damaged areas may occur",
            "Yellowing or collapse of affected leaves",
            "Stem or tuber symptoms may also require inspection",
        ],
        "causes": [
            "Phytophthora-like pathogen activity",
            "Cool, wet, or humid conditions",
            "Extended leaf wetness",
            "Infected plant material or field debris",
        ],
        "actions": [
            "Separate and inspect affected plants when practical",
            "Reduce prolonged leaf wetness",
            "Remove infected debris safely",
            "Monitor nearby plants for rapid spread",
            "Consult local agricultural guidance promptly",
        ],
        "prevention": [
            "Use disease-free planting material",
            "Maintain drainage and air circulation",
            "Avoid moving wet, contaminated soil or debris",
            "Inspect plants regularly during wet weather",
        ],
    },
    "Virus": {
        "name": "Viral Disease",
        "description": "A broad model category for potato leaves with visual patterns associated with viral disease. Laboratory or expert testing may be needed for confirmation.",
        "symptoms": [
            "Mosaic, mottling, or unusual leaf coloration",
            "Leaf curling or distortion",
            "Stunting or reduced plant vigor",
            "Symptoms can vary with cultivar and infection timing",
        ],
        "causes": [
            "Plant viruses",
            "Infected seed or planting material",
            "Transmission by insect vectors or handling",
            "Infected nearby plants",
        ],
        "actions": [
            "Remove strongly symptomatic plants where practical",
            "Control likely vector pests using local guidance",
            "Disinfect tools between plants",
            "Avoid propagating from symptomatic plants",
            "Seek expert confirmation before making treatment decisions",
        ],
        "prevention": [
            "Use certified or healthy planting material",
            "Monitor plants and vector populations",
            "Remove volunteer plants and crop debris",
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
    if not llm.is_configured():
        return None

    now = time.time()
    with _guidance_lock:
        cached = _guidance_cache.get(predicted_class)
        if cached and now - cached[0] < config.GUIDANCE_TTL_SECONDS:
            return cached[1]

    try:
        base_info = DISEASE_INFO[predicted_class]
        content = llm.chat_completion(
            [
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
            temperature=0.2,
            max_tokens=1500,
            session=f"guidance:{predicted_class}",
        )
        if not content:
            return None

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
    """Return display content and the source of the guidance."""
    fallback = DISEASE_INFO[predicted_class]
    generated = generate_disease_guidance(predicted_class)
    if not generated:
        return fallback, "builtin"

    info = dict(fallback)
    info.update(generated)
    return info, llm.resolve_provider()
