import os
import uuid
import json
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# =========================
# BASE PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_FOLDER = BASE_DIR / "generated_pdfs"

PDF_FOLDER.mkdir(exist_ok=True)


# =========================
# HELPERS
# =========================

def _safe_filename(phone):
    return phone.replace(":", "").replace("+", "")


def _build_pdf_path(phone):
    return PDF_FOLDER / f"{_safe_filename(phone)}.pdf"


# =========================
# MAIN PDF GENERATOR
# =========================

def generate_pdf(phone, data):
    """
    Generates kundali PDF.
    If already exists, returns existing file.
    """

    file_path = _build_pdf_path(phone)

    # -------------------------
    # RETURN CACHED PDF
    # -------------------------
    if file_path.exists():
        return str(file_path)

    # -------------------------
    # CREATE NEW PDF
    # -------------------------

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("BoloAstro Kundali Report", styles["Title"]))
    story.append(Spacer(1, 20))

    # Content
    for key, value in data.items():

        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value, indent=2, ensure_ascii=False)

        story.append(
            Paragraph(f"<b>{key}</b>: {value}", styles["Normal"])
        )
        story.append(Spacer(1, 12))

    story.append(PageBreak())

    doc.build(story)

    return str(file_path)
