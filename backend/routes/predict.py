"""Prediction endpoint: upload → prediction + Grad-CAM + guidance."""
import base64
import io
import logging

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from config import MAX_BATCH_FILES, MAX_UPLOAD_MB
from schemas import (
    BatchItemError,
    BatchItemSuccess,
    BatchResponse,
    GradcamInfo,
    GradcamSeverity,
    GuidanceInfo,
    PredictionResponse,
    TopPrediction,
)
from services import gradcam, guidance, model, uploads

router = APIRouter()

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "This is an AI-based preliminary classification and general "
    "information, not a definitive diagnosis. For serious or rapidly "
    "spreading crop disease, consult a qualified agricultural professional."
)


@router.post("/api/predict")
async def predict(image: UploadFile = File(...)) -> PredictionResponse:
    pil_image = await uploads.read_image(image)

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


HEALTHY_CLASS = "Potato___healthy"


@router.post("/api/predict/batch")
async def predict_batch(
    images: list[UploadFile] = File(...),
) -> BatchResponse:
    if len(images) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Too many images. Batch analysis accepts at most "
                f"{MAX_BATCH_FILES} files per request."
            ),
        )

    results: list[BatchItemSuccess | BatchItemError] = []

    for file in images:
        filename = file.filename or "unknown"
        try:
            uploads.validate_upload(file)
            data = await file.read()
            if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(
                    f"Image too large. Maximum size is {MAX_UPLOAD_MB} MB."
                )
            try:
                pil_image = Image.open(io.BytesIO(data))
            except Exception:
                raise ValueError("The file is not a readable image.")

            predicted_class, confidence, probabilities = model.predict_image(
                pil_image
            )
            probabilities_list = [
                float(p) for p in np.asarray(probabilities).reshape(-1)
            ]
            top = sorted(
                zip(model.CLASS_NAMES, probabilities_list),
                key=lambda pair: pair[1],
                reverse=True,
            )
            results.append(
                BatchItemSuccess(
                    status="ok",
                    filename=filename,
                    predicted_class=predicted_class,
                    display_name=model.DISPLAY_NAMES[predicted_class],
                    confidence=confidence,
                    top_predictions=[
                        TopPrediction(
                            className=name,
                            displayName=model.DISPLAY_NAMES[name],
                            probability=p,
                        )
                        for name, p in top
                    ],
                )
            )
        except HTTPException as exc:
            results.append(
                BatchItemError(
                    status="error", filename=filename, error=exc.detail
                )
            )
        except ValueError as exc:
            results.append(
                BatchItemError(
                    status="error", filename=filename, error=str(exc)
                )
            )
        except Exception:
            logger.exception("Batch item prediction failed for %s.", filename)
            results.append(
                BatchItemError(
                    status="error",
                    filename=filename,
                    error="The image could not be processed.",
                )
            )

    successes = [
        item for item in results if isinstance(item, BatchItemSuccess)
    ]
    healthy_count = sum(
        1 for item in successes if item.predicted_class == HEALTHY_CLASS
    )
    disease_count = len(successes) - healthy_count
    failed_count = len(results) - len(successes)

    return BatchResponse(
        results=results,
        healthy_count=healthy_count,
        disease_count=disease_count,
        failed_count=failed_count,
        disclaimer=DISCLAIMER,
    )
