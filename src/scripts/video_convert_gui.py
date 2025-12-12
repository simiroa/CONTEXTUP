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
from utils.files import get_safe_path
from utils.gui_lib import BaseWindow, FileListFrame

class VideoConvertGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="ContextUp Video Converter", width=700, height=750)
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        
        if not self.selection:
            self.selection = [target_path]
            
        # Filter video files
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
        self.files = [Path(p) for p in self.selection if Path(p).suffix.lower() in video_exts]
        
        if not self.files:
            messagebox.showerror("Error", "No video files selected.")
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
        self.fmt_var = ctk.StringVar(value="MP4 (H.264)")
        formats = [
            "MP4 (H.264 High)", 
            "MP4 (H.264 Low/Proxy)", 
            "MOV (ProRes 422)", 
            "MOV (ProRes 4444)", 
            "MOV (DNxHD)",
            "MKV (Copy Stream)"
        ]
        self.fmt_combo = ctk.CTkComboBox(opt_frame, variable=self.fmt_var, values=formats, command=self.on_fmt_change)
        self.fmt_combo.grid(row=1, column=1, padx=15, pady=10, sticky="ew")
        
        # Scale
        ctk.CTkLabel(opt_frame, text="Scale:").grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.scale_var = ctk.StringVar(value="100%")
        scales = ["100%", "50%", "25%", "Custom Width"]
        self.scale_combo = ctk.CTkComboBox(opt_frame, variable=self.scale_var, values=scales, command=self.on_scale_change)
        self.scale_combo.grid(row=2, column=1, padx=15, pady=10, sticky="ew")
        
        # Custom Width (Hidden initially)
        self.entry_width = ctk.CTkEntry(opt_frame, placeholder_text="Width (px)")
        
        # Quality (CRF)
        self.lbl_crf = ctk.CTkLabel(opt_frame, text="Quality (CRF):")
        self.lbl_crf.grid(row=3, column=0, padx=15, pady=10, sticky="w")
        
        self.crf_var = tk.IntVar(value=23)
        self.slider_crf = ctk.CTkSlider(opt_frame, from_=0, to=51, number_of_steps=51, variable=self.crf_var, command=self.update_crf_label)
        self.slider_crf.grid(row=3, column=1, padx=15, pady=10, sticky="ew")
        
        self.lbl_crf_val = ctk.CTkLabel(opt_frame, text="23", width=30)
        self.lbl_crf_val.grid(row=3, column=2, padx=15, pady=10)

        # 3. Progress & Actions
        # Output Option
        out_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        out_frame.pack(fill="x", padx=40, pady=(0, 5))
        ctk.CTkCheckBox(out_frame, text="Save to 'Converted' folder", variable=self.var_new_folder).pack(side="left")

        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=40, pady=(10, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready to convert", text_color="gray")
        self.lbl_status.pack(pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_convert = ctk.CTkButton(btn_frame, text="Start Conversion", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_convert)
        self.btn_convert.pack(side="right", padx=10)
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, border_color="gray", height=40, command=self.destroy).pack(side="right", padx=10)

    def update_crf_label(self, value):
        self.lbl_crf_val.configure(text=str(int(value)))

    def on_fmt_change(self, choice):
        if "H.264" in choice:
            self.slider_crf.configure(state="normal")
            if "High" in choice: self.crf_var.set(18)
            else: self.crf_var.set(28)
        else:
            self.slider_crf.configure(state="disabled")
        self.update_crf_label(self.crf_var.get())

    def on_scale_change(self, choice):
        if choice == "Custom Width":
            self.entry_width.grid(row=2, column=2, padx=5, pady=10)
        else:
            self.entry_width.grid_forget()

    def start_convert(self):
        self.btn_convert.configure(state="disabled", text="Converting...")
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        ffmpeg = get_ffmpeg()
        fmt = self.fmt_var.get()
        scale = self.scale_var.get()
        crf = int(self.crf_var.get())
        
        total = len(self.files)
        success = 0
        errors = []
        out_dir_cache = {}
        
        for i, path in enumerate(self.files):
            self.lbl_status.configure(text=f"Processing {i+1}/{total}: {path.name}")
            self.progress.set(i / total)
            
            try:
                cmd = [ffmpeg, "-i", str(path)]
                
                # Output filename
                suffix = path.suffix
                if "MP4" in fmt: suffix = ".mp4"
                elif "MOV" in fmt: suffix = ".mov"
                elif "MKV" in fmt: suffix = ".mkv"
                
                # Determine output directory
                if self.var_new_folder.get():
                    base_dir = path.parent / "Converted"
                    if base_dir not in out_dir_cache:
                        safe_dir = base_dir if not base_dir.exists() else get_safe_path(base_dir)
                        safe_dir.mkdir(exist_ok=True)
                        out_dir_cache[base_dir] = safe_dir
                    out_dir = out_dir_cache[base_dir]
                    out_name = f"{path.stem}{suffix}" # Clean name in new folder
                else:
                    out_dir = path.parent
                    out_name = f"{path.stem}_conv{suffix}" # Suffix in same folder
                
                output_path = get_safe_path(out_dir / out_name)
                
                # Video Codec
                if "H.264" in fmt:
                    cmd.extend(["-c:v", "libx264", "-crf", str(crf), "-c:a", "aac"])
                    if "Low" in fmt: cmd.extend(["-preset", "fast"])
                elif "ProRes 422" in fmt:
                    cmd.extend(["-c:v", "prores_ks", "-profile:v", "2", "-c:a", "pcm_s16le"])
                elif "ProRes 4444" in fmt:
                    cmd.extend(["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-c:a", "pcm_s16le"])
                elif "DNxHD" in fmt:
                    cmd.extend(["-c:v", "dnxhd", "-profile:v", "dnxhr_hq", "-c:a", "pcm_s16le"])
                elif "Copy" in fmt:
                    cmd.extend(["-c", "copy"])
                
                # Scaling
                vf = []
                if scale == "50%": vf.append("scale=iw/2:-2")
                elif scale == "25%": vf.append("scale=iw/4:-2")
                elif scale == "Custom Width":
                    try:
                        w = int(self.entry_width.get())
                        vf.append(f"scale={w}:-2")
                    except: pass
                
                if vf: cmd.extend(["-vf", ",".join(vf)])
                
                cmd.extend(["-y", str(output_path)])
                
                # Run without startupinfo for now to debug 0xC0000135
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                success += 1
                
            except subprocess.CalledProcessError as e:
                errors.append(f"{path.name}: {e.stderr}")
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")
                
        self.progress.set(1.0)
        self.lbl_status.configure(text="Conversion Complete")
        self.btn_convert.configure(state="normal", text="Start Conversion")
        
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
    app = VideoConvertGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # Mutex - ensure only one GUI window opens
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("video_convert", anchor, timeout=0.2) is None:
            sys.exit(0)
        
        run_gui(anchor)
    else:
        run_gui(str(Path.home() / "Videos"))

