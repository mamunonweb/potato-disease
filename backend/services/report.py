"""PDF report generation for a single analyzed leaf image."""

import os
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

from services import gradcam, guidance, localization, model

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOOGLE_SANS_REGULAR = os.path.join(
    _BACKEND_DIR, "assets", "GoogleSans-Regular.ttf"
)
GOOGLE_SANS_BOLD = os.path.join(_BACKEND_DIR, "assets", "GoogleSans-Bold.ttf")

_DISCLAIMERS = {
    "en": (
        "This report provides AI-based preliminary classification and general "
        "information. Grad-CAM attention severity, when available, is an "
        "experimental visualization metric and not a scientifically validated "
        "disease-severity percentage. For serious or rapidly spreading crop "
        "disease, consult a qualified agricultural professional."
    ),
    "bn": (
        "এই প্রতিবেদনে এআই-ভিত্তিক প্রাথমিক শ্রেণীবিভাগ ও সাধারণ তথ্য রয়েছে। "
        "Grad-CAM মনোযোগের তীব্রতা, যদি পাওয়া যায়, একটি পরীক্ষামূলক ভিজুয়ালাইজেশন "
        "মাপ, বৈজ্ঞানিকভাবে যাচাইকৃত রোগের তীব্রতার শতাংশ নয়। গুরুতর বা দ্রুত ছড়ানো "
        "ফসলের রোগের জন্য একজন যোগ্য কৃষি পেশাজীবীর পরামর্শ নিন।"
    ),
}

_TEXT = {
    "en": {
        "title": "Potato Plant Disease Detection Report",
        "date": "Date",
        "image": "Image",
        "prediction": "Prediction",
        "confidence": "Confidence",
        "gradcamLayer": "Grad-CAM layer",
        "attentionSeverity": "Attention severity estimate",
        "highlyActivated": "highly activated area",
        "gradcamUnavailable": "Not available for this model architecture.",
        "gradcamUnavailableBody": (
            "Grad-CAM unavailable. The prediction was generated successfully, "
            "but the saved model could not provide a compatible Grad-CAM graph."
        ),
        "top3": "Top-3 Class Probabilities",
        "rank": "Rank",
        "className": "Class",
        "probability": "Probability",
        "sections": [
            ("Description", "description"),
            ("Symptoms", "symptoms"),
            ("Possible Causes", "causes"),
            ("Recommended Actions", "actions"),
            ("Prevention", "prevention"),
        ],
        "severity": {"Mild": "Mild", "Moderate": "Moderate", "Severe": "Severe"},
    },
    "bn": {
        "title": "আলু রোগ শনাক্তকরণ প্রতিবেদন",
        "date": "তারিখ",
        "image": "ছবি",
        "prediction": "পূর্বাভাস",
        "confidence": "আস্থা",
        "gradcamLayer": "Grad-CAM স্তর",
        "attentionSeverity": "মনোযোগের তীব্রতার অনুমান",
        "highlyActivated": "অত্যন্ত সক্রিয় এলাকা",
        "gradcamUnavailable": "এই মডেল স্থাপত্যের জন্য উপলব্ধ নয়।",
        "gradcamUnavailableBody": (
            "Grad-CAM উপলব্ধ নয়। পূর্বাভাস সফলভাবে তৈরি হয়েছে, তবে সংরক্ষিত "
            "মডেলটি সামঞ্জস্যপূর্ণ Grad-CAM গ্রাফ দিতে পারেনি।"
        ),
        "top3": "শীর্ষ-৩ শ্রেণির সম্ভাবনা",
        "rank": "ক্রম",
        "className": "শ্রেণি",
        "probability": "সম্ভাবনা",
        "sections": [
            ("বর্ণনা", "description"),
            ("উপসর্গ", "symptoms"),
            ("সম্ভাব্য কারণ", "causes"),
            ("সুপারিশকৃত পদক্ষেপ", "actions"),
            ("প্রতিরোধ", "prevention"),
        ],
        "severity": {"Mild": "মৃদু", "Moderate": "মাঝারি", "Severe": "তীব্র"},
    },
}

_fonts_registered = False


