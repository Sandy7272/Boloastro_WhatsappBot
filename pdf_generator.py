# pdf_generator.py
# ----------------
# Premium PDF generator for Ultimate VIP Kundali
# Unicode-safe (English / Hindi / Marathi)
# AstroSage-style spacing & hierarchy

from fpdf import FPDF
import os
import time
import logging

# ---------------- CONFIG ----------------

# Get absolute path to prevent "File Not Found" errors
# Ye ensure karega ki file hamesha script ke folder me hi bane
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")

# Safe Font Paths
FONT_REGULAR = os.path.join(FONT_DIR, "NotoSans-Regular.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "NotoSans-Bold.ttf")

PAGE_MARGIN = 18
LINE_HEIGHT = 8

logger = logging.getLogger(__name__)

# ---------------- PDF CLASS ----------------

class PremiumPDF(FPDF):
    def header(self):
        # Header ke liye default font use karein agar Noto na ho
        try:
            self.set_font("NotoB", size=10)
        except:
            self.set_font("Arial", "B", 10)
            
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "Ultimate VIP Kundali Report", align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        try:
            self.set_font("Noto", size=9)
        except:
            self.set_font("Arial", "I", 8)
            
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# ---------------- MAIN FUNCTION ----------------

def generate_pdf(user, language, sections, values):
    """
    sections = dict of section_name -> formatted text
    values   = computed values (for cover page)
    """
    
    pdf = PremiumPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- 1. SAFE FONT LOADING ---
    # Agar font file na mile to crash na ho, standard font use kare
    try:
        pdf.add_font("Noto", "", FONT_REGULAR, uni=True)
        pdf.add_font("NotoB", "", FONT_BOLD, uni=True)
        has_custom_font = True
    except Exception as e:
        logger.warning(f"⚠️ Custom Font missing, using Arial. Error: {e}")
        has_custom_font = False

    # ---------------- COVER PAGE ----------------

    pdf.add_page()
    
    if has_custom_font:
        pdf.set_font("NotoB", size=20)
    else:
        pdf.set_font("Arial", "B", 20)
        
    pdf.set_text_color(20, 20, 20)

    pdf.ln(30)
    pdf.multi_cell(0, 12, "Complete Life Prediction Report", align="C")
    pdf.ln(6)

    if has_custom_font:
        pdf.set_font("Noto", size=13)
    else:
        pdf.set_font("Arial", "", 12)
        
    pdf.multi_cell(
        0,
        9,
        "Marriage • Career • Wealth • Property • Health • Dasha • Dosha",
        align="C"
    )

    pdf.ln(25)
    if has_custom_font:
        pdf.set_font("Noto", size=12)
    else:
        pdf.set_font("Arial", "", 12)

    # --- HANDLE KEYS SAFELY (Time vs TOB, Place vs PLACE) ---
    dob_val = values.get("DOB", values.get("Date", "—"))
    tob_val = values.get("Time", values.get("TOB", "—"))
    place_val = values.get("Place", values.get("PLACE", "—"))
    
    cover_data = [
        ("Name/ID", str(user)),
        ("Date of Birth", dob_val),
        ("Time of Birth", tob_val),
        ("Place of Birth", place_val),
        ("Ascendant", values.get("LAGNA", "—")),
        ("Moon Sign", values.get("RASHI", "—")),
        ("Nakshatra", values.get("NAKSHATRA", "—")),
        ("Confidence Score", f"{values.get('CONFIDENCE_SCORE', '—')} %"),
    ]

    for k, v in cover_data:
        pdf.cell(55, 8, f"{k}:", ln=0)
        # Ensure value is string
        pdf.multi_cell(0, 8, str(v))

    # ---------------- CONTENT SECTIONS ----------------

    for key, text in sections.items():
        pdf.add_page()

        if has_custom_font:
            pdf.set_font("NotoB", size=15)
        else:
            pdf.set_font("Arial", "B", 15)
            
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 10, key.replace("_", " ").upper())

        pdf.ln(4)
        if has_custom_font:
            pdf.set_font("Noto", size=11)
        else:
            pdf.set_font("Arial", "", 11)
            
        pdf.set_text_color(50, 50, 50)

        # Clean HTML-like tags (Basic cleaning)
        clean_text = (
            str(text)
            .replace("<b>", "")
            .replace("</b>", "")
            .replace("<br>", "\n")
        )

        pdf.multi_cell(0, LINE_HEIGHT, clean_text)

    # ---------------- SAVE FILE (ABSOLUTE PATH FIX) ----------------

    # Folder ka pakka pata (Absolute Path)
    output_folder = os.path.join(BASE_DIR, "generated_pdfs")
    os.makedirs(output_folder, exist_ok=True)
    
    # Filename generation
    filename = f"VIP_Kundali_{int(time.time())}.pdf"
    
    # Full Path join karein
    full_path = os.path.join(output_folder, filename)

    pdf.output(full_path)
    logger.info(f"✅ PDF Saved locally at: {full_path}")
    
    return full_path