"""
Advanced AI Upscaling tools.
Uses Real-ESRGAN and GFPGAN via Conda environment.
"""
import subprocess
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
import tkinter.simpledialog
from utils.ai_runner import run_ai_script
from utils.explorer import get_selection_from_explorer

def _get_root_up():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class UpscaleDialog(tk.simpledialog.Dialog):
    """Dialog for upscale settings."""
    
    def __init__(self, parent, title="AI Upscale"):
        self.result = None
        self.face_enhance = None
        super().__init__(parent, title)
    
    def body(self, master):
        # Title
        tk.Label(master, text="Advanced AI Upscaling", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Scale selection
        tk.Label(master, text="Scale Factor:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.scale = tk.IntVar(value=4)
        
        scales = [
            (2, "2x (Fast)"),
            (3, "3x (Balanced)"),
            (4, "4x (Best Quality)")
        ]
        
        scale_frame = tk.Frame(master)
        scale_frame.grid(row=2, column=0, sticky=tk.W, padx=20, pady=2)
        
        for value, desc in scales:
            tk.Radiobutton(scale_frame, text=desc, variable=self.scale, value=value, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Face Enhancement
        tk.Label(master, text="Enhancement:", font=("Arial", 9)).grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        self.face_enhance_var = tk.BooleanVar(value=False)
        tk.Checkbutton(master, text="Face Enhancement (GFPGAN)", variable=self.face_enhance_var, font=("Arial", 9)).grid(row=4, column=0, sticky=tk.W, padx=20, pady=2)
        tk.Label(master, text="Restores faces in portraits/photos", font=("Arial", 8), fg="gray").grid(row=5, column=0, sticky=tk.W, padx=40, pady=0)
        
        return None
    
    def apply(self):
        self.result = {
            'scale': self.scale.get(),
            'face_enhance': self.face_enhance_var.get()
        }

def upscale_image(target_path: str):
    """
    Upscale image using AI.
    """
    try:
        selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [target_path]
        
        # Filter for image files
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
        files_to_process = [Path(p) for p in selection if Path(p).suffix.lower() in img_exts]
        
        if not files_to_process:
            messagebox.showinfo("Info", "No image files selected.")
            return
        
        # Show settings dialog
        root = _get_root_up()
        dialog = UpscaleDialog(root)
        
        if not dialog.result:
            return
        
        scale = dialog.result['scale']
        face_enhance = dialog.result['face_enhance']
        
        # Process files
        success_count = 0
        errors = []
        
        for img_path in files_to_process:
            try:
                # Build arguments
                args = [
                    "upscale.py",
                    str(img_path),
                    "--scale", str(scale)
                ]
                
                if face_enhance:
                    args.append("--face-enhance")
                
                # Run AI script in Conda environment
                success, output = run_ai_script(*args)
                
                if success:
                    success_count += 1
                else:
                    errors.append(f"{img_path.name}: {output[:100]}")
                    
            except Exception as e:
                errors.append(f"{img_path.name}: {str(e)[:100]}")
        
        # Show results
        if errors:
            msg = f"Processed {success_count}/{len(files_to_process)} images.\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            msg = f"Successfully upscaled {success_count} image(s)\n\nScale: {scale}x"
            if face_enhance:
                msg += "\nFace Enhancement: On"
            messagebox.showinfo("Success", msg)
            
    except FileNotFoundError as e:
        messagebox.showerror("Setup Required", 
            f"Conda environment not properly configured.\n\n"
            "Please run: python tools/fix_ai_env.py")
    except Exception as e:
        # Show clean error message without traceback
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        messagebox.showerror("Error", f"Upscaling failed:\n\n{error_msg}")
