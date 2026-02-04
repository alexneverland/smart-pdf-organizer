import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
import os
from settings_manager import load_settings

def ocr_pdf(pdf_path: Path) -> str:
    """
    Μετατρέπει τις 2 πρώτες σελίδες του PDF σε εικόνες και κάνει OCR.
    Διαβάζει τα paths δυναμικά κάθε φορά που τρέχει.
    """
    settings = load_settings()
    tess_cmd = settings.get("tesseract_cmd", "")
    poppler_path = settings.get("poppler_path", "")

    # Ρύθμιση Tesseract
    if os.path.exists(tess_cmd):
        pytesseract.pytesseract.tesseract_cmd = tess_cmd
    else:
        return "ERROR_TESSERACT_NOT_FOUND"

    # Ρύθμιση Poppler
    if not poppler_path or not Path(poppler_path).exists():
        return "ERROR_POPPLER_NOT_FOUND"

    text = ""
    try:
        # Μετατροπή PDF σε εικόνες (μόνο οι 2 πρώτες για ταχύτητα)
        images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)

        for img in images[:2]:
            # Γλώσσες: Ελληνικά + Αγγλικά
            text += pytesseract.image_to_string(img, lang="ell+eng")
            
    except Exception as e:
        print(f"OCR Error στο {pdf_path.name}: {e}")
        return ""

    return text.upper()