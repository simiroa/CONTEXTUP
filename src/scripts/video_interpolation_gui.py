"""
Video Frame Interpolation GUI
Unified interface for FFmpeg (CPU) and RIFE (AI) interpolation.
"""
import os
import sys
import threading
import time
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path

# Add src to path
try:
    current_dir = Path(__file__).parent
    src_dir = current_dir.parent
    sys.path.append(str(src_dir))
except: pass

from utils.gui_lib import BaseWindow
from utils.ai_runner import run_ai_script
from core.logger import setup_logger

logger = setup_logger("video_interp_gui")

class VideoInterpApp(BaseWindow):
    def __init__(self):
        super().__init__(title="Video Frame Interpolation", width=600, height=500)
        
        # State
        self.input_path = None
        self.is_processing = False
        self.process = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # --- Input Section ---
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Input Video:").pack(anchor="w", padx=10, pady=(5,0))
        
        file_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        file_row.pack(fill="x", padx=5, pady=5)
        
        self.entry_input = ctk.CTkEntry(file_row, placeholder_text="Select video file...")
        self.entry_input.pack(side="left", fill="x", expand=True, padx=(5,5))
        
        ctk.CTkButton(file_row, text="Browse", width=80, command=self.browse_input).pack(side="right", padx=5)

        # --- Method Selection ---
        method_frame = ctk.CTkFrame(self.main_frame)
        method_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(method_frame, text="Interpolation Method:").pack(anchor="w", padx=10, pady=(5,0))
        
        self.method_var = ctk.StringVar(value="ffmpeg")
        
        # FFmpeg Option
        rb_ffmpeg = ctk.CTkRadioButton(method_frame, text="FFmpeg (CPU / Standard)", 
                                     variable=self.method_var, value="ffmpeg",
                                     command=self.update_options)
        rb_ffmpeg.pack(anchor="w", padx=20, pady=5)
        
        # AI Option
        rb_ai = ctk.CTkRadioButton(method_frame, text="AI (RIFE / GPU Recommended)", 
                                 variable=self.method_var, value="ai",
                                 command=self.update_options)
        rb_ai.pack(anchor="w", padx=20, pady=5)

        # --- Options Section ---
        self.opts_frame = ctk.CTkFrame(self.main_frame)
        self.opts_frame.pack(fill="x", padx=10, pady=10)
        
        # Multiplier
        ctk.CTkLabel(self.opts_frame, text="Target FPS / Multiplier:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.mult_var = ctk.StringVar(value="2x")
        self.opt_mult = ctk.CTkOptionMenu(self.opts_frame, variable=self.mult_var,
                                        values=["2x", "4x", "Target 30fps", "Target 60fps"])
        self.opt_mult.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Quality (FFmpeg only)
        self.lbl_quality = ctk.CTkLabel(self.opts_frame, text="Quality Mode:")
        self.lbl_quality.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.quality_var = ctk.StringVar(value="mci")
        self.opt_quality = ctk.CTkOptionMenu(self.opts_frame, variable=self.quality_var,
                                           values=["mci (High Quality)", "blend (Fast)"])
        self.opt_quality.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # --- Progress ---
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=10, pady=20)
        
        self.lbl_status = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.lbl_status.pack(anchor="w", padx=5)
        
        self.progress = ctk.CTkProgressBar(self.progress_frame)
        self.progress.pack(fill="x", padx=5, pady=5)
        self.progress.set(0)
        
        # --- Actions ---
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Start Interpolation", height=40, 
                                   font=("", 14, "bold"), command=self.start_processing)
        self.btn_run.pack(fill="x", padx=5)

    def browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv")])
        if path:
            self.input_path = path
            self.entry_input.delete(0, "end")
            self.entry_input.insert(0, path)

    def update_options(self):
        method = self.method_var.get()
        if method == "ffmpeg":
            self.lbl_quality.grid()
            self.opt_quality.grid()
            self.opt_mult.configure(values=["2x", "4x", "Target 30fps", "Target 60fps"])
        else:
            self.lbl_quality.grid_remove()
            self.opt_quality.grid_remove()
            self.opt_mult.configure(values=["2x", "4x"]) # RIFE usually does multipliers

    def start_processing(self):
        if self.is_processing: return
        
        input_path = self.entry_input.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid input video.")
            return
            
        self.is_processing = True
        self.btn_run.configure(state="disabled", text="Processing...")
        self.progress.set(0)
        self.lbl_status.configure(text="Initializing...")
        
        threading.Thread(target=self.run_thread, args=(input_path,), daemon=True).start()

    def run_thread(self, input_path):
        try:
            method = self.method_var.get()
            mult = self.mult_var.get()
            
            # Parse multiplier/target
            target_arg = ""
            if "Target" in mult:
                target_arg = f"--fps {mult.split()[1].replace('fps','')}"
            else:
                target_arg = f"--multiplier {mult.replace('x','')}"

            if method == "ffmpeg":
                quality = "mci" if "mci" in self.quality_var.get() else "blend"
                script = "ai_standalone/frame_interpolation.py" # Reuse existing script
                
                # We need to run it and capture output for progress
                # For now, just run it
                cmd = [sys.executable, f"src/scripts/{script}", input_path, 
                       "--method", quality] + target_arg.split()
                
                self.run_process(cmd)
                
            else:
                # AI (RIFE)
                script = "rife_inference.py"
                # Check if script exists
                if not (src_dir / "scripts" / "ai_standalone" / script).exists():
                    self.update_status("Error: RIFE script not found (Not implemented yet)")
                    return

                # Run via ai_runner
                # This is complex because we need to stream output from ai_runner
                # For now, basic run
                self.update_status("Running AI Inference (Check console)...")
                success, output = run_ai_script(script, input_path, *target_arg.split())
                
                if success:
                    self.update_status("Success!")
                    self.progress.set(1.0)
                else:
                    self.update_status(f"Error: {output[:50]}...")

        except Exception as e:
            self.update_status(f"Error: {e}")
        finally:
            self.is_processing = False
            self.after(0, lambda: self.btn_run.configure(state="normal", text="Start Interpolation"))

    def run_process(self, cmd):
        # Helper to run subprocess and update progress (basic)
        self.update_status("Processing with FFmpeg...")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            # Parse FFmpeg progress here if possible
            # frame=  123 fps= 12 ...
            if "frame=" in line:
                self.update_status(line.strip())
        
        process.wait()
        if process.returncode == 0:
            self.update_status("Done!")
            self.progress.set(1.0)
        else:
            self.update_status("Failed.")

    def update_status(self, msg):
        self.after(0, lambda: self.lbl_status.configure(text=msg))

if __name__ == "__main__":
    app = VideoInterpApp()
    app.mainloop()
