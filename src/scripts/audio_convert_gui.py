import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
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
from utils.gui_lib import BaseWindow, FileListFrame

class AudioConvertGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Audio Converter", width=600, height=650)
        
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

        self.var_new_folder = ctk.BooleanVar(value=True) # Default ON
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # 1. Header & File List
        self.add_header(f"Selected Files ({len(self.files)})")
        
        self.file_scroll = FileListFrame(self.main_frame, self.files)
        self.file_scroll.pack(fill="x", padx=20, pady=5)
        
        # 2. Options
        opt_frame = ctk.CTkFrame(self.main_frame)
        opt_frame.pack(fill="x", padx=20, pady=20)
        opt_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(opt_frame, text="Conversion Options", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=15)
        
        # Format
        ctk.CTkLabel(opt_frame, text="Format:").grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.fmt_var = ctk.StringVar(value="MP3")
        formats = ["MP3", "WAV", "OGG", "FLAC", "M4A"]
        self.fmt_combo = ctk.CTkComboBox(opt_frame, variable=self.fmt_var, values=formats)
        self.fmt_combo.grid(row=1, column=1, padx=15, pady=10, sticky="ew")
        
        # Metadata
        self.var_meta = ctk.BooleanVar(value=True)
        self.chk_meta = ctk.CTkCheckBox(opt_frame, text="Copy Metadata (Tags)", variable=self.var_meta)
        self.chk_meta.grid(row=2, column=1, padx=15, pady=10, sticky="w")
        
        # Quality
        ctk.CTkLabel(opt_frame, text="Quality:").grid(row=3, column=0, padx=15, pady=10, sticky="w")
        self.qual_var = ctk.StringVar(value="High")
        qualities = ["High", "Medium", "Low"]
        self.qual_combo = ctk.CTkComboBox(opt_frame, variable=self.qual_var, values=qualities)
        self.qual_combo.grid(row=3, column=1, padx=15, pady=10, sticky="ew")

        # 3. Progress & Actions
        # Output Option
        out_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        out_frame.pack(fill="x", padx=40, pady=(0, 5))
        ctk.CTkCheckBox(out_frame, text="Save to 'Converted_Audio' folder", variable=self.var_new_folder).pack(side="left")

        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=40, pady=(10, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_convert = ctk.CTkButton(btn_frame, text="Convert", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_convert)
        self.btn_convert.pack(side="right", padx=10)
        
        ctk.CTkButton(btn_frame, text="Close", fg_color="transparent", border_width=1, border_color="gray", height=40, command=self.destroy).pack(side="right", padx=10)

    def start_convert(self):
        self.btn_convert.configure(state="disabled", text="Converting...")
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        ffmpeg = get_ffmpeg()
        fmt = self.fmt_var.get().lower()
        copy_meta = self.var_meta.get()
        quality = self.qual_var.get()
        
        total = len(self.files)
        success = 0
        errors = []
        
        for i, path in enumerate(self.files):
            self.lbl_status.configure(text=f"Processing {i+1}/{total}: {path.name}")
            self.progress.set(i / total)
            
            try:
                # Determine output directory
                if self.var_new_folder.get():
                    out_dir = path.parent / "Converted_Audio"
                    out_dir.mkdir(exist_ok=True)
                    out_name = f"{path.stem}.{fmt}"
                else:
                    out_dir = path.parent
                    out_name = f"{path.stem}_conv.{fmt}"
                
                output_path = out_dir / out_name
                
                cmd = [ffmpeg, "-i", str(path)]
                
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
                
                cmd.extend(["-y", str(output_path)])
                
                subprocess.run(cmd, check=True, capture_output=True)
                success += 1
                
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")
                
        self.progress.set(1.0)
        self.lbl_status.configure(text="Done")
        self.btn_convert.configure(state="normal", text="Convert")
        
        msg = f"Converted {success}/{total} files."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:5])
            messagebox.showwarning("Result", msg)
        else:
            messagebox.showinfo("Success", msg)
            self.destroy()

    def on_closing(self):
        self.destroy()

def run_gui(target_path):
    app = AudioConvertGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_gui(sys.argv[1])
    else:
        # Debug
        run_gui(str(Path.home() / "Music"))
