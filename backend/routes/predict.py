"""Prediction endpoint: upload → prediction + Grad-CAM + guidance."""
import base64
import io
import logging
import os

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from config import ALLOWED_CONTENT_TYPES, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from schemas import (
    GradcamInfo,
    GradcamSeverity,
    GuidanceInfo,
    PredictionResponse,
    TopPrediction,
)
from services import gradcam, guidance, model

router = APIRouter()

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "This is an AI-based preliminary classification and general "
    "information, not a definitive diagnosis. For serious or rapidly "
    "spreading crop disease, consult a qualified agricultural professional."
)


def _validate_upload(file: UploadFile) -> None:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if file.content_type not in ALLOWED_CONTENT_TYPES or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload a JPG or PNG image.",
        )


@router.post("/api/predict")
async def predict(image: UploadFile = File(...)) -> PredictionResponse:
    _validate_upload(image)
    data = await image.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Maximum size is {MAX_UPLOAD_MB} MB.",
        )

    try:
        pil_image = Image.open(io.BytesIO(data))
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="The uploaded file is not a readable image.",
        )

    try:
        predicted_class, confidence, probabilities = model.predict_image(pil_image)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    probabilities_list = [
        float(p) for p in np.asarray(probabilities).reshape(-1)
    ]
    top = sorted(
        zip(model.CLASS_NAMES, probabilities_list),
        key=lambda pair: pair[1],
        reverse=True,
    )

    gradcam_payload: GradcamInfo | None = None
    gradcam_note = None
    try:
        current_model, model_error = model.get_model()
        if current_model is None:
            raise ValueError(model_error or "Model unavailable.")
        heatmap, layer_name = gradcam.make_gradcam(
            current_model, pil_image, model.CLASS_NAMES.index(predicted_class)
        )
        severity_ratio, severity_level = gradcam.estimate_attention_severity(heatmap)
        overlay = gradcam.make_overlay(pil_image, heatmap)
        overlay_buffer = io.BytesIO()
        overlay.save(overlay_buffer, format="PNG")
        data_uri = "data:image/png;base64," + base64.b64encode(
            overlay_buffer.getvalue()
        ).decode("ascii")
        gradcam_payload = GradcamInfo(
            image_data_uri=data_uri,
            layer_name=layer_name,
            severity=GradcamSeverity(ratio=severity_ratio, level=severity_level),
        )
    except Exception:
        # Do not fail the prediction because Grad-CAM is unavailable.
        logger.exception("Grad-CAM generation failed.")
        gradcam_note = (
            "The prediction was generated successfully, but Grad-CAM is "
            "unavailable for this model architecture."
        )

    info, generated = guidance.get_disease_info(predicted_class)

    return PredictionResponse(
        predicted_class=predicted_class,
        display_name=model.DISPLAY_NAMES[predicted_class],
        confidence=confidence,
        probabilities={
            name: float(p)
            for name, p in zip(model.CLASS_NAMES, probabilities_list)
        },
        top_predictions=[
            TopPrediction(
                className=name,
                displayName=model.DISPLAY_NAMES[name],
                probability=p,
            )
            for name, p in top
        ],
        gradcam=gradcam_payload,
        gradcam_note=gradcam_note,
        guidance=GuidanceInfo(
            source="openrouter" if generated else "builtin",
            **info,
        ),
        disclaimer=DISCLAIMER,
    )
