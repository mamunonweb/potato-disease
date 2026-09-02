"""PDF report generation for a single analyzed leaf image."""

from datetime import datetime
from io import BytesIO

import numpy as np
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as ReportLabImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from services import gradcam, guidance, model

DISCLAIMER = (
    "This report provides AI-based preliminary classification and general "
    "information. Grad-CAM attention severity, when available, is an "
    "experimental visualization metric and not a scientifically validated "
    "disease-severity percentage. For serious or rapidly spreading crop "
    "disease, consult a qualified agricultural professional."
)

SECTIONS = [
    ("Description", "description"),
    ("Symptoms", "symptoms"),
    ("Possible Causes", "causes"),
    ("Recommended Actions", "actions"),
    ("Prevention", "prevention"),
]


def _png_bytes(image: Image.Image) -> BytesIO:
    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_report(pil_image: Image.Image, filename: str) -> bytes:
    predicted_class, confidence, probabilities = model.predict_image(pil_image)

    probabilities_list = [float(p) for p in np.asarray(probabilities).reshape(-1)]
    top = sorted(
        zip(model.CLASS_NAMES, probabilities_list),
        key=lambda pair: pair[1],
        reverse=True,
    )[:3]

    gradcam_available = False
    overlay_png = None
    layer_name = "Not available"
    severity_ratio = 0.0
    severity_level = "Not available"

    try:
        current_model, model_error = model.get_model()
        if current_model is None:
            raise ValueError(model_error or "Model unavailable.")
        heatmap, layer_name = gradcam.make_gradcam(
            current_model, pil_image, model.CLASS_NAMES.index(predicted_class)
        )
        severity_ratio, severity_level = gradcam.estimate_attention_severity(heatmap)
        overlay_png = _png_bytes(gradcam.make_overlay(pil_image, heatmap))
        gradcam_available = True
    except Exception:
        # The report must still be generated when Grad-CAM is unavailable.
        pass

    info, _ = guidance.get_disease_info(predicted_class)

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Potato Plant Disease Detection Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["BodyText"],
        ),
        Paragraph(f"<b>Image:</b> {filename}", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph(
            f"<b>Prediction:</b> {model.DISPLAY_NAMES[predicted_class]}",
            styles["Heading2"],
        ),
        Paragraph(f"<b>Confidence:</b> {confidence * 100:.2f}%", styles["BodyText"]),
        Paragraph(f"<b>Grad-CAM layer:</b> {layer_name}", styles["BodyText"]),
    ]

    if gradcam_available:
        story.append(
            Paragraph(
                f"<b>Attention severity estimate:</b> {severity_level} "
                f"({severity_ratio * 100:.2f}% highly activated area)",
                styles["BodyText"],
            )
        )
    else:
        story.append(
            Paragraph(
                "<b>Grad-CAM:</b> Not available for this model architecture.",
                styles["BodyText"],
            )
        )
    story.append(Spacer(1, 12))

    original_png = _png_bytes(pil_image)
    cells: list = [ReportLabImage(original_png, width=3.1 * inch, height=3.1 * inch)]
    if overlay_png is not None:
        cells.append(ReportLabImage(overlay_png, width=3.1 * inch, height=3.1 * inch))
    else:
        cells.append(
            Paragraph(
                "<b>Grad-CAM unavailable.</b> The prediction was generated "
                "successfully, but the saved model could not provide a "
                "compatible Grad-CAM graph.",
                styles["BodyText"],
            )
        )

    image_table = Table([cells], colWidths=[3.2 * inch, 3.2 * inch])
    image_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(image_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Top-3 Class Probabilities", styles["Heading2"]))
    probability_rows = [["Rank", "Class", "Probability"]]
    for rank, (class_name, value) in enumerate(top, 1):
        probability_rows.append([str(rank), model.DISPLAY_NAMES[class_name], f"{value * 100:.2f}%"])
    probability_table = Table(probability_rows, colWidths=[0.7 * inch, 3.3 * inch, 2.0 * inch])
    probability_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(probability_table)
    story.append(Spacer(1, 12))

    for title, key in SECTIONS:
        story.append(Paragraph(title, styles["Heading2"]))
        value = info[key]
        if isinstance(value, list):
            for item in value:
                story.append(Paragraph(f"\u2022 {item}", styles["BodyText"]))
        else:
            story.append(Paragraph(str(value), styles["BodyText"]))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 10))
    story.append(Paragraph(DISCLAIMER, styles["BodyText"]))

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()
