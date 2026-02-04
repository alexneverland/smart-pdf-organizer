import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import json

from organizer import organize
from config import GROUPS_FILE
from settings_manager import load_settings, save_settings

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lazaros Organizer Pro v2")
        self.geometry("950x700")

        # Variables
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=True) # Default ασφαλές
        
        self.tess_path = tk.StringVar()
        self.poppler_path = tk.StringVar()

        self.groups = []
        self.selected_index = None

        self.load_app_settings()
        self.build_ui()

    def load_app_settings(self):
        s = load_settings()
        self.tess_path.set(s.get("tesseract_cmd", ""))
        self.poppler_path.set(s.get("poppler_path", ""))

    def build_ui(self):
        # Στυλ
        style = ttk.Style()
        style.configure("Bold.TButton", font=("Segoe UI", 10, "bold"))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # TAB 1: RUN
        tab_run = ttk.Frame(notebook)
        notebook.add(tab_run, text="📂 Οργάνωση")
        self.build_run_tab(tab_run)

        # TAB 2: GROUPS
        tab_groups = ttk.Frame(notebook)
        notebook.add(tab_groups, text="🧩 Κανόνες")
        self.build_groups_tab(tab_groups)

        # TAB 3: SETTINGS
        tab_settings = ttk.Frame(notebook)
        notebook.add(tab_settings, text="⚙ Ρυθμίσεις")
        self.build_settings_tab(tab_settings)

    # --- TAB 1: RUN ---
    def build_run_tab(self, parent):
        frm = ttk.LabelFrame(parent, text="Εκτέλεση", padding=15)
        frm.pack(fill="x", padx=10, pady=10)

        # Input
        ttk.Label(frm, text="1. Ακατάστατος Φάκελος:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.input_dir, width=65).grid(row=0, column=1, padx=5)
        ttk.Button(frm, text="...", command=lambda: self.sel_dir(self.input_dir)).grid(row=0, column=2)

        # Output
        ttk.Label(frm, text="2. Φάκελος Ταξινόμησης:").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(frm, textvariable=self.output_dir, width=65).grid(row=1, column=1, padx=5)
        ttk.Button(frm, text="...", command=lambda: self.sel_dir(self.output_dir)).grid(row=1, column=2)

        # Checkbox Dry Run
        cb = ttk.Checkbutton(frm, text="Λειτουργία Προσομοίωσης (Dry Run) - Δεν μετακινεί αρχεία", variable=self.dry_run_var)
        cb.grid(row=2, column=1, sticky="w", pady=10)

        # Start Button
        btn = ttk.Button(parent, text="▶ ΕΚΚΙΝΗΣΗ", style="Bold.TButton", command=self.run_organizer)
        btn.pack(pady=5, ipadx=20, ipady=5)

        # Progress & Log
        self.progress = ttk.Progressbar(parent, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        lbl = ttk.Label(parent, text="Καταγραφή Ενεργειών (Log):")
        lbl.pack(anchor="w", padx=10)
        
        self.log_box = tk.Text(parent, height=15, bg="#f8f9fa", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def sel_dir(self, var):
        d = filedialog.askdirectory()
        if d: var.set(d)

    def run_organizer(self):
        inp = self.input_dir.get()
        out = self.output_dir.get()

        if not inp or not out:
            messagebox.showerror("Σφάλμα", "Επέλεξε φακέλους εισαγωγής και εξαγωγής!")
            return

        self.log_box.delete("1.0", tk.END)
        self.log_box.insert(tk.END, "Προετοιμασία...\n")
        
        # Υπολογισμός πλήθους αρχείων για την μπάρα
        try:
            files = list(Path(inp).glob("*.*"))
            total = len(files)
        except:
            total = 0
            
        self.progress["maximum"] = total
        self.progress["value"] = 0

        def log_gui(msg):
            self.log_box.insert(tk.END, msg + "\n")
            self.log_box.see(tk.END)

        def step_gui():
            self.progress["value"] += 1

        def worker():
            try:
                organize(
                    Path(inp), 
                    Path(out), 
                    progress_cb=step_gui, 
                    log_cb=log_gui, 
                    dry_run=self.dry_run_var.get()
                )
            except Exception as e:
                log_gui(f"CRITICAL ERROR: {e}")

        threading.Thread(target=worker, daemon=True).start()

    # --- TAB 2: GROUPS (Logic maintained) ---
    def build_groups_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        left = ttk.Frame(paned)
        right = ttk.LabelFrame(paned, text="Επεξεργασία Κανόνα")
        paned.add(left, weight=1)
        paned.add(right, weight=3)

        self.listbox = tk.Listbox(left, width=20)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_group_select)

        btns = ttk.Frame(left)
        btns.pack(fill="x")
        ttk.Button(btns, text="+", command=self.add_group, width=5).pack(side="left")
        ttk.Button(btns, text="-", command=self.del_group, width=5).pack(side="right")

        # Fields
        ttk.Label(right, text="Όνομα Φακέλου:").pack(anchor="w", padx=5)
        self.grp_name = ttk.Entry(right)
        self.grp_name.pack(fill="x", padx=5)

        ttk.Label(right, text="Prefix Αρχείου (π.χ. TIMOL):").pack(anchor="w", padx=5)
        self.grp_type = ttk.Entry(right)
        self.grp_type.pack(fill="x", padx=5)

        ttk.Label(right, text="Λέξεις Κλειδιά (μία ανά σειρά):").pack(anchor="w", padx=5)
        self.grp_kw = tk.Text(right, height=10)
        self.grp_kw.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(right, text="💾 Αποθήκευση JSON", command=self.save_groups_json).pack(pady=5)
        
        self.load_groups_json()

    def load_groups_json(self):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                self.groups = json.load(f)["groups"]
        except:
            self.groups = []
        self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for g in self.groups:
            self.listbox.insert(tk.END, g["name"])

    def on_group_select(self, e):
        if not self.listbox.curselection(): return
        idx = self.listbox.curselection()[0]
        self.selected_index = idx
        g = self.groups[idx]

        self.grp_name.delete(0, tk.END); self.grp_name.insert(0, g["name"])
        self.grp_type.delete(0, tk.END); self.grp_type.insert(0, g["type"])
        self.grp_kw.delete("1.0", tk.END)
        self.grp_kw.insert(tk.END, "\n".join(g["keywords"]))

    def add_group(self):
        self.groups.append({"name": "New Group", "type": "DOC", "keywords": []})
        self.refresh_listbox()

    def del_group(self):
        if self.selected_index is not None:
            self.groups.pop(self.selected_index)
            self.selected_index = None
            self.refresh_listbox()

    def save_groups_json(self):
        if self.selected_index is not None:
            kws = [x.strip() for x in self.grp_kw.get("1.0", tk.END).splitlines() if x.strip()]
            self.groups[self.selected_index] = {
                "name": self.grp_name.get(),
                "type": self.grp_type.get(),
                "keywords": kws
            }
        
        try:
            with open(GROUPS_FILE, "w", encoding="utf-8") as f:
                json.dump({"groups": self.groups}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("OK", "Οι κανόνες αποθηκεύτηκαν!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- TAB 3: SETTINGS ---
    def build_settings_tab(self, parent):
        frm = ttk.LabelFrame(parent, text="Διαδρομές Εργαλείων (Paths)", padding=15)
        frm.pack(fill="x", padx=20, pady=20)

        # Tesseract
        ttk.Label(frm, text="Tesseract (tesseract.exe):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.tess_path, width=70).grid(row=0, column=1, padx=5)
        ttk.Button(frm, text="📂", command=lambda: self.find_file(self.tess_path)).grid(row=0, column=2)

        # Poppler
        ttk.Label(frm, text="Poppler (φάκελος bin):").grid(row=1, column=0, sticky="w", pady=15)
        ttk.Entry(frm, textvariable=self.poppler_path, width=70).grid(row=1, column=1, padx=5)
        ttk.Button(frm, text="📂", command=lambda: self.find_folder(self.poppler_path)).grid(row=1, column=2)

        ttk.Button(frm, text="💾 Αποθήκευση Ρυθμίσεων", command=self.save_gui_settings).grid(row=2, column=1, pady=20)

    def find_file(self, var):
        f = filedialog.askopenfilename(filetypes=[("EXE", "*.exe")])
        if f: var.set(f)

    def find_folder(self, var):
        d = filedialog.askdirectory()
        if d: var.set(d)

    def save_gui_settings(self):
        data = {
            "tesseract_cmd": self.tess_path.get(),
            "poppler_path": self.poppler_path.get()
        }
        save_settings(data)
        messagebox.showinfo("Επιτυχία", "Οι ρυθμίσεις αποθηκεύτηκαν!\nΕπανεκκίνησε το πρόγραμμα αν χρειαστεί.")

if __name__ == "__main__":
    app = App()
    app.mainloop()