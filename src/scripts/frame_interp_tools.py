"""
GUI wrapper for AI frame interpolation.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.ai_runner import run_ai_script
from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow

class FrameInterpolationGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Frame Interpolation", width=500, height=500)
        self.target_path = target_path
        
        self.selection = get_selection_from_explorer(target_path)
        if not self.selection:
            self.selection = [target_path]
        
        # Filter for video files
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
        self.files_to_process = [Path(p) for p in self.selection if Path(p).suffix.lower() in video_exts]
        
        if not self.files_to_process:
            messagebox.showinfo("Info", "No video files selected.")
            self.destroy()
            return

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Header
        self.add_header(f"Interpolating {len(self.files_to_process)} Videos")
        
        # Settings Frame
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        # Multiplier selection
        ctk.CTkLabel(settings_frame, text="Interpolation Multiplier:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.multiplier_var = ctk.IntVar(value=2)
        
        multipliers = [
            (2, "2x (30fps → 60fps, 24fps → 48fps)"),
            (3, "3x (30fps → 90fps, 24fps → 72fps)"),
            (4, "4x (30fps → 120fps, 24fps → 96fps)")
        ]
        
        for value, desc in multipliers:
            frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
            frame.pack(anchor="w", padx=30, pady=2)
            ctk.CTkRadioButton(frame, text=f"{value}x", variable=self.multiplier_var, value=value).pack(side="left")
            ctk.CTkLabel(frame, text=desc, text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=10)
        
        # Info
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(info_frame, text="Quality: Highest (Motion Compensated)", text_color="#3498DB").pack(anchor="w")
        ctk.CTkLabel(info_frame, text="Acceleration: GPU (NVENC) Enabled", text_color="#2ECC71").pack(anchor="w")
        ctk.CTkLabel(info_frame, text="Note: Processing may take time depending on video length", text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(5, 0))
        
        # Progress
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=40, pady=(20, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Start Interpolation", command=self.start_interpolation)
        self.btn_run.pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)

    def start_interpolation(self):
        self.btn_run.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.run_interpolation, daemon=True).start()

    def run_interpolation(self):
        multiplier = self.multiplier_var.get()
        
        success_count = 0
        errors = []
        total = len(self.files_to_process)
        
        for i, video_path in enumerate(self.files_to_process):
            self.lbl_status.configure(text=f"Processing {i+1}/{total}: {video_path.name}")
            self.progress.set(i / total)
            
            try:
                # Build arguments
                args = [
                    "frame_interpolation.py",
                    str(video_path),
                    "--multiplier", str(multiplier),
                    "--method", "mci"  # Always use highest quality
                ]
                
                # Run AI script
                success, output = run_ai_script(*args)
                
                if success:
                    success_count += 1
                else:
                    errors.append(f"{video_path.name}: {output[:500]}")
                    
            except Exception as e:
                errors.append(f"{video_path.name}: {str(e)[:500]}")
        
        self.progress.set(1.0)
        self.lbl_status.configure(text="Done")
        self.btn_run.configure(state="normal", text="Start Interpolation")
        
        # Show results
        if errors:
            msg = f"Processed {success_count}/{total} videos.\n\nMultiplier: {multiplier}x\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            messagebox.showinfo("Success", 
                f"Successfully interpolated {success_count} video(s)\n\n"
                f"Multiplier: {multiplier}x\n"
                f"Quality: Highest (Motion Compensated)\n"
                f"Output: *_{multiplier}x.mp4")
            self.destroy()

    def on_closing(self):
        self.destroy()

def interpolate_frames(target_path: str):
    """
    Interpolate video frames using FFmpeg/AI.
    """
    try:
        app = FrameInterpolationGUI(target_path)
        app.mainloop()
            
    except Exception as e:
        messagebox.showerror("Error", f"Frame interpolation failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        interpolate_frames(sys.argv[1])
