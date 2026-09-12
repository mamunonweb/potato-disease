"""Disease knowledge and provider-generated guidance.

The built-in DISEASE_INFO is the fallback used automatically when the
configured provider is unavailable, rate-limited, or not configured.
"""

import json
import threading
import time

import config
from services import llm, localization

_DISEASE_INFO_EN = {
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

_DISEASE_INFO_BN = {
    "Bacteria": {
        "name": "ব্যাকটেরিয়াজনিত রোগ",
        "description": "আলুর পাতায় ব্যাকটেরিয়াজনিত রোগের সাথে সম্পর্কিত দৃশ্যমান নিদর্শনের একটি বিস্তৃত মডেল শ্রেণি। এটি নির্দিষ্ট কোনো ব্যাকটেরিয়া শনাক্ত করে না।",
        "symptoms": [
            "পানিতে ভেজা, বাদামি বা গাঢ় পাতার ক্ষত",
            "আক্রান্ত টিস্যুর চারপাশে হলুদ হয়ে যাওয়া বা শুকিয়ে যাওয়া",
            "অনুকূল পরিস্থিতিতে ক্ষত বড় হতে পারে",
            "তীব্রভাবে আক্রান্ত টিস্যু ভেঙে পড়তে পারে",
        ],
        "causes": [
            "ব্যাকটেরিয়াজনিত রোগজীবাণু",
            "ভেজা বা আর্দ্র পরিবেশ",
            "আক্রান্ত রোপণ উপকরণ বা আবর্জনা",
            "দূষিত যন্ত্রপাতি, পানি বা পরিচর্যা",
        ],
        "actions": [
            "সম্ভব হলে তীব্রভাবে আক্রান্ত অংশ সরিয়ে ফেলুন",
            "অপ্রয়োজনীয় ওপর থেকে সেচ এড়িয়ে চলুন",
            "গাছের মধ্যে যন্ত্রপাতি জীবাণুমুক্ত করুন",
            "আক্রান্ত আবর্জনা চাষের এলাকা থেকে সরান",
            "চিকিৎসার সিদ্ধান্তের আগে স্থানীয় কৃষি পরামর্শ নিন",
        ],
        "prevention": [
            "সুস্থ রোপণ উপকরণ ব্যবহার করুন",
            "ক্ষেত পরিষ্কার-পরিচ্ছন্ন রাখুন",
            "পাতা দীর্ঘক্ষণ ভেজা থাকা কমান",
            "কাছাকাছি গাছ নিয়মিত পর্যবেক্ষণ করুন",
        ],
    },
    "Fungi": {
        "name": "ছত্রাকজনিত রোগ",
        "description": "আলুর পাতায় ছত্রাকজনিত রোগের সাথে সম্পর্কিত দৃশ্যমান নিদর্শনের একটি বিস্তৃত মডেল শ্রেণি। এটি নির্দিষ্ট কোনো ছত্রাক প্রজাতি শনাক্ত করে না।",
        "symptoms": [
            "পাতায় দাগ বা অনিয়মিত ক্ষত",
            "ক্ষতিগ্রস্ত টিস্যুর চারপাশে হলুদ হয়ে যাওয়া",
            "গুঁড়ো, তুলতুলে বা বিবর্ণ বৃদ্ধি দেখা দিতে পারে",
            "তীব্র সংক্রমণে পাতা ঝরে যেতে পারে",
        ],
        "causes": [
            "ছত্রাকজনিত রোগজীবাণু",
            "উষ্ণ, আর্দ্র বা দীর্ঘস্থায়ীভাবে ভেজা পরিবেশ",
            "দুর্বল বায়ু চলাচল",
            "আক্রান্ত ফসলের অবশেষ",
        ],
        "actions": [
            "সম্ভব হলে তীব্রভাবে আক্রান্ত অংশ সরিয়ে ফেলুন",
            "গাছের দূরত্ব ও বায়ু চলাচল উন্নত করুন",
            "পাতা দীর্ঘক্ষণ ভেজা থাকা এড়িয়ে চলুন",
            "আক্রান্ত আবর্জনা সরান",
            "স্থানীয়ভাবে সুপারিশকৃত রোগব্যবস্থাপনার নির্দেশনা অনুসরণ করুন",
        ],
        "prevention": [
            "সুস্থ রোপণ উপকরণ ব্যবহার করুন",
            "ক্ষেত পরিষ্কার-পরিচ্ছন্ন রাখুন",
            "অপ্রয়োজনীয় ওপর থেকে সেচ এড়িয়ে চলুন",
            "গাছ নিয়মিত পরীক্ষা করুন",
        ],
    },
    "Healthy": {
        "name": "সুস্থ",
        "description": "মডেলটি আপলোড করা আলুর পাতাটিকে সুস্থ হিসাবে শ্রেণীবদ্ধ করেছে।",
        "symptoms": [
            "মডেল কোনো শক্তিশালী রোগের নিদর্শন পায়নি",
            "পাতার চেহারা সাধারণত সুস্থ শ্রেণির সাথে সঙ্গতিপূর্ণ",
        ],
        "causes": [
            "মডেল কোনো রোগের নিদর্শন শনাক্ত করেনি",
        ],
        "actions": [
            "নিয়মিত পর্যবেক্ষণ চালিয়ে যান",
            "যথাযথ সেচ বজায় রাখুন",
            "সুষম উদ্ভিদ পুষ্টি বজায় রাখুন",
            "ক্ষেত পরিষ্কার রাখুন",
        ],
        "prevention": [
            "সুস্থ রোপণ উপকরণ ব্যবহার করুন",
            "পাতা নিয়মিত পর্যবেক্ষণ করুন",
            "উপযুক্ত গাছের দূরত্ব বজায় রাখুন",
            "পোকামাকড় ও আগাছা নিয়ন্ত্রণ করুন",
            "ক্ষেতের পরিচ্ছন্নতা বজায় রাখুন",
        ],
    },
    "Phytopthora": {
        "name": "ফাইটোফথোরা রোগ",
        "description": "ডেটাসেটে Phytopthora নামে চিহ্নিত এবং Phytophthora হিসাবে প্রদর্শিত একটি মডেল শ্রেণি। একটি পাতার ছবি রোগজীবাণু নিশ্চিত করতে বা একই রকম সব অবস্থা আলাদা করতে পারে না।",
        "symptoms": [
            "গাঢ় বা পানিতে ভেজা পাতার ক্ষত",
            "দ্রুত ছড়িয়ে পড়া ক্ষতিগ্রস্ত এলাকা দেখা দিতে পারে",
            "আক্রান্ত পাতা হলুদ হয়ে যাওয়া বা ভেঙে পড়া",
            "কাণ্ড বা কন্দের উপসর্গও পরীক্ষা করার প্রয়োজন হতে পারে",
        ],
        "causes": [
            "ফাইটোফথোরা-সদৃশ রোগজীবাণুর কার্যকলাপ",
            "ঠান্ডা, ভেজা বা আর্দ্র পরিবেশ",
            "দীর্ঘস্থায়ীভাবে পাতা ভেজা থাকা",
            "আক্রান্ত গাছের উপকরণ বা ক্ষেতের আবর্জনা",
        ],
        "actions": [
            "সম্ভব হলে আক্রান্ত গাছ আলাদা করে পরীক্ষা করুন",
            "দীর্ঘক্ষণ পাতা ভেজা থাকা কমান",
            "আক্রান্ত আবর্জনা নিরাপদে সরান",
            "দ্রুত ছড়িয়ে পড়ার জন্য কাছাকাছি গাছ পর্যবেক্ষণ করুন",
            "দ্রুত স্থানীয় কৃষি পরামর্শ নিন",
        ],
        "prevention": [
            "রোগমুক্ত রোপণ উপকরণ ব্যবহার করুন",
            "নিকাশী ও বায়ু চলাচল বজায় রাখুন",
            "ভেজা, দূষিত মাটি বা আবর্জনা স্থানান্তর এড়িয়ে চলুন",
            "ভেজা আবহাওয়ায় নিয়মিত গাছ পরীক্ষা করুন",
        ],
    },
    "Virus": {
        "name": "ভাইরাসজনিত রোগ",
        "description": "আলুর পাতায় ভাইরাসজনিত রোগের সাথে সম্পর্কিত দৃশ্যমান নিদর্শনের একটি বিস্তৃত মডেল শ্রেণি। নিশ্চিতকরণের জন্য পরীক্ষাগার বা বিশেষজ্ঞ পরীক্ষার প্রয়োজন হতে পারে।",
        "symptoms": [
            "মোজাইক, দাগ বা অস্বাভাবিক পাতার রঙ",
            "পাতা কোঁকড়ানো বা বিকৃত হওয়া",
            "বৃদ্ধি ব্যাহত হওয়া বা গাছের প্রাণশক্তি কমে যাওয়া",
            "জাত ও সংক্রমণের সময় অনুযায়ী উপসর্গ ভিন্ন হতে পারে",
        ],
        "causes": [
            "উদ্ভিদ ভাইরাস",
            "আক্রান্ত বীজ বা রোপণ উপকরণ",
            "পোকামাকড় বাহক বা পরিচর্যার মাধ্যমে সংক্রমণ",
            "কাছাকাছি আক্রান্ত গাছ",
        ],
        "actions": [
            "সম্ভব হলে তীব্র উপসর্গযুক্ত গাছ সরিয়ে ফেলুন",
            "স্থানীয় নির্দেশনা অনুযায়ী সম্ভাব্য বাহক পোকা নিয়ন্ত্রণ করুন",
            "গাছের মধ্যে যন্ত্রপাতি জীবাণুমুক্ত করুন",
            "উপসর্গযুক্ত গাছ থেকে বংশবিস্তার এড়িয়ে চলুন",
            "চিকিৎসার সিদ্ধান্তের আগে বিশেষজ্ঞের নিশ্চয়তা নিন",
        ],
        "prevention": [
            "প্রত্যয়িত বা সুস্থ রোপণ উপকরণ ব্যবহার করুন",
            "গাছ ও বাহক পোকার সংখ্যা পর্যবেক্ষণ করুন",
            "স্বেচ্ছা-উদ্ভিদ ও ফসলের অবশেষ সরান",
            "ক্ষেতের পরিচ্ছন্নতা বজায় রাখুন",
        ],
    },
}

DISEASE_INFO = {
    "en": _DISEASE_INFO_EN,
    "bn": _DISEASE_INFO_BN,
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


def generate_disease_guidance(
    predicted_class, language=localization.DEFAULT_LANGUAGE
):
    """Generate cached guidance in the requested language, returning None when
    the provider is unavailable. Cached for GUIDANCE_TTL_SECONDS (default 24h)."""
    if not llm.is_configured():
        return None

    language = localization.normalize_language(language)
    cache_key = (predicted_class, language)

    now = time.time()
    with _guidance_lock:
        cached = _guidance_cache.get(cache_key)
        if cached and now - cached[0] < config.GUIDANCE_TTL_SECONDS:
            return cached[1]

    try:
        base_info = DISEASE_INFO[language][predicted_class]
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
                        "Recommend local agricultural guidance for treatment decisions. "
                        f"Write every field in {localization.language_name(language)}."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate concise guidance for {base_info['name']}. "
                        "Use this existing reference as context, but improve its "
                        "clarity without contradicting it:\n"
                        f"{json.dumps(base_info, ensure_ascii=False)}"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=1500,
            session=f"guidance:{predicted_class}:{language}",
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
            _guidance_cache[cache_key] = (now, guidance)
    return guidance


def is_supported_class(predicted_class):
    return predicted_class in DISEASE_INFO["en"]


def get_disease_info(predicted_class, language=localization.DEFAULT_LANGUAGE):
    """Return localized display content and the source of the guidance."""
    language = localization.normalize_language(language)
    fallback = DISEASE_INFO[language][predicted_class]
    generated = generate_disease_guidance(predicted_class, language)
    if not generated:
        return fallback, "builtin"

    info = dict(fallback)
    info.update(generated)
    return info, llm.resolve_provider()
