"""Health endpoints. /health never touches the model; /health/ready does."""
from fastapi import APIRouter

from services import model

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
def ready() -> dict:
    loaded, error = model.get_model()
    return {"status": "ok", "modelLoaded": loaded is not None, "error": error}
