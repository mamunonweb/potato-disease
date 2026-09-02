"""Shared upload validation for image endpoints."""
import io
import os

from fastapi import HTTPException, UploadFile
from PIL import Image

from config import ALLOWED_CONTENT_TYPES, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB


def validate_upload(file: UploadFile) -> None:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if file.content_type not in ALLOWED_CONTENT_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload a JPG or PNG image.",
        )


async def read_image(file: UploadFile) -> Image.Image:
    validate_upload(file)
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Maximum size is {MAX_UPLOAD_MB} MB.",
        )
    try:
        return Image.open(io.BytesIO(data))
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="The uploaded file is not a readable image.",
        )
