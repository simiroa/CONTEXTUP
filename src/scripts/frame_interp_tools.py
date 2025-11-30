"""
GUI wrapper for AI frame interpolation.
"""
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
import tkinter.simpledialog
from utils.ai_runner import run_ai_script
from utils.explorer import get_selection_from_explorer

def _get_root_fi():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    return root

class FrameInterpolationDialog(tk.simpledialog.Dialog):
    """Dialog for frame interpolation settings."""
    
    def __init__(self, parent, title="Frame Interpolation"):
        self.result = None
        super().__init__(parent, title)
    
    def body(self, master):
        # Title
        tk.Label(master, text="Frame Interpolation Settings", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Multiplier selection
        tk.Label(master, text="Interpolation Multiplier:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.multiplier = tk.IntVar(value=2)
        
        multipliers = [
            (2, "2x (30fps → 60fps, 24fps → 48fps)"),
            (3, "3x (30fps → 90fps, 24fps → 72fps)"),
            (4, "4x (30fps → 120fps, 24fps → 96fps)")
        ]
        
        for i, (value, desc) in enumerate(multipliers):
            frame = tk.Frame(master)
            frame.grid(row=i+2, column=0, sticky=tk.W, padx=20, pady=2)
            
            tk.Radiobutton(frame, text=f"{value}x", variable=self.multiplier, value=value, font=("Arial", 9, "bold")).pack(anchor=tk.W)
            tk.Label(frame, text=desc, font=("Arial", 8), fg="gray").pack(anchor=tk.W, padx=20)
        
        # Info
        tk.Label(master, text="Quality: Highest (Motion Compensated)", font=("Arial", 8), fg="blue").grid(row=5, column=0, sticky=tk.W, padx=20, pady=(10, 0))
        tk.Label(master, text="Acceleration: GPU (NVENC) Enabled", font=("Arial", 8), fg="green").grid(row=6, column=0, sticky=tk.W, padx=20, pady=(2, 0))
        tk.Label(master, text="Note: Processing may take time depending on video length", font=("Arial", 8), fg="gray").grid(row=7, column=0, sticky=tk.W, padx=20, pady=(2, 0))
        
        return None
    
    def apply(self):
        self.result = {
            'multiplier': self.multiplier.get()
        }

def interpolate_frames(target_path: str):
    """
    Interpolate video frames using FFmpeg/AI.
    """
    try:
        selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [target_path]
        
        # Filter for video files
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
        files_to_process = [Path(p) for p in selection if Path(p).suffix.lower() in video_exts]
        
        if not files_to_process:
            messagebox.showinfo("Info", "No video files selected.")
            return
        
        # Show settings dialog
        root = _get_root_fi()
        dialog = FrameInterpolationDialog(root)
        
        if not dialog.result:
            return
        
        multiplier = dialog.result['multiplier']
        
        # Process files
        success_count = 0
        errors = []
        
        for video_path in files_to_process:
            try:
                # Build arguments
                args = [
                    "frame_interpolation.py",
                    str(video_path),
                    "--multiplier", str(multiplier),
                    "--method", "mci"  # Always use highest quality
                ]
                
                # Run AI script in Conda environment
                success, output = run_ai_script(*args)
                
                if success:
                    success_count += 1
                else:
                    errors.append(f"{video_path.name}: {output[:100]}")
                    
            except Exception as e:
                errors.append(f"{video_path.name}: {str(e)[:100]}")
        
        # Show results
        if errors:
            msg = f"Processed {success_count}/{len(files_to_process)} videos.\n\nMultiplier: {multiplier}x\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += "\n..."
            messagebox.showwarning("Completed with Errors", msg)
        else:
            messagebox.showinfo("Success", 
                f"Successfully interpolated {success_count} video(s)\n\n"
                f"Multiplier: {multiplier}x\n"
                f"Quality: Highest (Motion Compensated)\n"
                f"Output: *_{multiplier}x.mp4")
            
    except FileNotFoundError as e:
        messagebox.showerror("Setup Required", 
            f"Conda environment not properly configured.\n\n"
            "Please run: python tools/fix_ai_env.py")
    except Exception as e:
        # Show clean error message without traceback
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        messagebox.showerror("Error", f"Frame interpolation failed:\n\n{error_msg}")
