"""
GUI wrapper for AI frame interpolation.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
import sys
import os
import shutil

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/ai -> src
sys.path.append(str(src_dir))

from utils.ai_runner import run_ai_script
from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow

from utils.config_persistence import load_gui_state, save_gui_state

# RIFE NCNN binary path check
def check_rife_binary():
    """Check if RIFE NCNN Vulkan binary is available."""
    # Logic: Look in bin/rife/ at Project Root
    try:
        project_root = Path(__file__).parent.parent.parent
        bin_dir = project_root / "bin"
        
        # 1. Check bin/rife/rife-ncnn-vulkan.exe
        target_1 = bin_dir / "rife" / "rife-ncnn-vulkan.exe"
        if target_1.exists(): return True, str(target_1)
        
        # 2. Check bin/rife-ncnn-vulkan.exe (flatter structure?)
        target_2 = bin_dir / "rife-ncnn-vulkan.exe"
        if target_2.exists(): return True, str(target_2)

        # 3. Recursive check
        rife_root = bin_dir / "rife"
        if rife_root.exists():
            found = list(rife_root.rglob("rife-ncnn-vulkan.exe"))
            if found: return True, str(found[0])
            
        # 4. PATH check
        if shutil.which("rife-ncnn-vulkan"):
            return True, "rife-ncnn-vulkan"
            
        return False, f"Not found in: {target_1}\nor {bin_dir}"
        
    except Exception as e:
        return False, f"Error checking binary: {e}"

class FrameInterpolationGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Frame Interpolation", width=600, height=700, icon_name="video_frame_interp") # Increased height for logs
        self.target_path = target_path
        
        # Load State
        self.gui_state = load_gui_state("frame_interp", {"multiplier": 2})
        

        
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
        
        self.multiplier_var = ctk.IntVar(value=self.gui_state.get("multiplier", 2))
        
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
        
        # Info + Binary Check
        info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(info_frame, text="Quality: Highest (Motion Compensated)", text_color="#3498DB").pack(anchor="w")
        
        # Check RIFE binary
        rife_available, rife_msg = check_rife_binary()
        if rife_available:
            ctk.CTkLabel(info_frame, text="✅ RIFE NCNN Vulkan: Installed", text_color="#2ECC71").pack(anchor="w")
        else:
            ctk.CTkLabel(info_frame, text=f"⚠ Beta Mode: Using FFmpeg (RIFE not found)", text_color="orange").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Debug: {rife_msg}", text_color="gray", font=ctk.CTkFont(size=10)).pack(anchor="w")
        
        ctk.CTkLabel(info_frame, text="Note: Processing may take time depending on video length", text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(info_frame, text="Tip: Large videos may take 10+ minutes. Do not close the window.", text_color="gray", font=ctk.CTkFont(size=10)).pack(anchor="w")
        
        # Progress
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=40, pady=(20, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=(0, 10))

        # Log Area
        self.log_box = ctk.CTkTextbox(self.main_frame, height=150, font=("Consolas", 10))
        self.log_box.pack(fill="x", padx=20, pady=(0, 10))
        self.log_box.configure(state="disabled")

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_run = ctk.CTkButton(btn_frame, text="Start Interpolation", command=self.start_interpolation)
        self.btn_run.pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", command=self.destroy).pack(side="right", padx=5)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", str(msg) + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_interpolation(self):
        self.btn_run.configure(state="disabled", text="Processing...")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        threading.Thread(target=self.run_interpolation, daemon=True).start()

    def run_interpolation(self):
        # Delayed import to avoid circular dependencies if any
        from utils.ai_runner import run_ai_script_streaming
        
        multiplier = self.multiplier_var.get()
        
        success_count = 0
        errors = []
        total = len(self.files_to_process)
        
        for i, video_path in enumerate(self.files_to_process):
            self.lbl_status.configure(text=f"Processing {i+1}/{total}: {video_path.name}")
            self.progress.set(i / total)
            self.log(f"--- Processing: {video_path.name} ---")
            
            try:
                # Build arguments
                # Use RIFE if available
                rife_available, _ = check_rife_binary()
                
                if rife_available:
                     script_name = "rife_inference.py"
                     args = [
                        script_name,
                        str(video_path),
                        "--multiplier", str(multiplier)
                    ]
                else:
                    script_name = "frame_interpolation.py"
                    args = [
                        script_name,
                        str(video_path),
                        "--multiplier", str(multiplier),
                        "--method", "mci"
                    ]
                
                # Run AI script (Streaming)
                has_error = False
                last_error_msg = ""
                
                for is_error, line in run_ai_script_streaming(*args):
                    if is_error:
                        has_error = True
                        last_error_msg = line
                        self.log(f"Error: {line}")
                    elif line == "__DONE__":
                        self.log("Done.")
                    else:
                        self.log(line)
                
                if not has_error:
                    success_count += 1
                else:
                    errors.append(f"{video_path.name}: {last_error_msg}")
                    
            except Exception as e:
                errors.append(f"{video_path.name}: {str(e)[:500]}")
                self.log(f"Exception: {e}")
        
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
        # Save State
        try:
            state = {"multiplier": self.multiplier_var.get()}
            save_gui_state("frame_interp", state)
        except:
            pass
        self.destroy()

def interpolate_frames(target_path: str):
    """
    Interpolate video frames using FFmpeg/AI.
    """
    try:
        app = FrameInterpolationGUI(target_path)
        app.mainloop()
            
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        messagebox.showerror("Error", f"Frame interpolation failed: {e}\n\n{err_msg}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        interpolate_frames(sys.argv[1])
