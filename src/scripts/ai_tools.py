"""
AI-powered background removal using latest models (Nov-Dec 2024).
Runs in isolated Conda environment.
"""
import subprocess
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
import tkinter.simpledialog

def _get_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class BackgroundRemovalDialog(tk.simpledialog.Dialog):
    """Dialog for background removal model selection."""
    
    def __init__(self, parent, title="AI Background Removal"):
        self.result = None
        self.transparency = None
        self.postprocess = None
        super().__init__(parent, title)
    
    def body(self, master):
        # Model selection
        tk.Label(master, text="Select AI Model:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        self.model = tk.StringVar(value="rmbg")
        
        models = [
            ("rmbg", "RMBG-2.0", "Best Balance (92% accuracy, Nov 2024) ✓"),
            ("birefnet", "BiRefNet", "Highest Quality (Dec 2024 update) ✓"),
            ("inspyrenet", "InSPyReNet", "Fastest (MIT license, 500K+ downloads) ✓")
        ]
        
        for i, (value, name, desc) in enumerate(models):
            frame = tk.Frame(master)
            frame.grid(row=i+1, column=0, sticky=tk.W, padx=20, pady=5)
            
            tk.Radiobutton(frame, text=name, variable=self.model, value=value, font=("Arial", 9, "bold")).pack(anchor=tk.W)
            tk.Label(frame, text=desc, font=("Arial", 8), fg="gray").pack(anchor=tk.W, padx=20)
        
        # Separator
        tk.Frame(master, height=2, bd=1, relief=tk.SUNKEN).grid(row=4, column=0, sticky=tk.EW, pady=10)
        
        # Output options
        tk.Label(master, text="Output Options:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        # Transparency checkbox
        self.transparency_var = tk.BooleanVar(value=True)
        tk.Checkbutton(master, text="Transparent background (PNG)", variable=self.transparency_var, font=("Arial", 9)).grid(row=6, column=0, sticky=tk.W, padx=20, pady=2)
        
        # Post-processing dropdown
        tk.Label(master, text="Post-processing:", font=("Arial", 9)).grid(row=7, column=0, sticky=tk.W, padx=20, pady=(10, 2))
        
        self.postprocess_var = tk.StringVar(value="none")
        postprocess_options = [
            ("None", "none"),
            ("Edge Smoothing (softer edges)", "smooth"),
            ("Edge Sharpening (crisp edges)", "sharpen"),
            ("Matte Feathering (natural blend)", "feather")
        ]
        
        postprocess_frame = tk.Frame(master)
        postprocess_frame.grid(row=8, column=0, sticky=tk.W, padx=40, pady=2)
        
        for label, value in postprocess_options:
            tk.Radiobutton(postprocess_frame, text=label, variable=self.postprocess_var, value=value, font=("Arial", 8)).pack(anchor=tk.W)
        
        return None
    
    def apply(self):
        self.result = {
            'model': self.model.get(),
            'transparency': self.transparency_var.get(),
            'postprocess': self.postprocess_var.get()
        }

def remove_background(target_path: str):
    """
    Remove background from images using AI models.
    Runs in isolated Conda environment.
    """
    try:
        from utils.explorer import get_selection_from_explorer
        from utils.ai_runner import run_ai_script
        
        selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [target_path]
        
        # Filter for image files
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        files_to_process = [Path(p) for p in selection if Path(p).suffix.lower() in img_exts]
        
        if not files_to_process:
            messagebox.showinfo("Info", "No image files selected.")
            return
        
        # Show model selection dialog
        root = _get_root()
        dialog = BackgroundRemovalDialog(root)
        
        if not dialog.result:
            return
        
        # Get options
        model = dialog.result['model']
        transparency = dialog.result['transparency']
        postprocess = dialog.result['postprocess']
        
        # Process files
        from utils.progress_gui import run_batch_gui
        
        def process_image(img_path, update_msg):
            try:
                # Build arguments
                args = [
                    "bg_removal.py",
                    str(img_path),
                    "--model", model
                ]
                
                # Add transparency option
                if not transparency:
                    args.extend(["--no-transparency"])
                
                # Add post-processing option
                if postprocess != "none":
                    args.extend(["--postprocess", postprocess])
                
                update_msg(f"Running AI model on {img_path.name}...")
                
                # Run AI script in Conda environment
                success, output = run_ai_script(*args)
                
                if success:
                    return True, ""
                else:
                    return False, output[:200]
                    
            except Exception as e:
                return False, str(e)[:200]

        run_batch_gui("AI Background Removal", files_to_process, process_image)
            
    except FileNotFoundError as e:
        messagebox.showerror("Setup Required", 
            f"Conda environment not properly configured.\n\n"
            "Please run: python tools/fix_ai_env.py")
    except Exception as e:
        # Show clean error message without traceback
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        messagebox.showerror("Error", f"Background removal failed:\n\n{error_msg}")
