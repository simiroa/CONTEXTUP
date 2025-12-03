"""
Advanced AI Upscaling tools.
Uses Real-ESRGAN and GFPGAN via Conda environment.
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

class UpscaleGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp AI Upscale", width=500, height=650)
        self.target_path = target_path
        
        self.selection = get_selection_from_explorer(target_path)
        if not self.selection:
            self.selection = [target_path]
        
        # Filter for image files
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
        self.files_to_process = [Path(p) for p in self.selection if Path(p).suffix.lower() in img_exts]
        
        if not self.files_to_process:
            messagebox.showinfo("Info", "No image files selected.")
            self.destroy()
            return

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Header
        self.add_header(f"Upscaling {len(self.files_to_process)} Images")
        
        # Settings Frame
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        # Scale Factor
        ctk.CTkLabel(settings_frame, text="Scale Factor:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.scale_var = ctk.IntVar(value=4)
        
        scales = [
            (2, "2x (Fast)"),
            (3, "3x (Balanced)"),
            (4, "4x (Best Quality)")
        ]
        
        for value, desc in scales:
            ctk.CTkRadioButton(settings_frame, text=desc, variable=self.scale_var, value=value).pack(anchor="w", padx=30, pady=5)
            
        # Face Enhancement
        ctk.CTkLabel(settings_frame, text="Enhancement:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.face_enhance_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(settings_frame, text="Face Enhancement (GFPGAN)", variable=self.face_enhance_var).pack(anchor="w", padx=30, pady=5)
        ctk.CTkLabel(settings_frame, text="Restores faces in portraits/photos", text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=55, pady=0)
        
        # Progress
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=40, pady=(20, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Start Upscale", command=self.start_upscale)
        self.btn_run.pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)

    def start_upscale(self):
        self.btn_run.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.run_upscale, daemon=True).start()

    def run_upscale(self):
        scale = self.scale_var.get()
        face_enhance = self.face_enhance_var.get()
        
        success_count = 0
        errors = []
        total = len(self.files_to_process)
        
        for i, img_path in enumerate(self.files_to_process):
            self.lbl_status.configure(text=f"Processing {i+1}/{total}: {img_path.name}")
            self.progress.set(i / total)
            
            try:
                # Build arguments
                args = [
                    "upscale.py",
                    str(img_path),
                    "--scale", str(scale)
                ]
                
                if face_enhance:
                    args.append("--face-enhance")
                
                # Run AI script
                success, output = run_ai_script(*args)
                
                if success:
                    success_count += 1
                else:
                    errors.append(f"{img_path.name}: {output[:100]}")
                    
            except Exception as e:
                errors.append(f"{img_path.name}: {str(e)[:100]}")
        
        self.progress.set(1.0)
        self.lbl_status.configure(text="Done")
        self.btn_run.configure(state="normal", text="Start Upscale")
        
        # Show results
        if errors:
            msg = f"Processed {success_count}/{total} images.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            msg = f"Successfully upscaled {success_count} image(s)\n\nScale: {scale}x"
            if face_enhance:
                msg += "\nFace Enhancement: On"
            messagebox.showinfo("Success", msg)
            self.destroy()

    def on_closing(self):
        self.destroy()

def upscale_image(target_path: str):
    """
    Upscale image using AI.
    """
    try:
        app = UpscaleGUI(target_path)
        app.mainloop()
            
    except Exception as e:
        messagebox.showerror("Error", f"Upscaling failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        upscale_image(sys.argv[1])
