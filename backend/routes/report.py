"""PDF report endpoint: image upload → downloadable report."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

from services import localization, report, uploads

router = APIRouter()


@router.post("/api/report")
async def generate_pdf_report(
    image: UploadFile = File(...),  # noqa: B008
    language: str = Form("en"),
) -> Response:
    filename = image.filename or "unknown"
    pil_image: Image.Image = await uploads.read_image(image)
    language = localization.normalize_language(language)

    try:
        pdf_bytes = report.generate_report(pil_image, filename, language)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="potato_disease_report.pdf"'},
    )
