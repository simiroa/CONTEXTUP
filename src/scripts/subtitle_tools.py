"""
Subtitle Generation GUI Tools.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import threading
import subprocess
import sys
import os

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow

class SubtitleGUI(BaseWindow):
    def __init__(self, target_path=None):
        super().__init__(title="ContextUp Subtitle", width=700, height=520)
        
        self.files = []
        if target_path:
            self.files.append(Path(target_path))
            
        self.log_visible = False
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Check for cached models
        threading.Thread(target=self.check_cached_models, daemon=True).start()
        
    def check_cached_models(self):
        try:
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            if not cache_dir.exists(): return
            
            cached = []
            for d in cache_dir.iterdir():
                if d.name.startswith("models--Systran--faster-whisper-"):
                    size = d.name.split("-")[-1]
                    cached.append(size)
            
            self.after(0, lambda: self.update_model_list(cached))
        except Exception:
            pass

    def update_model_list(self, cached_models):
        current = self.model_var.get()
        new_values = []
        base_models = ['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3']
        
        for m in base_models:
            if m in cached_models:
                new_values.append(f"{m} *")
            else:
                new_values.append(m)
                
        self.model_combo.configure(values=new_values)
        if current in base_models and current in cached_models:
            self.model_var.set(f"{current} *")

    def create_widgets(self):
        self.main_frame.grid_rowconfigure(0, weight=1) # Files
        self.main_frame.grid_rowconfigure(1, weight=0) # Settings
        self.main_frame.grid_rowconfigure(2, weight=0) # Progress
        self.main_frame.grid_rowconfigure(3, weight=0) # Logs
        self.main_frame.grid_rowconfigure(4, weight=0) # Actions
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- 1. File List (Top) ---
        file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        file_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 5))
        
        header_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header_frame, text="Input Files", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="Clear", width=60, height=24, fg_color="#C0392B", hover_color="#E74C3C", command=self.clear_files).pack(side="right")
        ctk.CTkButton(header_frame, text="+ Add", width=60, height=24, command=self.add_files).pack(side="right", padx=5)

        self.file_listbox = ctk.CTkTextbox(file_frame, font=("Consolas", 12), height=120)
        self.file_listbox.pack(fill="both", expand=True)
        self.update_file_list()

        # --- 2. Settings Area (Middle) ---
        settings_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        settings_container.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        settings_container.grid_columnconfigure(0, weight=1)
        settings_container.grid_columnconfigure(1, weight=1)

        # Left: AI Processing
        ai_frame = ctk.CTkFrame(settings_container)
        ai_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        ctk.CTkLabel(ai_frame, text="AI Processing", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.create_compact_setting(ai_frame, "Model", ['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3'], "small", "model")
        self.create_compact_setting(ai_frame, "Task", ["transcribe", "translate"], "transcribe", "task")
        self.create_compact_setting(ai_frame, "Device", ["cuda", "cpu"], "cuda", "device")
        self.create_compact_setting(ai_frame, "Language", ["Auto", "en", "ko", "ja", "zh", "es", "fr", "de", "ru", "it"], "Auto", "lang")
        
        # Right: Output Deliverables
        out_frame = ctk.CTkFrame(settings_container)
        out_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        
        ctk.CTkLabel(out_frame, text="Output Deliverables", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Folder
        ctk.CTkLabel(out_frame, text="Output Folder", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=10, pady=(5, 0))
        folder_row = ctk.CTkFrame(out_frame, fg_color="transparent")
        folder_row.pack(fill="x", padx=10, pady=(0, 10))
        
        self.out_dir_var = ctk.StringVar(value="")
        ctk.CTkEntry(folder_row, textvariable=self.out_dir_var, placeholder_text="Default: Source folder", height=28).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(folder_row, text="...", width=30, height=28, command=self.browse_output_dir).pack(side="right")
        
        # Formats (Checkboxes)
        ctk.CTkLabel(out_frame, text="Generate Formats", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=10, pady=(0, 5))
        fmt_row = ctk.CTkFrame(out_frame, fg_color="transparent")
        fmt_row.pack(fill="x", padx=10, pady=(0, 10))
        
        self.fmt_srt = ctk.BooleanVar(value=True)
        self.fmt_vtt = ctk.BooleanVar(value=False)
        self.fmt_txt = ctk.BooleanVar(value=False)
        self.fmt_json = ctk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(fmt_row, text="SRT", variable=self.fmt_srt, width=60).pack(side="left")
        ctk.CTkCheckBox(fmt_row, text="VTT", variable=self.fmt_vtt, width=60).pack(side="left")
        ctk.CTkCheckBox(fmt_row, text="TXT", variable=self.fmt_txt, width=60).pack(side="left")
        ctk.CTkCheckBox(fmt_row, text="JSON", variable=self.fmt_json, width=60).pack(side="left")

        # --- 3. Progress & Status ---
        status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        status_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 0))
        
        status_line = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_line.pack(fill="x")
        self.status_label = ctk.CTkLabel(status_line, text="Ready", anchor="w", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left", fill="x", expand=True)
        self.btn_toggle_log = ctk.CTkButton(status_line, text="Show Log ▼", width=80, height=24, fg_color="transparent", border_width=1, border_color="gray", text_color="gray", command=self.toggle_log)
        self.btn_toggle_log.pack(side="right")
        
        self.progress_bar = ctk.CTkProgressBar(status_frame, height=10)
        self.progress_bar.pack(fill="x", pady=(5, 5))
        self.progress_bar.set(0)

        # --- 4. Log Area ---
        self.log_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.log_area = ctk.CTkTextbox(self.log_frame, font=("Consolas", 10), height=120)
        self.log_area.pack(fill="both", expand=True)

        # --- 5. Actions ---
        action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        action_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=(10, 20))
        
        self.btn_run = ctk.CTkButton(action_frame, text="Generate Subtitles", command=self.start_generation,
                                   height=40, font=("", 14, "bold"), fg_color=("#27AE60", "#2ECC71"), hover_color=("#2ECC71", "#27AE60"))
        self.btn_run.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(action_frame, text="Close", width=80, height=40, fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right")

    def create_compact_setting(self, parent, label, values, default, var_name):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text=label, width=70, anchor="w", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")
        var = ctk.StringVar(value=default)
        setattr(self, f"{var_name}_var", var)
        combo = ctk.CTkComboBox(frame, variable=var, values=values, height=24, font=("", 12))
        combo.pack(side="left", fill="x", expand=True)
        setattr(self, f"{var_name}_combo", combo)

    def browse_output_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.out_dir_var.set(path)

    def toggle_log(self):
        if self.log_visible:
            self.log_frame.grid_forget()
            self.btn_toggle_log.configure(text="Show Log ▼")
            self.geometry("700x520")
            self.log_visible = False
        else:
            self.log_frame.grid(row=3, column=0, sticky="nsew", padx=15, pady=5)
            self.btn_toggle_log.configure(text="Hide Log ▲")
            self.geometry("700x650")
            self.log_visible = True

    def update_file_list(self):
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", "end")
        if not self.files:
            self.file_listbox.insert("end", "\n  No files selected.")
        else:
            for i, p in enumerate(self.files, 1):
                self.file_listbox.insert("end", f"{i}. {p.name}\n")
        self.file_listbox.configure(state="disabled")

    def add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("Video/Audio", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.flac"), ("All Files", "*.*")])
        if paths:
            for p in paths:
                path_obj = Path(p)
                if path_obj not in self.files:
                    self.files.append(path_obj)
            self.update_file_list()
            
    def clear_files(self):
        self.files = []
        self.update_file_list()

    def start_generation(self):
        if not self.files:
            messagebox.showwarning("No Files", "Please add files.")
            return
            
        # Check formats
        formats = []
        if self.fmt_srt.get(): formats.append("srt")
        if self.fmt_vtt.get(): formats.append("vtt")
        if self.fmt_txt.get(): formats.append("txt")
        if self.fmt_json.get(): formats.append("json")
        
        if not formats:
            messagebox.showwarning("No Format", "Please select at least one output format.")
            return
            
        self.btn_run.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)
        self.status_label.configure(text="Initializing...")
        self.log_area.delete("1.0", "end")
        
        threading.Thread(target=self.run_batch, args=(formats,), daemon=True).start()
        
    def run_batch(self, formats):
        script_path = src_dir / "scripts" / "ai_standalone" / "subtitle_gen.py"
        total = len(self.files)
        
        model = self.model_var.get().split(" ")[0]
        task = self.task_var.get()
        device = self.device_var.get()
        lang = self.lang_var.get()
        out_dir = self.out_dir_var.get().strip()
        
        fmt_str = ",".join(formats)
        
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        for i, file_path in enumerate(self.files, 1):
            self.update_status(f"Processing {i}/{total}: {file_path.name}...", (i-1)/total)
            self.update_log(f"--- Processing {i}/{total}: {file_path.name} ---\n")
            
            cmd = [sys.executable, str(script_path), str(file_path)]
            cmd.extend(["--model", model, "--task", task, "--device", device, "--format", fmt_str])
            if lang != "Auto": cmd.extend(["--lang", lang])
            if out_dir: cmd.extend(["--output_dir", out_dir])
            
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=0x08000000, env=env)
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None: break
                    if line: self.update_log(line)
                        
                if process.returncode != 0:
                    self.update_log(f"Error: {file_path.name}\n")
            except Exception as e:
                self.update_log(f"Exception: {e}\n")
            
            self.update_status(f"Finished {i}/{total}", i/total)
            
        self.after(0, self.finish_batch)
        
    def update_status(self, text, progress):
        self.after(0, lambda: self.status_label.configure(text=text))
        self.after(0, lambda: self.progress_bar.set(progress))
        
    def update_log(self, text):
        self.after(0, lambda: self.log_area.insert("end", text))
        self.after(0, lambda: self.log_area.see("end"))
        
    def finish_batch(self):
        self.btn_run.configure(state="normal", text="Generate Subtitles")
        self.status_label.configure(text="Batch processing complete.")
        self.progress_bar.set(1)
        messagebox.showinfo("Complete", "Processing finished.")

    def on_closing(self):
        self.destroy()

def generate_subtitles(target_path: str):
    """
    Open Subtitle Generation dialog.
    """
    app = SubtitleGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_subtitles(sys.argv[1])
    else:
        generate_subtitles(None)
