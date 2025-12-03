"""
Audio Separation GUI using Spleeter.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import threading
import subprocess
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from utils.explorer import get_selection_from_explorer

class AudioSeparateGUI(BaseWindow):
    def __init__(self, target_path=None):
        super().__init__(title="ContextUp Audio Separator (Spleeter)", width=600, height=550)
        
        self.target_path = target_path
        self.files = []
        
        if target_path:
            selection = get_selection_from_explorer(target_path)
            if not selection:
                selection = [target_path]
            
            audio_exts = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma'}
            self.files = [Path(p) for p in selection if Path(p).suffix.lower() in audio_exts]
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Header
        count = len(self.files)
        header_text = f"Separating {count} Audio Files" if count > 0 else "Audio Separator"
        self.add_header(header_text)
        
        # File Selection (if none selected initially)
        if not self.files:
            file_frame = ctk.CTkFrame(self.main_frame)
            file_frame.pack(fill="x", padx=20, pady=10)
            ctk.CTkButton(file_frame, text="Select Audio Files", command=self.select_files).pack(pady=10)
            self.lbl_files = ctk.CTkLabel(file_frame, text="No files selected")
            self.lbl_files.pack(pady=5)
        
        # Options
        opt_frame = ctk.CTkFrame(self.main_frame)
        opt_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(opt_frame, text="Stems:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=20)
        self.stems_var = ctk.StringVar(value="2stems")
        
        stems_opts = [
            ("2 Stems (Vocals + Accompaniment)", "2stems"),
            ("4 Stems (Vocals, Drums, Bass, Other)", "4stems"),
            ("5 Stems (Vocals, Drums, Bass, Piano, Other)", "5stems")
        ]
        
        for text, val in stems_opts:
            ctk.CTkRadioButton(opt_frame, text=text, variable=self.stems_var, value=val).pack(anchor="w", padx=20, pady=5)
            
        # Log Area
        ctk.CTkLabel(self.main_frame, text="Log:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.log_area = ctk.CTkTextbox(self.main_frame, height=150, font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Start Separation", command=self.start_separation)
        self.btn_run.pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Close", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)
        
        if not self.files:
            self.btn_run.configure(state="disabled")

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.m4a *.ogg *.aac *.wma")])
        if files:
            self.files = [Path(f) for f in files]
            self.lbl_files.configure(text=f"{len(self.files)} files selected")
            self.btn_run.configure(state="normal")

    def log(self, msg):
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")

    def start_separation(self):
        if not self.files:
            return
            
        self.btn_run.configure(state="disabled", text="Running...")
        self.log(f"Starting separation with {self.stems_var.get()} model...")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        try:
            # Check if spleeter is installed
            try:
                subprocess.run(["spleeter", "--version"], check=True, capture_output=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                self.after(0, lambda: self.log("Error: 'spleeter' command not found.\nPlease install it: pip install spleeter"))
                self.after(0, lambda: messagebox.showerror("Error", "Spleeter not found.\nPlease install it using: pip install spleeter"))
                self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Separation"))
                return

            total = len(self.files)
            success_count = 0
            
            for i, path in enumerate(self.files):
                self.after(0, lambda i=i, p=path: self.log(f"[{i+1}/{total}] Processing: {p.name}"))
                
                output_dir = path.parent / "Separated_Audio"
                output_dir.mkdir(exist_ok=True)
                
                cmd = ["spleeter", "separate", "-p", f"spleeter:{self.stems_var.get()}", "-o", str(output_dir), str(path)]
                
                try:
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            self.after(0, lambda l=line: self.log(f"  > {l.strip()}"))
                            
                    if process.returncode == 0:
                        success_count += 1
                        self.after(0, lambda: self.log("  Done."))
                    else:
                        err = process.stderr.read()
                        self.after(0, lambda e=err: self.log(f"  Failed: {e}"))
                        
                except Exception as e:
                    self.after(0, lambda e=e: self.log(f"  Error: {e}"))
            
            self.after(0, lambda: self.log(f"\nCompleted: {success_count}/{total} files."))
            self.after(0, lambda: messagebox.showinfo("Success", f"Separation complete.\nOutput folder: Separated_Audio"))
            
        except Exception as e:
            self.after(0, lambda e=e: self.log(f"Critical Error: {e}"))
            
        self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Separation"))

    def on_closing(self):
        self.destroy()

def separate_audio(target_path: str = None):
    """Open Audio Separator GUI."""
    try:
        app = AudioSeparateGUI(target_path)
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        separate_audio(sys.argv[1])
    else:
        separate_audio()
