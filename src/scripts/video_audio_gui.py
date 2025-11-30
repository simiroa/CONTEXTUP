import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys
import subprocess
import threading

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.external_tools import get_ffmpeg
from utils.explorer import get_selection_from_explorer

class VideoAudioGUI(tk.Tk):
    def __init__(self, target_path):
        super().__init__()
        self.title("Audio Tools")
        self.geometry("500x400")
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        if not self.selection: self.selection = [target_path]
        
        self.files = [Path(p) for p in self.selection] # Accept all, filter later if needed

        self.create_widgets()
        self.eval('tk::PlaceWindow . center')

    def create_widgets(self):
        # Tabs for Extract / Remove / Separate
        tab_control = ttk.Notebook(self)
        
        self.tab_extract = ttk.Frame(tab_control)
        self.tab_remove = ttk.Frame(tab_control)
        self.tab_separate = ttk.Frame(tab_control)
        
        tab_control.add(self.tab_extract, text='Extract Audio')
        tab_control.add(self.tab_remove, text='Remove Audio')
        tab_control.add(self.tab_separate, text='Separate (Voice/BGM)')
        
        tab_control.pack(expand=1, fill="both", padx=10, pady=5)
        self.tab_control = tab_control

        # --- Extract Tab ---
        ttk.Label(self.tab_extract, text="Format:").pack(pady=10)
        self.ext_fmt = tk.StringVar(value="MP3")
        ttk.Radiobutton(self.tab_extract, text="MP3", variable=self.ext_fmt, value="MP3").pack()
        ttk.Radiobutton(self.tab_extract, text="WAV", variable=self.ext_fmt, value="WAV").pack()
        
        ttk.Button(self.tab_extract, text="Extract", command=self.run_extract).pack(pady=20)

        # --- Remove Tab ---
        ttk.Label(self.tab_remove, text="Remove audio track from video files.").pack(pady=20)
        ttk.Button(self.tab_remove, text="Remove Audio", command=self.run_remove).pack(pady=10)

        # --- Separate Tab ---
        ttk.Label(self.tab_separate, text="Separate Voice and BGM using AI.").pack(pady=10)
        ttk.Label(self.tab_separate, text="(Requires Spleeter/Demucs - Not fully implemented yet)").pack(pady=5)
        # Placeholder for now, or simple filter
        self.sep_mode = tk.StringVar(value="Voice")
        ttk.Radiobutton(self.tab_separate, text="Extract Voice (Simple Filter)", variable=self.sep_mode, value="Voice").pack()
        ttk.Radiobutton(self.tab_separate, text="Extract BGM (Simple Filter)", variable=self.sep_mode, value="BGM").pack()
        
        ttk.Button(self.tab_separate, text="Separate", command=self.run_separate).pack(pady=20)

        # Status
        self.lbl_status = ttk.Label(self, text=f"Selected {len(self.files)} files")
        self.lbl_status.pack(pady=5)

    def run_extract(self):
        self.process_files("extract")

    def run_remove(self):
        self.process_files("remove")

    def run_separate(self):
        self.process_files("separate")

    def process_files(self, action):
        ffmpeg = get_ffmpeg()
        count = 0
        errors = []
        
        for path in self.files:
            try:
                if action == "extract":
                    fmt = self.ext_fmt.get().lower()
                    out_path = path.with_suffix(f".{fmt}")
                    cmd = [ffmpeg, "-i", str(path), "-vn", "-y", str(out_path)]
                    if fmt == "mp3":
                        cmd.extend(["-acodec", "libmp3lame"])
                    else:
                        cmd.extend(["-acodec", "pcm_s16le"])
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                elif action == "remove":
                    out_path = path.with_name(f"{path.stem}_noaudio{path.suffix}")
                    cmd = [ffmpeg, "-i", str(path), "-c", "copy", "-an", "-y", str(out_path)]
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                elif action == "separate":
                    # Simple filter fallback
                    mode = self.sep_mode.get()
                    out_path = path.with_name(f"{path.stem}_{mode.lower()}.wav")
                    cmd = [ffmpeg, "-i", str(path), "-vn", "-y", str(out_path)]
                    if mode == "Voice":
                        # Highpass + Lowpass for voice range approx
                        cmd.extend(["-af", "highpass=f=200,lowpass=f=3000"])
                    else:
                        # Bandreject voice range? Very crude.
                        cmd.extend(["-af", "bandreject=f=1000:width_type=h:width=2000"])
                    subprocess.run(cmd, check=True, capture_output=True)
                
                count += 1
            except Exception as e:
                errors.append(f"{path.name}: {e}")
        
        msg = f"Processed {count} files."
        if errors:
            msg += "\nErrors:\n" + "\n".join(errors[:5])
            messagebox.showwarning("Result", msg)
        else:
            messagebox.showinfo("Success", msg)
            self.destroy()

def run_gui(target_path):
    app = VideoAudioGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_gui(sys.argv[1])
