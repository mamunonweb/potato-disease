"""Lazy, cached model loading and image prediction.

TensorFlow is imported lazily so the API can boot and serve /health
on machines without TF installed. The model is loaded once per worker.
"""

import logging
import os
import threading

import numpy as np
from PIL import Image

import config

logger = logging.getLogger(__name__)

IMG_SIZE = (224, 224)

CLASS_NAMES = [
    "Bacteria",
    "Fungi",
    "Healthy",
    "Nematode",
    "Pest",
    "Phytopthora",
    "Virus",
]

DISPLAY_NAMES = {
    "Bacteria": "Bacterial Disease",
    "Fungi": "Fungal Disease",
    "Healthy": "Healthy",
    "Nematode": "Nematode Damage",
    "Pest": "Pest Damage",
    "Phytopthora": "Phytophthora Disease",
    "Virus": "Viral Disease",
}

LOW_CONFIDENCE_THRESHOLD = 0.60
UNCERTAIN_CONFIDENCE = 0.55
UNCERTAIN_ENTROPY = 0.80

_model = None
_model_error = None
_model_lock = threading.Lock()


def get_model():
    """Load the model once per worker; returns (model, error)."""
    global _model, _model_error
    if _model is not None or _model_error is not None:
        return _model, _model_error

    with _model_lock:
        if _model is not None or _model_error is not None:
            return _model, _model_error

        if not os.path.exists(config.MODEL_PATH):
            _model_error = "Model file not found on the server."
            return None, _model_error

        try:
            import tensorflow as tf

            _model = tf.keras.models.load_model(config.MODEL_PATH, compile=False)
            output_shape = getattr(_model, "output_shape", None)
            if not output_shape or output_shape[-1] != len(CLASS_NAMES):
                raise ValueError("The model output does not match the configured classes.")
        except Exception:
            # Log the real cause server-side; clients only get a safe message.
            logger.exception("Failed to load the model from the configured path.")
            _model_error = "The model could not be loaded on the server."
        return _model, _model_error


def preprocess_image(image):
    image = image.convert("RGB").resize(IMG_SIZE)
    array = np.asarray(image, dtype=np.float32) / 255.0
    return np.expand_dims(array, axis=0)


def verify_potato_leaf_input(image):
    """Conservative input gate for the seven-class potato-leaf model.

    A safety filter for obvious unrelated images, not a guaranteed
    potato-vs-non-potato classifier.
    """
    rgb = np.asarray(image.convert("RGB").resize(IMG_SIZE), dtype=np.float32)
    hsv = np.asarray(Image.fromarray(np.uint8(rgb)).convert("HSV"), dtype=np.float32)
    h = hsv[:, :, 0]
    s = hsv[:, :, 1] / 255.0
    v = hsv[:, :, 2] / 255.0

    green_mask = (h >= 25) & (h <= 105) & (s >= 0.20) & (v >= 0.18)
    brown_mask = (h >= 5) & (h <= 35) & (s >= 0.20) & (v >= 0.18)

    green_ratio = float(np.mean(green_mask))
    brown_ratio = float(np.mean(brown_mask))
    colorful_ratio = float(np.mean(s >= 0.15))

    gray = np.mean(rgb, axis=2)
    contrast = float(np.std(gray))

    leaf_color_ratio = green_ratio + 0.35 * brown_ratio
    color_ok = leaf_color_ratio >= 0.10 and colorful_ratio >= 0.18
    contrast_ok = contrast >= 18.0

    return bool(color_ok and contrast_ok)


def predict_image(image):
    """Predict a class from a PIL image; raises ValueError on rejection.

    Returns (class_name, confidence, probabilities).
    """
    if not verify_potato_leaf_input(image):
        raise ValueError(
            "This image does not appear to be a potato leaf. "
            "Please upload a clear potato leaf photo."
        )

    model, model_error = get_model()
    if model is None:
        raise ValueError(model_error or "The model is unavailable.")

    processed = preprocess_image(image)
    output = np.asarray(model.predict(processed, verbose=0))

    if output.ndim == 2:
        probabilities = output[0]
    else:
        probabilities = output.reshape(-1)

    if (
        np.min(probabilities) < 0
        or np.max(probabilities) > 1.0
        or not np.isclose(np.sum(probabilities), 1.0, atol=1e-3)
    ):
        exp_values = np.exp(probabilities - np.max(probabilities))
        probabilities = exp_values / np.sum(exp_values)

    if len(probabilities) != len(CLASS_NAMES):
        raise ValueError("The model output does not match the expected classes.")

    index = int(np.argmax(probabilities))
    class_name = CLASS_NAMES[index]
    confidence = float(probabilities[index])

    safe = np.clip(probabilities, 1e-8, 1.0)
    entropy = float(-np.sum(safe * np.log(safe)) / np.log(len(safe)))

    if confidence < UNCERTAIN_CONFIDENCE and entropy > UNCERTAIN_ENTROPY:
        raise ValueError(
            "The image could not be confidently identified as a potato "
            "leaf. Please upload a clear potato leaf photo."
        )

    return class_name, confidence, probabilities
