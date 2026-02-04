import pdfplumber
import re
import unicodedata
from pathlib import Path
from ocr_utils import ocr_pdf
import json
from config import GROUPS_FILE


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.upper()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text

def load_groups():
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["groups"]


def extract_text_pdf(pdf_path: Path) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:2]:
                t = page.extract_text()
                if t:
                    text += t + " "
    except Exception:
        pass
    return normalize_text(text)

def keyword_match(text: str, keyword: str) -> bool:
    """
    Χαλαρό match:
    - αγνοεί τελείες
    - αγνοεί πολλαπλά κενά
    - keyword ⊂ text
    """
    k = keyword.replace(".", "").strip()
    return k in text

def detect_type(text: str):
    groups = load_groups()
    print("---- OCR TEXT START ----")
    print(text[:1500])
    print("---- OCR TEXT END ----")
    for g in groups:
        for kw in g.get("keywords", []):
            if keyword_match(text, kw):
                return g["type"], g["name"], 0.9


    return "UNKNOWN", "UNCERTAIN", 0.0




def extract_date(text: str):
    match = re.search(r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})', text)
    return match.group(1) if match else None


def extract_number(text: str):
    patterns = [
        r'ΑΡΙΘΜΟΣ\s+(\d+)',
        r'ΑΡΙΘΜΙΟΣ\s+(\d+)',
        r'ΠΑΡΑΣΤΑΤΙΚΟ\s*[:\-]?\s*([A-Z0-9]+)',
        r'ΤΙΜΟΛΟΓΙΟ.*?(\d{3,})'
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def analyze_pdf(pdf_path: Path):
    text = extract_text_pdf(pdf_path)

    doc_type, group_name, conf = detect_type(text)
    date = extract_date(text)
    number = extract_number(text)

    if doc_type == "UNKNOWN" or not date or not number:
        ocr_text = normalize_text(ocr_pdf(pdf_path))

        doc_type2, group_name2, conf2 = detect_type(ocr_text)
        date2 = extract_date(ocr_text)
        number2 = extract_number(ocr_text)

        if doc_type2 != "UNKNOWN":
            doc_type = doc_type2
            group_name = group_name2
            conf = conf2

        date = date or date2
        number = number or number2

    return {
        "type": doc_type,
        "group": group_name,
        "date": date,
        "number": number,
        "confidence": conf
    }

