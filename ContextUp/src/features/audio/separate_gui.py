"""
Audio Separation GUI using Demucs.
Separates audio into stems: vocals, drums, bass, other (+ guitar, piano for 6-stem models).
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
src_dir = current_dir.parent.parent  # features/audio -> src
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from utils.explorer import get_selection_from_explorer
from utils.i18n import t


class AudioSeparateGUI(BaseWindow):
    """Demucs-based audio stem separation GUI."""
    
    def __init__(self, target_path=None, demo=False):
        super().__init__(title="ContextUp Audio Separator (Demucs)", width=650, height=620, icon_name="audio_separate_stems")
        
        self.demo_mode = demo
        self.target_path = target_path
        self.files = []
        self.process = None
        self.is_running = False
        
        if demo:
            self.files = [Path("demo_audio.mp3")]
        elif target_path:
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
        header_text = f"Separating {count} Audio File(s)" if count > 0 else "Audio Stem Separator"
        self.add_header(header_text)
        
        # === Content Area (Scrollable) ===
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=(0, 10))
        
        # File Selection
        if not self.files:
            file_frame = ctk.CTkFrame(self.scroll_frame)
            file_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkButton(file_frame, text=t("audio_separate_gui.select_files"), command=self.select_files).pack(pady=10)
            self.lbl_files = ctk.CTkLabel(file_frame, text=t("audio_separate_gui.no_files_selected"))
            self.lbl_files.pack(pady=5)
        
        # === Model Selection ===
        model_frame = ctk.CTkFrame(self.scroll_frame)
        model_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(model_frame, text=t("audio_separate_gui.model"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.model_var = ctk.StringVar(value="htdemucs")
        models = [
            ("htdemucs", "Best quality (4 stems)"),
            ("htdemucs_ft", "Fine-tuned (4 stems, slower)"),
            ("htdemucs_6s", "6 stems (+ guitar, piano)"),
            ("mdx_extra", "MDX model (faster)"),
        ]
        
        model_grid = ctk.CTkFrame(model_frame, fg_color="transparent")
        model_grid.pack(fill="x", padx=15, pady=5)
        
        for i, (val, desc) in enumerate(models):
            row = i // 2
            col = i % 2
            ctk.CTkRadioButton(model_grid, text=f"{val} - {desc}", variable=self.model_var, 
                               value=val, width=280).grid(row=row, column=col, sticky="w", pady=3, padx=5)
        
        # === Separation Mode ===
        mode_frame = ctk.CTkFrame(self.scroll_frame)
        mode_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(mode_frame, text=t("audio_separate_gui.separation_mode"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.mode_var = ctk.StringVar(value="all")
        mode_row = ctk.CTkFrame(mode_frame, fg_color="transparent")
        mode_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkRadioButton(mode_row, text="All Stems (vocals, drums, bass, other)", 
                           variable=self.mode_var, value="all").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(mode_row, text="Vocals Only (vocals + instrumental)", 
                           variable=self.mode_var, value="vocals").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(mode_row, text="Drums Only (drums + no_drums)", 
                           variable=self.mode_var, value="drums").pack(anchor="w", pady=2)
        
        # === Output Format ===
        output_frame = ctk.CTkFrame(self.scroll_frame)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(output_frame, text=t("audio_separate_gui.output"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        output_row = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_row.pack(fill="x", padx=15, pady=5)
        
        self.format_var = ctk.StringVar(value="wav")
        ctk.CTkLabel(output_row, text=t("audio_separate_gui.format_label")).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(output_row, text="WAV", variable=self.format_var, value="wav", width=80).pack(side="left")
        ctk.CTkRadioButton(output_row, text="FLAC", variable=self.format_var, value="flac", width=80).pack(side="left")
        ctk.CTkRadioButton(output_row, text="MP3", variable=self.format_var, value="mp3", width=80).pack(side="left")
        
        # Quality slider (shifts)
        quality_row = ctk.CTkFrame(output_frame, fg_color="transparent")
        quality_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(quality_row, text="Quality Shifts:").pack(side="left", padx=(0, 10))
        self.shifts_var = ctk.IntVar(value=1)
        self.shifts_slider = ctk.CTkSlider(quality_row, from_=1, to=10, number_of_steps=9, 
                                           variable=self.shifts_var, command=self.update_shifts_label, width=150)
        self.shifts_slider.pack(side="left")
        self.shifts_label = ctk.CTkLabel(quality_row, text="1 (fast)", width=100)
        self.shifts_label.pack(side="left", padx=10)
            
        # Log Area
        ctk.CTkLabel(self.scroll_frame, text="Log:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.log_area = ctk.CTkTextbox(self.scroll_frame, height=100, font=("Consolas", 10))
        self.log_area.pack(fill="x", padx=20, pady=5)
        
        # === Bottom Fixed Area ===
        
        # Progress Bar
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=20, pady=5)
        self.progress.set(0)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=20, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text=t("audio_separate_gui.start_separation"), command=self.start_separation,
                                     font=ctk.CTkFont(weight="bold"), height=40)
        self.btn_run.pack(side="right", padx=5)
        self.btn_close = ctk.CTkButton(btn_frame, text=t("common.close"), fg_color="transparent", 
                                       border_width=1, border_color="gray", command=self.cancel_or_close)
        self.btn_close.pack(side="right", padx=5)
        
        if not self.files:
            self.btn_run.configure(state="disabled")

    def update_shifts_label(self, val):
        val = int(val)
        if val == 1:
            desc = "1 (fast)"
        elif val <= 3:
            desc = f"{val} (balanced)"
        elif val <= 5:
            desc = f"{val} (quality)"
        else:
            desc = f"{val} (best, slow)"
        self.shifts_label.configure(text=desc)

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.m4a *.ogg *.aac *.wma")])
        if files:
            self.files = [Path(f) for f in files]
            self.lbl_files.configure(text=f"{len(self.files)} files selected")
            self.btn_run.configure(state="normal")

    def log(self, msg):
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")

    def cancel_or_close(self):
        if self.is_running and self.process:
            self.process.terminate()
            self.is_running = False
            self.log("❌ Cancelled by user.")
            self.btn_run.configure(state="normal", text="Start Separation")
            self.btn_close.configure(text="Close")
        else:
            self.destroy()

    def start_separation(self):
        if not self.files:
            return
            
        self.is_running = True
        self.btn_run.configure(state="disabled", text="Running...")
        self.btn_close.configure(text="Cancel")
        self.progress.set(0)
        
        model = self.model_var.get()
        mode = self.mode_var.get()
        fmt = self.format_var.get()
        shifts = self.shifts_var.get()
        
        self.log(f"🎵 Model: {model} | Mode: {mode} | Format: {fmt} | Shifts: {shifts}")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        try:
            python_exe = sys.executable
            total = len(self.files)
            success_count = 0
            
            for i, path in enumerate(self.files):
                if not self.is_running:
                    break
                    
                self.after(0, lambda i=i, p=path: self.log(f"\n[{i+1}/{total}] Processing: {p.name}"))
                self.after(0, lambda i=i: self.progress.set(i / total))
                
                output_dir = path.parent / "Separated_Audio"
                
                # Build command
                cmd = [
                    python_exe, "-m", "demucs",
                    "-n", self.model_var.get(),
                    "-o", str(output_dir),
                    "--shifts", str(self.shifts_var.get()),
                ]
                
                # Two-stems mode
                if self.mode_var.get() != "all":
                    cmd.extend(["--two-stems", self.mode_var.get()])
                
                # Output format
                fmt = self.format_var.get()
                if fmt == "mp3":
                    cmd.append("--mp3")
                elif fmt == "flac":
                    cmd.append("--flac")
                
                cmd.append(str(path))
                
                try:
                    self.process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                        text=True, bufsize=1
                    )
                    
                    while True:
                        line = self.process.stdout.readline()
                        if not line and self.process.poll() is not None:
                            break
                        if line.strip():
                            self.after(0, lambda l=line: self.log(f"  {l.strip()}"))
                            
                    if self.process.returncode == 0:
                        success_count += 1
                        self.after(0, lambda: self.log("  ✅ Done"))
                    else:
                        self.after(0, lambda: self.log("  ❌ Failed"))
                        
                except Exception as e:
                    self.after(0, lambda e=e: self.log(f"  ❌ Error: {e}"))
            
            self.after(0, lambda: self.progress.set(1))
            
            if self.is_running:
                self.after(0, lambda: self.log(f"\n🎉 Completed: {success_count}/{total} files."))
                if success_count > 0:
                    self.after(0, lambda: messagebox.showinfo("Success", 
                        f"Separation complete!\n\nOutput: {self.files[0].parent / 'Separated_Audio'}"))
            
        except Exception as e:
            self.after(0, lambda e=e: self.log(f"❌ Critical Error: {e}"))
            
        self.is_running = False
        self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Separation"))
        self.after(0, lambda: self.btn_close.configure(text="Close"))

    def on_closing(self):
        if self.is_running and self.process:
            self.process.terminate()
        self.destroy()


def separate_audio(target_path: str = None):
    """Open Audio Separator GUI."""
    try:
        app = AudioSeparateGUI(target_path)
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")


if __name__ == "__main__":
    # Demo mode for screenshots
    if "--demo" in sys.argv:
        app = AudioSeparateGUI(None, demo=True)
        app.mainloop()
    elif len(sys.argv) > 1:
        separate_audio(sys.argv[1])
    else:
        separate_audio()
