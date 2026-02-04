from pathlib import Path
from datetime import datetime
import shutil
import re
from pdf_parser import analyze_pdf
from config import CONFIDENCE_THRESHOLD

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def parse_date(d: str):
    """
    Προσπαθεί να βρει ημερομηνία με Regex και καθαρισμό OCR λαθών.
    """
    if not d: return None
    
    # Καθαρισμός θορύβου
    d = d.strip().replace(".", "/").replace("-", "/")
    # Διόρθωση συχνών OCR λαθών (το γράμμα O γίνεται 0)
    d = d.replace("O", "0").replace("o", "0")

    # Regex για εντοπισμό μοτίβου ΗΗ/ΜΜ/ΕΕΕΕ μέσα σε κείμενο
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", d)
    if match:
        d = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

    for fmt in ("%d/%m/%Y", "%Y/%m/%d", "%d/%m/%y"):
        try:
            return datetime.strptime(d, fmt)
        except ValueError:
            pass
    return None

def unique_name(target_dir: Path, filename: str) -> str:
    path = target_dir / filename
    if not path.exists():
        return filename

    stem = path.stem
    suffix = path.suffix
    i = 1
    while True:
        new_name = f"{stem}_{i}{suffix}"
        if not (target_dir / new_name).exists():
            return new_name
        i += 1

def organize(input_dir: Path, output_dir: Path, progress_cb=None, log_cb=None, dry_run=False):
    def log(msg: str):
        if log_cb: log_cb(msg)
        else: print(msg)

    files = [f for f in input_dir.iterdir() if f.is_file()]
    
    if dry_run:
        log("🔍 --- ΛΕΙΤΟΥΡΓΙΑ ΠΡΟΣΟΜΟΙΩΣΗΣ (DRY RUN) ---")
        log("   Κανένα αρχείο δεν θα μετακινηθεί πραγματικά.")

    for file in files:
        try:
            ext = file.suffix.lower()
            
            # Ανάλυση PDF
            if ext == ".pdf":
                analysis = analyze_pdf(file) or {}
                
                conf = analysis.get("confidence", 0)
                date_str = analysis.get("date")
                
                # Κριτήρια για επιτυχή ταυτοποίηση
                if (analysis.get("type") != "UNKNOWN" and date_str and conf >= CONFIDENCE_THRESHOLD):
                    dt = parse_date(date_str)

                    if not dt:
                        category = "UNCERTAIN_DATE"
                        year = datetime.now().strftime("%Y")
                        month = "Unknown"
                    else:
                        year = dt.strftime("%Y")
                        month = dt.strftime("%m")
                        category = analysis.get("group") or "General"
                    
                    # Καθαρισμός αριθμού παραστατικού από σύμβολα
                    number = analysis.get("number") or "NO_NUM"
                    number = re.sub(r'[\\/*?:"<>|]', "", str(number))

                    new_name = f"{year}-{month}_{analysis['type']}_{number}.pdf"
                    target_dir = output_dir / category / year / month
                else:
                    category = "Unsorted"
                    target_dir = output_dir / category
                    new_name = f"CHECK_{file.name}"

            else:
                # Μη PDF αρχεία
                category = "Λοιπά"
                target_dir = output_dir / category
                new_name = file.name

            # Υπολογισμός τελικού ονόματος (Unique)
            final_name = unique_name(target_dir, new_name)

            # --- ΕΚΤΕΛΕΣΗ Ή ΠΡΟΣΟΜΟΙΩΣΗ ---
            if dry_run:
                # Δείχνουμε τι ΘΑ γινόταν
                log(f"🔍 [TEST] {file.name} -> {category}/{year}/{month}/{final_name}" if 'year' in locals() else f"🔍 [TEST] {file.name} -> {category}/{final_name}")
            else:
                # Πραγματική μετακίνηση
                ensure_dir(target_dir)
                shutil.move(str(file), target_dir / final_name)
                log(f"✔ {category}: {final_name}")

        except Exception as e:
            log(f"❌ ERROR {file.name}: {e}")

        if progress_cb: progress_cb()

    log("✅ Διαδικασία ολοκληρώθηκε.")