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

class AudioConvertGUI(tk.Tk):
    def __init__(self, target_path):
        super().__init__()
        self.title("Audio Converter")
        self.geometry("500x450")
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        
        if not self.selection:
            self.selection = [target_path]
            
        # Filter audio files
        audio_exts = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.aiff'}
        self.files = [Path(p) for p in self.selection if Path(p).suffix.lower() in audio_exts]
        
        if not self.files:
            messagebox.showerror("Error", "No audio files selected.")
            self.destroy()
            return

        self.create_widgets()
        self.eval('tk::PlaceWindow . center')

    def create_widgets(self):
        # File List
        lbl_files = ttk.Label(self, text=f"Selected {len(self.files)} files:")
        lbl_files.pack(pady=5, padx=10, anchor="w")
        
        file_frame = ttk.Frame(self)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        file_list = tk.Listbox(file_frame, height=5)
        file_list.pack(side="left", fill="x", expand=True)
        scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=file_list.yview)
        scrollbar.pack(side="right", fill="y")
        file_list.config(yscrollcommand=scrollbar.set)
        
        for f in self.files:
            file_list.insert(tk.END, f.name)

        # Options Frame
        opt_frame = ttk.LabelFrame(self, text="Conversion Options")
        opt_frame.pack(fill="x", padx=10, pady=10)
        
        # Format
        ttk.Label(opt_frame, text="Format:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.fmt_var = tk.StringVar(value="MP3")
        formats = ["MP3", "WAV", "OGG", "FLAC", "M4A"]
        self.fmt_combo = ttk.Combobox(opt_frame, textvariable=self.fmt_var, values=formats, state="readonly")
        self.fmt_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Metadata
        self.var_meta = tk.BooleanVar(value=True)
        self.chk_meta = tk.Checkbutton(opt_frame, text="Copy Metadata (Tags)", variable=self.var_meta)
        self.chk_meta.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Quality (for lossy)
        ttk.Label(opt_frame, text="Quality:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.qual_var = tk.StringVar(value="High")
        qualities = ["High", "Medium", "Low"]
        self.qual_combo = ttk.Combobox(opt_frame, textvariable=self.qual_var, values=qualities, state="readonly")
        self.qual_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        opt_frame.columnconfigure(1, weight=1)

        # Progress
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=10)
        
        self.lbl_status = ttk.Label(self, text="Ready")
        self.lbl_status.pack(pady=5)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side="right", padx=5)
        self.btn_convert = ttk.Button(btn_frame, text="Convert", command=self.start_convert)
        self.btn_convert.pack(side="right", padx=5)

    def start_convert(self):
        self.btn_convert.config(state="disabled")
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        ffmpeg = get_ffmpeg()
        fmt = self.fmt_var.get().lower()
        copy_meta = self.var_meta.get()
        quality = self.qual_var.get()
        
        total = len(self.files)
        self.progress["maximum"] = total
        
        success = 0
        errors = []
        
        for i, path in enumerate(self.files):
            self.lbl_status.config(text=f"Processing {i+1}/{total}: {path.name}")
            self.progress["value"] = i
            
            try:
                cmd = [ffmpeg, "-i", str(path)]
                
                output_path = path.with_suffix(f".{fmt}")
                
                # Codec & Quality
                if fmt == "mp3":
                    cmd.extend(["-acodec", "libmp3lame"])
                    if quality == "High": cmd.extend(["-q:a", "0"]) # VBR best
                    elif quality == "Medium": cmd.extend(["-q:a", "4"])
                    else: cmd.extend(["-q:a", "6"])
                elif fmt == "wav":
                    cmd.extend(["-acodec", "pcm_s16le"])
                elif fmt == "ogg":
                    cmd.extend(["-acodec", "libvorbis"])
                    if quality == "High": cmd.extend(["-q:a", "6"])
                    elif quality == "Medium": cmd.extend(["-q:a", "4"])
                    else: cmd.extend(["-q:a", "2"])
                elif fmt == "flac":
                    cmd.extend(["-acodec", "flac"])
                elif fmt == "m4a":
                    cmd.extend(["-acodec", "aac"])
                    if quality == "High": cmd.extend(["-b:a", "256k"])
                    elif quality == "Medium": cmd.extend(["-b:a", "192k"])
                    else: cmd.extend(["-b:a", "128k"])
                
                # Metadata
                if not copy_meta:
                    cmd.extend(["-map_metadata", "-1"])
                else:
                    # Default is usually to copy, but let's be explicit if needed?
                    # FFmpeg usually copies by default for compatible containers.
                    pass
                
                cmd.extend(["-y", str(output_path)])
                
                subprocess.run(cmd, check=True, capture_output=True)
                success += 1
                
            except Exception as e:
                errors.append(f"{path.name}: {e}")
                
        self.progress["value"] = total
        self.lbl_status.config(text="Done")
        self.btn_convert.config(state="normal")
        
        msg = f"Converted {success}/{total} files."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:5])
            messagebox.showwarning("Result", msg)
        else:
            messagebox.showinfo("Success", msg)
            self.destroy()

def run_gui(target_path):
    app = AudioConvertGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_gui(sys.argv[1])
