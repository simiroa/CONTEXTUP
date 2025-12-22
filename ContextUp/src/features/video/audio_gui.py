import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import subprocess
import threading

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/video -> src
sys.path.append(str(src_dir))

from utils.external_tools import get_ffmpeg
from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow, FileListFrame

class VideoAudioGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Audio Tools", width=600, height=850, icon_name="video_audio_tools")
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        if not self.selection: self.selection = [target_path]
        
        self.files = [Path(p) for p in self.selection]
        
        self.var_new_folder = ctk.BooleanVar(value=True) # Default ON
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # 1. Header & File List
        self.add_header(f"Selected Files ({len(self.files)})")
        
        self.file_scroll = FileListFrame(self.main_frame, self.files)
        self.file_scroll.pack(fill="x", padx=20, pady=5)

        # 2. Tabs
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_extract = self.tab_view.add("Extract Audio")
        self.tab_remove = self.tab_view.add("Remove Audio")
        self.tab_separate = self.tab_view.add("Separate (Voice/BGM)")
        
        # --- Extract Tab ---
        ctk.CTkLabel(self.tab_extract, text="Select Output Format:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 10))
        self.ext_fmt = ctk.StringVar(value="MP3")
        
        radio_frame = ctk.CTkFrame(self.tab_extract, fg_color="transparent")
        radio_frame.pack(pady=10)
        ctk.CTkRadioButton(radio_frame, text="MP3 (Compressed)", variable=self.ext_fmt, value="MP3").pack(side="left", padx=20)
        ctk.CTkRadioButton(radio_frame, text="WAV (Lossless)", variable=self.ext_fmt, value="WAV").pack(side="left", padx=20)
        
        ctk.CTkButton(self.tab_extract, text="Extract Audio", height=40, command=self.run_extract).pack(pady=30)

        # --- Remove Tab ---
        ctk.CTkLabel(self.tab_remove, text="Remove audio track from video files.", font=ctk.CTkFont(size=14)).pack(pady=(40, 20))
        ctk.CTkButton(self.tab_remove, text="Remove Audio Track", height=40, fg_color="#C0392B", hover_color="#E74C3C", command=self.run_remove).pack(pady=10)

        # --- Separate Tab ---
        ctk.CTkLabel(self.tab_separate, text="Separate Voice and BGM (Experimental)", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 10))
        ctk.CTkLabel(self.tab_separate, text="Uses simple frequency filtering.", text_color="gray").pack(pady=5)
        
        self.sep_mode = ctk.StringVar(value="Voice")
        sep_frame = ctk.CTkFrame(self.tab_separate, fg_color="transparent")
        sep_frame.pack(pady=20)
        ctk.CTkRadioButton(sep_frame, text="Extract Voice", variable=self.sep_mode, value="Voice").pack(side="left", padx=20)
        ctk.CTkRadioButton(sep_frame, text="Extract BGM", variable=self.sep_mode, value="BGM").pack(side="left", padx=20)
        
        ctk.CTkButton(self.tab_separate, text="Process Separation", height=40, command=self.run_separate).pack(pady=20)

        # Progress
        # Output Option
        out_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        out_frame.pack(fill="x", padx=40, pady=(0, 5))
        ctk.CTkCheckBox(out_frame, text="Save to new folder", variable=self.var_new_folder).pack(side="left")

        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=40, pady=(10, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=(0, 20))

    def run_extract(self):
        self.start_thread("extract")

    def run_remove(self):
        self.start_thread("remove")

    def run_separate(self):
        self.start_thread("separate")

    def start_thread(self, action):
        # Disable tabs during processing? For now just run
        threading.Thread(target=self.process_files, args=(action,), daemon=True).start()

    def process_files(self, action):
        ffmpeg = get_ffmpeg()
        count = 0
        errors = []
        total = len(self.files)
        
        # Determine output folder name
        folder_map = {
            "extract": "Extracted_Audio",
            "remove": "Muted_Video",
            "separate": "Separated_Audio"
        }
        out_folder_name = folder_map.get(action, "Output")
        
        for i, path in enumerate(self.files):
            self.lbl_status.configure(text=f"Processing {i+1}/{total}: {path.name}")
            self.progress.set(i / total)
            
            try:
                # Determine output directory
                if self.var_new_folder.get():
                    out_dir = path.parent / out_folder_name
                    out_dir.mkdir(exist_ok=True)
                else:
                    out_dir = path.parent
                
                cmd = []
                if action == "extract":
                    fmt = self.ext_fmt.get().lower()
                    out_path = out_dir / path.with_suffix(f".{fmt}").name
                    cmd = [ffmpeg, "-i", str(path), "-vn", "-y", str(out_path)]
                    if fmt == "mp3":
                        cmd.extend(["-acodec", "libmp3lame", "-q:a", "2"])
                    else:
                        cmd.extend(["-acodec", "pcm_s16le"])
                    
                elif action == "remove":
                    out_path = out_dir / path.with_name(f"{path.stem}_noaudio{path.suffix}").name
                    cmd = [ffmpeg, "-i", str(path), "-c", "copy", "-an", "-y", str(out_path)]
                    
                elif action == "separate":
                    mode = self.sep_mode.get()
                    out_path = out_dir / path.with_name(f"{path.stem}_{mode.lower()}.wav").name
                    cmd = [ffmpeg, "-i", str(path), "-vn", "-y", str(out_path)]
                    if mode == "Voice":
                        # Simple voice filter
                        cmd.extend(["-af", "highpass=f=200,lowpass=f=3000"])
                    else:
                        # Simple BGM filter (remove voice range)
                        cmd.extend(["-af", "bandreject=f=1000:width_type=h:width=2000"])
                
                if cmd:
                    # Run without startupinfo to avoid 0xC0000135
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                    count += 1
                    
            except subprocess.CalledProcessError as e:
                errors.append(f"{path.name}: {e.stderr}")
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")
        
        self.progress.set(1.0)
        self.lbl_status.configure(text="Done")
        
        msg = f"Processed {count}/{total} files."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:5])
            messagebox.showwarning("Result", msg)
        else:
            messagebox.showinfo("Success", msg)
            self.destroy()

    def on_closing(self):
        self.destroy()

def run_gui(target_path):
    app = VideoAudioGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_gui(sys.argv[1])
    else:
        # Debug
        run_gui(str(Path.home() / "Videos"))
