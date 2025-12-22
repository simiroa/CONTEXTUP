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
src_dir = current_dir.parent.parent  # features/video -> src
sys.path.append(str(src_dir))


def main():
    """Main entry - deferred imports for fast startup."""
    import customtkinter as ctk
    from tkinter import messagebox
    
    from utils.external_tools import get_ffmpeg
    from utils.gui_lib import BaseWindow
    from utils.files import get_safe_path
    from utils.i18n import t

    class SequenceToVideoGUI(BaseWindow):
        def __init__(self, target_path):
            super().__init__(title="ContextUp Sequence to Video", width=600, height=550, icon_name="sequence_to_video")
            
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
            self.frame_count = len(img_files)
            self.seq_name = self.folder.name
            
            if img_files:
                self.seq_files = [self.folder / f for f in img_files] # Store full paths for ListFrame
                ref = self.target_path.name if self.target_path.is_file() and self.target_path.name in img_files else img_files[0]
                match = re.search(r"(\d+)", ref)
                if match:
                    padding = len(match.group(1))
                    prefix = ref[:match.start()]
                    suffix = ref[match.end():]
                    self.guess_pattern = f"{prefix}%0{padding}d{suffix}"
                    self.start_num = int(match.group(1))
                    self.seq_name = prefix.strip("._-") or self.folder.name
            else:
                self.seq_files = []

        def create_widgets(self):
            # --- Strict Layout: Footer FIRST, Header SECOND, Body LAST ---
            
            # 4. Footer (Packed FIRST to stick to bottom)
            footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            footer_frame.pack(side="bottom", fill="x", padx=20, pady=20)
            
            # Footer: Progress
            self.progress = ctk.CTkProgressBar(footer_frame, height=10)
            self.progress.pack(fill="x", pady=(0, 10))
            self.progress.set(0)
            
            # Footer: Buttons (Equal Size)
            btn_row = ctk.CTkFrame(footer_frame, fg_color="transparent")
            btn_row.pack(fill="x")
            
            self.btn_cancel = ctk.CTkButton(btn_row, text="Cancel", height=45, fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90"), command=self.destroy)
            self.btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            self.btn_run = ctk.CTkButton(btn_row, text="Create Video", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_conversion)
            self.btn_run.pack(side="left", fill="x", expand=True, padx=(0, 0))
            
            self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray", font=("", 11))
            self.lbl_status.pack(side="bottom", pady=(0, 5))


            # 1. Header (Standardized)
            from utils.gui_lib import FileListFrame
            header_text = f"{self.seq_name} ({self.frame_count} frames)"
            self.add_header(header_text, font_size=16)
            
            # 2. Main Body (Fills remaining space)
            body_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            body_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)
            
            # File List (Top of Body, Fixed Height)
            # Use FileListFrame to show the sequence files
            self.file_list = FileListFrame(body_frame, self.seq_files, height=150)
            self.file_list.pack(fill="x", pady=(0, 10))
            
            # Options (Rest of Body)
            content = ctk.CTkFrame(body_frame, fg_color="transparent")
            content.pack(fill="x")
            content.grid_columnconfigure(1, weight=1)
            
            # Row 0: Pattern
            ctk.CTkLabel(content, text="Pattern:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")
            self.entry_pattern = ctk.CTkEntry(content)
            self.entry_pattern.grid(row=0, column=1, padx=0, pady=10, sticky="ew")
            if self.guess_pattern:
                self.entry_pattern.insert(0, self.guess_pattern)
            
            # Row 1: FPS & Preset
            # We can put these in grid row 1 and 2
            ctk.CTkLabel(content, text="Framerate:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=(0, 10), pady=10, sticky="w")
            
            fps_frame = ctk.CTkFrame(content, fg_color="transparent")
            fps_frame.grid(row=1, column=1, padx=0, pady=10, sticky="ew")
            
            self.entry_fps = ctk.CTkEntry(fps_frame, width=60)
            self.entry_fps.pack(side="left")
            self.entry_fps.insert(0, "30")
            ctk.CTkLabel(fps_frame, text="fps").pack(side="left", padx=5)
            
            # Row 2: Preset
            ctk.CTkLabel(content, text="Format:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=(0, 10), pady=10, sticky="w")
            
            self.presets = [
                "MP4 High (H.264)",
                "MP4 Proxy (Fast)",
                "ProRes 422",
                "ProRes 4444 + Alpha"
            ]
            self.var_preset = ctk.StringVar(value=self.presets[0])
            ctk.CTkOptionMenu(content, variable=self.var_preset, values=self.presets).grid(row=2, column=1, padx=0, pady=10, sticky="ew")
            
            # Row 3: Skip Frame checkbox
            self.var_skip = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(content, text="Skip First Frame (Unreal Engine Fix)", variable=self.var_skip).grid(row=3, column=0, columnspan=2, padx=0, pady=15, sticky="w")


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


def run_gui(target_path):
    """Entry point for external calls."""
    SequenceToVideoGUI = main()
    app = SequenceToVideoGUI(target_path)
    app.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        try:
            from utils.batch_runner import collect_batch_context
            # Prevent multiple instances if multiple files selected
            if collect_batch_context("sequence_to_video", anchor, timeout=0.2) is None:
                sys.exit(0)
        except ImportError:
            pass # Fallback if utils not available (standalone dev)

        SequenceToVideoGUI = main()
        app = SequenceToVideoGUI(anchor)
        app.mainloop()
    else:
        # Dev/Test mode - launch with dummy or prompt
        print("Sequence to Video: No file provided.")