def _register_fonts():
    """Register the bundled Google Sans faces (Latin + Bengali) once."""
    global _fonts_registered
    if _fonts_registered:
        return
    if os.path.exists(GOOGLE_SANS_REGULAR):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        pdfmetrics.registerFont(TTFont("GoogleSans", GOOGLE_SANS_REGULAR))
        if os.path.exists(GOOGLE_SANS_BOLD):
            pdfmetrics.registerFont(TTFont("GoogleSans-Bold", GOOGLE_SANS_BOLD))
            pdfmetrics.registerFontFamily(
                "GoogleSans",
                normal="GoogleSans",
                bold="GoogleSans-Bold",
                italic="GoogleSans",
                boldItalic="GoogleSans-Bold",
            )
    _fonts_registered = True


def _body_font():
    _register_fonts()
    return "GoogleSans" if os.path.exists(GOOGLE_SANS_REGULAR) else "Helvetica"


def _bold_font():
    _register_fonts()
    return (
        "GoogleSans-Bold"
        if os.path.exists(GOOGLE_SANS_BOLD)
        else "Helvetica-Bold"
    )


def _png_bytes(image: Image.Image) -> BytesIO:
    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_report(
    pil_image: Image.Image, filename: str, language=localization.DEFAULT_LANGUAGE
) -> bytes:
    language = localization.normalize_language(language)
    text = _TEXT[language]
    font = _body_font()
    bold_font = _bold_font()

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

    info, _ = guidance.get_disease_info(predicted_class, language)

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
    for style in styles.byName.values():
        style.fontName = font
    styles["Title"].fontName = bold_font
    for heading in ("Heading1", "Heading2", "Heading3"):
        if heading in styles.byName:
            styles[heading].fontName = bold_font
    story = [
        Paragraph(text["title"], styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            f"<b>{text['date']}:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["BodyText"],
        ),
        Paragraph(f"<b>{text['image']}:</b> {filename}", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph(
            f"<b>{text['prediction']}:</b> "
            f"{model.display_name(predicted_class, language)}",
            styles["Heading2"],
        ),
        Paragraph(
            f"<b>{text['confidence']}:</b> {confidence * 100:.2f}%",
            styles["BodyText"],
        ),
        Paragraph(
            f"<b>{text['gradcamLayer']}:</b> {layer_name}", styles["BodyText"]
        ),
    ]

    if gradcam_available:
        severity_label = text["severity"].get(severity_level, severity_level)
        story.append(
            Paragraph(
                f"<b>{text['attentionSeverity']}:</b> {severity_label} "
                f"({severity_ratio * 100:.2f}% {text['highlyActivated']})",
                styles["BodyText"],
            )
        )
    else:
        story.append(
            Paragraph(
                f"<b>Grad-CAM:</b> {text['gradcamUnavailable']}",
                styles["BodyText"],
            )
        )
    story.append(Spacer(1, 12))

    original_png = _png_bytes(pil_image)
    cells: list = [ReportLabImage(original_png, width=3.1 * inch, height=3.1 * inch)]
    if overlay_png is not None:
        cells.append(ReportLabImage(overlay_png, width=3.1 * inch, height=3.1 * inch))
    else:
        cells.append(Paragraph(text["gradcamUnavailableBody"], styles["BodyText"]))

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

    story.append(Paragraph(text["top3"], styles["Heading2"]))
    probability_rows = [[text["rank"], text["className"], text["probability"]]]
    for rank, (class_name, value) in enumerate(top, 1):
        probability_rows.append(
            [
                str(rank),
                model.display_name(class_name, language),
                f"{value * 100:.2f}%",
            ]
        )
    probability_table = Table(
        probability_rows, colWidths=[0.7 * inch, 3.3 * inch, 2.0 * inch]
    )
    probability_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(probability_table)
    story.append(Spacer(1, 12))

    for title, key in text["sections"]:
        story.append(Paragraph(title, styles["Heading2"]))
        value = info[key]
        if isinstance(value, list):
            for item in value:
                story.append(Paragraph(f"\u2022 {item}", styles["BodyText"]))
        else:
            story.append(Paragraph(str(value), styles["BodyText"]))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 10))
    story.append(Paragraph(_DISCLAIMERS[language], styles["BodyText"]))

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()
