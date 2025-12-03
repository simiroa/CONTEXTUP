"""
AI-powered background removal using latest models (Nov-Dec 2024).
Runs in isolated Conda environment.
"""
import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
import threading
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow
from utils.explorer import get_selection_from_explorer
from utils.ai_runner import run_ai_script

class BackgroundRemovalGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="AI Background Removal", width=500, height=650)
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        if not self.selection: self.selection = [target_path]
        
        # Filter for image files
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        self.files = [Path(p) for p in self.selection if Path(p).suffix.lower() in img_exts]
        
        if not self.files:
            messagebox.showinfo("Info", "No image files selected.")
            self.destroy()
            return

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.add_header(f"Removing Background ({len(self.files)} images)")
        
        # Model Selection
        ctk.CTkLabel(self.main_frame, text="Select AI Model:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.model_var = ctk.StringVar(value="rmbg")
        
        models = [
            ("rmbg", "RMBG-2.0", "Best Balance (92% accuracy)"),
            ("birefnet", "BiRefNet", "Highest Quality"),
            ("inspyrenet", "InSPyReNet", "Fastest")
        ]
        
        for val, name, desc in models:
            frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            frame.pack(anchor="w", padx=30, pady=2)
            ctk.CTkRadioButton(frame, text=name, variable=self.model_var, value=val).pack(side="left")
            ctk.CTkLabel(frame, text=desc, text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=10)
            
        # Options
        ctk.CTkLabel(self.main_frame, text="Output Options:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.transparency_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.main_frame, text="Transparent background (PNG)", variable=self.transparency_var).pack(anchor="w", padx=30, pady=5)
        
        # Post-processing
        ctk.CTkLabel(self.main_frame, text="Post-processing:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.postprocess_var = ctk.StringVar(value="none")
        pp_opts = [
            ("None", "none"),
            ("Edge Smoothing", "smooth"),
            ("Edge Sharpening", "sharpen"),
            ("Matte Feathering", "feather")
        ]
        
        pp_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        pp_frame.pack(anchor="w", padx=30)
        
        for label, val in pp_opts:
            ctk.CTkRadioButton(pp_frame, text=label, variable=self.postprocess_var, value=val).pack(anchor="w", pady=2)

        # Progress
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=40, pady=(20, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=(0, 10))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Start Processing", command=self.start_processing)
        self.btn_run.pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)

    def start_processing(self):
        self.btn_run.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        model = self.model_var.get()
        transparency = self.transparency_var.get()
        postprocess = self.postprocess_var.get()
        
        total = len(self.files)
        success_count = 0
        errors = []
        
        for i, img_path in enumerate(self.files):
            self.lbl_status.configure(text=f"Processing {i+1}/{total}: {img_path.name}")
            self.progress.set(i / total)
            
            try:
                args = [
                    "bg_removal.py",
                    str(img_path),
                    "--model", model
                ]
                
                if not transparency:
                    args.extend(["--no-transparency"])
                
                if postprocess != "none":
                    args.extend(["--postprocess", postprocess])
                
                success, output = run_ai_script(*args)
                
                if success:
                    success_count += 1
                else:
                    errors.append(f"{img_path.name}: {output[:100]}")
                    
            except Exception as e:
                errors.append(f"{img_path.name}: {str(e)[:100]}")
        
        self.progress.set(1.0)
        self.lbl_status.configure(text="Done")
        self.btn_run.configure(state="normal", text="Start Processing")
        
        if errors:
            msg = f"Processed {success_count}/{total} images.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5: msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            messagebox.showinfo("Success", f"Successfully processed {success_count} images.")
            self.destroy()

    def on_closing(self):
        self.destroy()

def remove_background(target_path: str):
    """Remove background from images using AI models."""
    try:
        app = BackgroundRemovalGUI(target_path)
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed: {e}")

