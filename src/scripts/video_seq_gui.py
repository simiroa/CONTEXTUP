"""
Sequence to Video GUI
Convert image sequences to video files using FFmpeg.
"""
import sys
import subprocess
import threading
import re
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))


def main():
    """Main entry - deferred imports for fast startup."""
    import customtkinter as ctk
    from tkinter import messagebox
    
    from utils.external_tools import get_ffmpeg
    from utils.gui_lib import BaseWindow
    from utils.files import get_safe_path

    class SequenceToVideoGUI(BaseWindow):
        def __init__(self, target_path):
            super().__init__(title="Sequence to Video", width=550, height=480)
            
            self.target_path = Path(target_path)
            self.folder = self.target_path.parent if self.target_path.is_file() else self.target_path
            
            self.detect_sequence()
            self.create_widgets()
            
        def detect_sequence(self):
            """Auto-detect image sequence pattern from files."""
            files = sorted([f.name for f in self.folder.iterdir() if f.is_file()])
            img_files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.exr', '.tga', '.tif'))]
            
            self.guess_pattern = ""
            self.start_num = 0
            
            if img_files:
                ref = self.target_path.name if self.target_path.is_file() and self.target_path.name in img_files else img_files[0]
                match = re.search(r"(\d+)", ref)
                if match:
                    padding = len(match.group(1))
                    prefix = ref[:match.start()]
                    suffix = ref[match.end():]
                    self.guess_pattern = f"{prefix}%0{padding}d{suffix}"
                    self.start_num = int(match.group(1))

        def create_widgets(self):
            # Header
            self.add_header("Sequence to Video")
            
            content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Pattern
            ctk.CTkLabel(content, text="Pattern (e.g. seq.%04d.jpg):").pack(anchor="w", pady=(0, 3))
            self.entry_pattern = ctk.CTkEntry(content, width=350)
            self.entry_pattern.pack(fill="x", pady=(0, 12))
            if self.guess_pattern:
                self.entry_pattern.insert(0, self.guess_pattern)
                
            # Framerate
            row1 = ctk.CTkFrame(content, fg_color="transparent")
            row1.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row1, text="FPS:", width=60).pack(side="left")
            self.entry_fps = ctk.CTkEntry(row1, width=60)
            self.entry_fps.pack(side="left", padx=5)
            self.entry_fps.insert(0, "30")
            
            # Preset
            ctk.CTkLabel(row1, text="Preset:", width=60).pack(side="left", padx=(20, 0))
            self.presets = [
                "MP4 High (H.264)",
                "MP4 Proxy (Fast)",
                "ProRes 422",
                "ProRes 4444 + Alpha"
            ]
            self.var_preset = ctk.StringVar(value=self.presets[0])
            ctk.CTkOptionMenu(row1, variable=self.var_preset, values=self.presets, width=180).pack(side="left", padx=5)
            
            # Skip option
            self.var_skip = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(content, text="Skip First Frame (Unreal Engine Fix)", variable=self.var_skip).pack(anchor="w", pady=10)
            
            # Status
            self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
            self.lbl_status.pack(pady=5)
            
            self.progress = ctk.CTkProgressBar(self.main_frame, height=6)
            self.progress.pack(fill="x", padx=20, pady=5)
            self.progress.set(0)
            
            # Buttons
            btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=15)
            
            self.btn_run = ctk.CTkButton(btn_frame, text="Create Video", height=38, 
                                          font=("", 13, "bold"), command=self.start_conversion)
            self.btn_run.pack(side="right", padx=5)
            
            ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1,
                          text_color="gray", width=80, height=38, command=self.destroy).pack(side="right", padx=5)

        def start_conversion(self):
            self.btn_run.configure(state="disabled", text="Processing...")
            self.progress.set(0)
            threading.Thread(target=self.run_process, daemon=True).start()
            
        def run_process(self):
            try:
                pattern = self.entry_pattern.get()
                try:
                    fps = int(self.entry_fps.get())
                except:
                    fps = 30
                    
                preset = self.var_preset.get()
                start_num = self.start_num + (1 if self.var_skip.get() else 0)
                
                # Output setup
                output_name = self.folder.name
                ffmpeg_args = []
                
                if "High" in preset:
                    output_name += "_high.mp4"
                    ffmpeg_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18"]
                elif "Proxy" in preset:
                    output_name += "_proxy.mp4"
                    ffmpeg_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "fast"]
                elif "422" in preset:
                    output_name += "_422.mov"
                    ffmpeg_args = ["-c:v", "prores_ks", "-profile:v", "2", "-pix_fmt", "yuv422p10le"]
                elif "4444" in preset:
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
                
                self.after(0, lambda: self.lbl_status.configure(text="Encoding..."))
                subprocess.run(cmd, check=True, capture_output=True)
                
                self.after(0, lambda: self.progress.set(1))
                self.after(0, lambda: messagebox.showinfo("Success", f"Created {output_name}"))
                self.after(0, self.destroy)
                
            except subprocess.CalledProcessError as e:
                err = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
                self.after(0, lambda: messagebox.showerror("Error", f"FFmpeg failed:\n{err[:200]}"))
                self.after(0, lambda: self.btn_run.configure(state="normal", text="Create Video"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))
                self.after(0, lambda: self.btn_run.configure(state="normal", text="Create Video"))
    
    return SequenceToVideoGUI


if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # Mutex - ensure only one GUI window opens
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("sequence_to_video", anchor, timeout=0.2) is None:
            sys.exit(0)
        
        SequenceToVideoGUI = main()
        app = SequenceToVideoGUI(anchor)
        app.mainloop()
