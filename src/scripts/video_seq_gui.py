import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import subprocess
import threading
import re

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.external_tools import get_ffmpeg
from utils.gui_lib import BaseWindow
from utils.files import get_safe_path

class SequenceToVideoGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="Sequence to Video", width=600, height=550)
        
        self.target_path = Path(target_path)
        if self.target_path.is_dir():
            self.folder = self.target_path
        else:
            self.folder = self.target_path.parent
            
        self.detect_sequence()
        self.create_widgets()
        
    def detect_sequence(self):
        files = sorted([f.name for f in self.folder.iterdir() if f.is_file()])
        img_files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.exr', '.tga', '.tif'))]
        
        self.guess_pattern = ""
        self.start_num = 0
        
        if img_files:
            ref_file = self.target_path.name if self.target_path.is_file() and self.target_path.name in img_files else img_files[0]
            match = re.search(r"(\d+)", ref_file)
            if match:
                padding = len(match.group(1))
                prefix = ref_file[:match.start()]
                suffix = ref_file[match.end():]
                self.guess_pattern = f"{prefix}%0{padding}d{suffix}"
                self.start_num = int(match.group(1))

    def create_widgets(self):
        # Header
        self.add_header("Sequence to Video")
        
        # Main Content
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Pattern
        ctk.CTkLabel(content, text="Input Pattern (e.g. seq.%04d.jpg):").pack(anchor="w", pady=(0, 5))
        self.entry_pattern = ctk.CTkEntry(content, width=400)
        self.entry_pattern.pack(fill="x", pady=(0, 15))
        if self.guess_pattern:
            self.entry_pattern.insert(0, self.guess_pattern)
            
        # Framerate
        ctk.CTkLabel(content, text="Framerate:").pack(anchor="w", pady=(0, 5))
        self.entry_fps = ctk.CTkEntry(content, width=100)
        self.entry_fps.pack(anchor="w", pady=(0, 15))
        self.entry_fps.insert(0, "30")
        
        # Preset
        ctk.CTkLabel(content, text="Preset:").pack(anchor="w", pady=(0, 5))
        self.presets = [
            "MP4 High (H.264, CRF 18)",
            "MP4 Low/Proxy (H.264, CRF 28)",
            "ProRes 422 (MOV)",
            "ProRes 4444 + Alpha (MOV)"
        ]
        self.var_preset = ctk.StringVar(value=self.presets[0])
        self.opt_preset = ctk.CTkOptionMenu(content, variable=self.var_preset, values=self.presets, width=300)
        self.opt_preset.pack(anchor="w", pady=(0, 15))
        
        # Options
        self.var_skip = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(content, text="Skip First Frame (Unreal Engine Fix)", variable=self.var_skip).pack(anchor="w", pady=(0, 10))
        
        # Actions
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Create Video", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_conversion)
        self.btn_run.pack(side="right", padx=10)
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", height=40, command=self.destroy).pack(side="right", padx=10)

    def start_conversion(self):
        self.btn_run.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.run_process, daemon=True).start()
        
    def run_process(self):
        try:
            pattern = self.entry_pattern.get()
            try:
                fps = int(self.entry_fps.get())
            except:
                fps = 30
            preset = self.var_preset.get()
            skip = self.var_skip.get()
            
            start_num = self.start_num
            if skip:
                start_num += 1
                
            output_name = self.folder.name
            ffmpeg_args = []
            
            if "MP4 High" in preset:
                output_name += "_high.mp4"
                ffmpeg_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18"]
            elif "MP4 Low" in preset:
                output_name += "_proxy.mp4"
                ffmpeg_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "fast"]
            elif "ProRes 422" in preset:
                output_name += "_422.mov"
                ffmpeg_args = ["-c:v", "prores_ks", "-profile:v", "2", "-pix_fmt", "yuv422p10le"]
            elif "ProRes 4444" in preset:
                output_name += "_4444.mov"
                ffmpeg_args = ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le"]
                
            output_path = get_safe_path(self.folder / output_name)
            ffmpeg = get_ffmpeg()
            
            cmd = [
                ffmpeg,
                "-framerate", str(fps),
                "-start_number", str(start_num),
                "-i", str(self.folder / pattern)
            ]
            cmd.extend(ffmpeg_args)
            cmd.extend(["-y", str(output_path)])
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            self.after(0, lambda: messagebox.showinfo("Success", f"Created {output_name}"))
            self.after(0, self.destroy)
            
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            self.after(0, lambda: messagebox.showerror("Error", f"FFmpeg failed: {err_msg}"))
            self.after(0, lambda: self.btn_run.configure(state="normal", text="Create Video"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Failed: {str(e)}"))
            self.after(0, lambda: self.btn_run.configure(state="normal", text="Create Video"))

def run_gui(target_path):
    app = SequenceToVideoGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_gui(sys.argv[1])
