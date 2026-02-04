import json
from pathlib import Path

SETTINGS_FILE = "settings.json"

# Προεπιλογές (αν δεν βρει αρχείο ρυθμίσεων)
DEFAULT_SETTINGS = {
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "poppler_path": r"C:\Program Files\poppler-24.02.0\Library\bin"  # Τυπικό path, μπορεί να διαφέρει
}

def load_settings():
    """Φορτώνει τις ρυθμίσεις από το JSON."""
    if not Path(SETTINGS_FILE).exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS

def save_settings(settings_dict):
    """Αποθηκεύει τις ρυθμίσεις στο JSON."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")