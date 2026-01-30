import os
import uuid
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER = os.path.join(BASE_DIR, "generated_pdfs")
os.makedirs(PDF_FOLDER, exist_ok=True)


def generate_pdf(phone, data):

    filename = f"{phone.replace(':','')}_{uuid.uuid4()}.pdf"
    file_path = os.path.join(PDF_FOLDER, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("BoloAstro Kundali Report", styles["Title"]))
    story.append(Spacer(1, 15))

    for k, v in data.items():
        story.append(Paragraph(f"{k}: {v}", styles["Normal"]))
        story.append(Spacer(1, 10))

    doc.build(story)
    return file_path
