"""
Unified Audio Studio GUI
Combines Audio Converter, AI Separator (Spleeter), and Video Audio Tools.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import sys
import subprocess
import threading
import argparse

# Add src to path
try:
    current_dir = Path(__file__).parent
    src_dir = current_dir.parent
    sys.path.append(str(src_dir))
except: pass

from utils.external_tools import get_ffmpeg
from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow, FileListFrame

class AudioStudioGUI(BaseWindow):
    def __init__(self, target_path=None, start_tab="convert"):
        super().__init__(title="ContextUp Audio Studio", width=700, height=700)
        
        self.target_path = target_path
        self.files = []
        
        # Initial file selection
        if target_path:
            selection = get_selection_from_explorer(target_path)
            if not selection:
                selection = [target_path]
            self.files = [Path(p) for p in selection]
            
        self.create_widgets(start_tab)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self, start_tab):
        # 1. Header & File List (Shared)
        self.add_header(f"Selected Files ({len(self.files)})")
        
        self.file_scroll = FileListFrame(self.main_frame, self.files, height=120)
        self.file_scroll.pack(fill="x", padx=20, pady=5)
        
        # File Actions
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_frame, text="+ Add Files", width=100, command=self.add_files).pack(side="left")
        ctk.CTkButton(btn_frame, text="Clear", width=80, fg_color="#C0392B", hover_color="#E74C3C", command=self.clear_files).pack(side="left", padx=10)

        # 2. Tabs
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tab_convert = self.tab_view.add("Converter")
        self.tab_separate = self.tab_view.add("AI Separator")
        self.tab_video = self.tab_view.add("Video Audio")
        
        # Set default tab
        if start_tab == "separate":
            self.tab_view.set("AI Separator")
        elif start_tab == "video":
            self.tab_view.set("Video Audio")
        else:
            self.tab_view.set("Converter")
            
        self.setup_converter_tab()
        self.setup_separator_tab()
        self.setup_video_tab()
        
        # 3. Progress & Status (Shared)
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress = ctk.CTkProgressBar(self.progress_frame)
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.progress_frame, text="Ready", text_color="gray")
        self.lbl_status.pack()

    def add_files(self):
        files = filedialog.askopenfilenames()
        if files:
            new_files = [Path(f) for f in files]
            # Avoid duplicates
            existing = set(self.files)
            for f in new_files:
                if f not in existing:
                    self.files.append(f)
            self.file_scroll.files = self.files
            self.file_scroll.populate()
            self.add_header(f"Selected Files ({len(self.files)})") # Update header text hackily or just ignore

    def clear_files(self):
        self.files = []
        self.file_scroll.files = []
        self.file_scroll.populate()

    # --- Tab 1: Converter ---
    def setup_converter_tab(self):
        frame = self.tab_convert
        
        # Options
        opt_frame = ctk.CTkFrame(frame, fg_color="transparent")
        opt_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(opt_frame, text="Format:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.conv_fmt = ctk.StringVar(value="MP3")
        ctk.CTkComboBox(opt_frame, variable=self.conv_fmt, values=["MP3", "WAV", "OGG", "FLAC", "M4A"]).grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(opt_frame, text="Quality:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.conv_qual = ctk.StringVar(value="High")
        ctk.CTkComboBox(opt_frame, variable=self.conv_qual, values=["High", "Medium", "Low"]).grid(row=1, column=1, padx=10, pady=10)
        
        self.conv_meta = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_frame, text="Copy Metadata", variable=self.conv_meta).grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkButton(frame, text="Start Conversion", height=40, command=self.run_convert).pack(pady=20)

    def run_convert(self):
        if not self.files: return
        self.start_thread(self.process_convert)

    def process_convert(self):
        ffmpeg = get_ffmpeg()
        fmt = self.conv_fmt.get().lower()
        quality = self.conv_qual.get()
        
        total = len(self.files)
        for i, path in enumerate(self.files):
            self.update_status(f"Converting {i+1}/{total}: {path.name}", i/total)
            
            try:
                out_dir = path.parent / "Converted_Audio"
                out_dir.mkdir(exist_ok=True)
                out_path = out_dir / f"{path.stem}.{fmt}"
                
                cmd = [ffmpeg, "-i", str(path)]
                
                # Codec logic (simplified)
                if fmt == "mp3":
                    cmd.extend(["-acodec", "libmp3lame"])
                    q = "0" if quality == "High" else "4" if quality == "Medium" else "6"
                    cmd.extend(["-q:a", q])
                elif fmt == "wav":
                    cmd.extend(["-acodec", "pcm_s16le"])
                # ... other formats ...
                
                cmd.extend(["-y", str(out_path)])
                subprocess.run(cmd, check=True, capture_output=True)
                
            except Exception as e:
                print(f"Error: {e}")
        
        self.update_status("Conversion Complete!", 1.0)

    # --- Tab 2: AI Separator ---
    def setup_separator_tab(self):
        frame = self.tab_separate
        
        ctk.CTkLabel(frame, text="Spleeter AI Separation", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.sep_stems = ctk.StringVar(value="2stems")
        ctk.CTkRadioButton(frame, text="2 Stems (Vocals + Accompaniment)", variable=self.sep_stems, value="2stems").pack(pady=5)
        ctk.CTkRadioButton(frame, text="4 Stems (Vocals, Drums, Bass, Other)", variable=self.sep_stems, value="4stems").pack(pady=5)
        ctk.CTkRadioButton(frame, text="5 Stems (+ Piano)", variable=self.sep_stems, value="5stems").pack(pady=5)
        
        self.log_area = ctk.CTkTextbox(frame, height=100)
        self.log_area.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(frame, text="Start Separation", height=40, command=self.run_separate).pack(pady=10)

    def run_separate(self):
        if not self.files: return
        self.start_thread(self.process_separate)

    def process_separate(self):
        # Check spleeter
        try:
            subprocess.run(["spleeter", "--version"], check=True, capture_output=True)
        except:
            self.log("Error: Spleeter not installed. Run 'pip install spleeter'")
            return

        total = len(self.files)
        for i, path in enumerate(self.files):
            self.update_status(f"Separating {i+1}/{total}: {path.name}", i/total)
            self.log(f"Processing {path.name}...")
            
            try:
                out_dir = path.parent / "Separated_Audio"
                out_dir.mkdir(exist_ok=True)
                
                cmd = ["spleeter", "separate", "-p", f"spleeter:{self.sep_stems.get()}", "-o", str(out_dir), str(path)]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for line in process.stdout:
                    self.log(line.strip())
                process.wait()
                
            except Exception as e:
                self.log(f"Error: {e}")
                
        self.update_status("Separation Complete!", 1.0)
        self.log("Done.")

    def log(self, msg):
        self.after(0, lambda: self.log_area.insert("end", msg + "\n"))
        self.after(0, lambda: self.log_area.see("end"))

    # --- Tab 3: Video Audio ---
    def setup_video_tab(self):
        frame = self.tab_video
        
        ctk.CTkLabel(frame, text="Video Audio Operations", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.vid_action = ctk.StringVar(value="extract")
        ctk.CTkRadioButton(frame, text="Extract Audio (to MP3/WAV)", variable=self.vid_action, value="extract").pack(pady=5)
        ctk.CTkRadioButton(frame, text="Remove Audio (Mute Video)", variable=self.vid_action, value="remove").pack(pady=5)
        
        ctk.CTkButton(frame, text="Process Video", height=40, command=self.run_video).pack(pady=20)

    def run_video(self):
        if not self.files: return
        self.start_thread(self.process_video)

    def process_video(self):
        ffmpeg = get_ffmpeg()
        action = self.vid_action.get()
        total = len(self.files)
        
        for i, path in enumerate(self.files):
            self.update_status(f"Processing {i+1}/{total}: {path.name}", i/total)
            
            try:
                if action == "extract":
                    out_dir = path.parent / "Extracted_Audio"
                    out_dir.mkdir(exist_ok=True)
                    out_path = out_dir / f"{path.stem}.mp3"
                    cmd = [ffmpeg, "-i", str(path), "-vn", "-y", str(out_path)]
                else:
                    out_dir = path.parent / "Muted_Video"
                    out_dir.mkdir(exist_ok=True)
                    out_path = out_dir / f"{path.stem}_noaudio{path.suffix}"
                    cmd = [ffmpeg, "-i", str(path), "-c", "copy", "-an", "-y", str(out_path)]
                
                subprocess.run(cmd, check=True, capture_output=True)
                
            except Exception as e:
                print(f"Error: {e}")
                
        self.update_status("Video Processing Complete!", 1.0)

    # --- Helpers ---
    def start_thread(self, target):
        threading.Thread(target=target, daemon=True).start()

    def update_status(self, msg, progress):
        self.after(0, lambda: self.lbl_status.configure(text=msg))
        self.after(0, lambda: self.progress.set(progress))

    def on_closing(self):
        self.destroy()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="Target file or directory")
    parser.add_argument("--tab", choices=["convert", "separate", "video"], default="convert", help="Start tab")
    args = parser.parse_args()
    
    # Handle path being passed as first arg even if not named
    target_path = args.path
    
    app = AudioStudioGUI(target_path, start_tab=args.tab)
    app.mainloop()

if __name__ == "__main__":
    main()
