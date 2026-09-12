"""Environment-based settings. Secrets never live in source code."""

import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(os.path.dirname(BACKEND_DIR), "explainable_cnn_model.keras"),
)
# Chat/guidance provider: "openrouter" or "opencode".
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "openrouter").strip().lower()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "deepseek-v4.1-flash")
OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:4173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_BATCH_FILES = int(os.getenv("MAX_BATCH_FILES", "12"))
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

PRELOAD_MODEL = os.getenv("PRELOAD_MODEL", "0") == "1"

GUIDANCE_TTL_SECONDS = int(os.getenv("GUIDANCE_TTL_SECONDS", "86400"))
CHAT_MAX_HISTORY_TURNS = int(os.getenv("CHAT_MAX_HISTORY_TURNS", "20"))
CHAT_MAX_MESSAGE_CHARS = int(os.getenv("CHAT_MAX_MESSAGE_CHARS", "2000"))
