"""Grad-CAM explainability, ported from the Streamlit app.

Every function takes the model as an argument so nothing depends on
module-level singletons. Grad-CAM is optional: failures degrade to a
None heatmap instead of failing the prediction.
"""
import numpy as np
from PIL import Image

from services.model import IMG_SIZE


def find_gradcam_target(container):
    """Find the last Conv2D layer and the model/container that owns it."""
    if not hasattr(container, "layers"):
        return None, None

    for layer in reversed(container.layers):
        if isinstance(layer, _conv2d_cls()):
            return layer, container
        if hasattr(layer, "layers"):
            found_layer, owner = find_gradcam_target(layer)
            if found_layer is not None:
                return found_layer, owner
    return None, None


def _conv2d_cls():
    import tensorflow as tf

    return tf.keras.layers.Conv2D


def get_gradcam_model(model):
    """Build a Grad-CAM model; handles nested model/backbone layouts."""
    conv_layer, owner = find_gradcam_target(model)

    if conv_layer is None:
        raise ValueError(
            "No convolutional layer was found in the loaded model."
        )

    import tensorflow as tf

    if owner is model:
        return tf.keras.Model(
            inputs=model.inputs,
            outputs=[conv_layer.output, model.output],
        ), conv_layer.name

    owner_index = next(
        i for i, layer in enumerate(model.layers) if layer is owner
    )

    x = owner.output
    for layer in model.layers[owner_index + 1:]:
        if isinstance(layer, tf.keras.layers.InputLayer):
            continue
        x = layer(x)

    grad_model = tf.keras.Model(
        inputs=owner.input, outputs=[conv_layer.output, x]
    )
    return grad_model, conv_layer.name


def make_gradcam(model, image, class_index):
    """Return (heatmap, layer_name) for the requested class index."""
    import tensorflow as tf

    from services.model import preprocess_image

    grad_model, layer_name = get_gradcam_model(model)
    input_tensor = preprocess_image(image)

    with tf.GradientTape() as tape:
        conv_output, predictions = grad_model(input_tensor, training=False)
        score = predictions[:, class_index]

    gradients = tape.gradient(score, conv_output)
    if gradients is None:
        raise ValueError(
            "Gradients were not produced for the selected layer."
        )

    if len(conv_output.shape) != 4:
        raise ValueError("Unsupported Grad-CAM feature map shape.")

    weights = tf.reduce_mean(gradients, axis=(1, 2))
    conv_output = conv_output[0]
    weights = weights[0]

    heatmap = tf.reduce_sum(conv_output * weights, axis=-1)
    heatmap = tf.maximum(heatmap, 0)
    maximum = tf.reduce_max(heatmap)

    if float(maximum) > 0:
        heatmap = heatmap / maximum

    return heatmap.numpy(), layer_name


def make_overlay(image, heatmap):
    """Blend a dependency-free RGB heatmap over the original image."""
    original = image.convert("RGB").resize(IMG_SIZE)

    heat = Image.fromarray(
        np.uint8(np.clip(heatmap * 255, 0, 255))
    ).resize(IMG_SIZE)
    heat_array = np.asarray(heat, dtype=np.float32) / 255.0

    red = heat_array
    green = np.sqrt(heat_array)
    blue = 1.0 - heat_array

    rgb = np.stack([red, green, blue], axis=-1)
    rgb = np.uint8(np.clip(rgb * 255, 0, 255))

    heat_rgb = Image.fromarray(rgb)
    return Image.blend(original, heat_rgb, 0.45)


def estimate_attention_severity(heatmap):
    """Experimental Grad-CAM attention estimate, not a validated
    percentage of infected tissue."""
    heatmap = np.asarray(heatmap, dtype=np.float32)
    if heatmap.size == 0:
        return 0.0, "Unknown"

    normalized = np.clip(heatmap, 0.0, 1.0)
    active_ratio = float(np.mean(normalized >= 0.55))

    if active_ratio < 0.15:
        level = "Mild"
    elif active_ratio < 0.35:
        level = "Moderate"
    else:
        level = "Severe"

    return active_ratio, level
