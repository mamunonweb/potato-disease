"""Language codes and helpers shared by guidance, chat, and reports."""

SUPPORTED_LANGUAGES = ("en", "bn")
DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES = {
    "en": "English",
    "bn": "Bengali (বাংলা)",
}


def normalize_language(code):
    """Return a supported language code, falling back to the default."""
    if not code:
        return DEFAULT_LANGUAGE
    primary = str(code).strip().lower().replace("_", "-").split("-")[0]
    return primary if primary in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def language_name(code):
    return LANGUAGE_NAMES[normalize_language(code)]
