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

class VideoConvertGUI(tk.Tk):
    def __init__(self, target_path):
        super().__init__()
        self.title("Video Converter")
        self.geometry("600x550")
        
        self.target_path = target_path
        self.selection = get_selection_from_explorer(target_path)
        
        if not self.selection:
            # Fallback
            self.selection = [target_path]
            
        # Filter video files
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
        self.files = [Path(p) for p in self.selection if Path(p).suffix.lower() in video_exts]
        
        if not self.files:
            messagebox.showerror("Error", "No video files selected.")
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
        self.fmt_var = tk.StringVar(value="MP4 (H.264)")
        formats = [
            "MP4 (H.264 High)", 
            "MP4 (H.264 Low/Proxy)", 
            "MOV (ProRes 422)", 
            "MOV (ProRes 4444)", 
            "MOV (DNxHD)",
            "MKV (Copy Stream)"
        ]
        self.fmt_combo = ttk.Combobox(opt_frame, textvariable=self.fmt_var, values=formats, state="readonly")
        self.fmt_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.fmt_combo.bind("<<ComboboxSelected>>", self.on_fmt_change)
        
        # Scale
        ttk.Label(opt_frame, text="Scale:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.scale_var = tk.StringVar(value="100%")
        scales = ["100%", "50%", "25%", "Custom Width"]
        self.scale_combo = ttk.Combobox(opt_frame, textvariable=self.scale_var, values=scales, state="readonly")
        self.scale_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.scale_combo.bind("<<ComboboxSelected>>", self.on_scale_change)
        
        # Custom Width Entry (Hidden by default)
        self.lbl_width = ttk.Label(opt_frame, text="Width:")
        self.entry_width = ttk.Entry(opt_frame, width=10)
        
        # Quality (CRF)
        self.lbl_crf = ttk.Label(opt_frame, text="Quality (CRF):")
        self.lbl_crf.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        
        self.crf_var = tk.IntVar(value=23)
        self.scale_crf = ttk.Scale(opt_frame, from_=0, to=51, variable=self.crf_var, orient="horizontal")
        self.scale_crf.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.lbl_crf_val = ttk.Label(opt_frame, text="23")
        self.lbl_crf_val.grid(row=2, column=2, padx=5, pady=5)
        self.scale_crf.configure(command=lambda v: self.lbl_crf_val.configure(text=f"{int(float(v))}"))

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

    def on_fmt_change(self, event):
        fmt = self.fmt_var.get()
        if "H.264" in fmt:
            self.scale_crf.state(["!disabled"])
            self.lbl_crf.state(["!disabled"])
            if "High" in fmt: self.crf_var.set(18)
            else: self.crf_var.set(28)
            self.lbl_crf_val.configure(text=f"{self.crf_var.get()}")
        else:
            self.scale_crf.state(["disabled"])
            self.lbl_crf.state(["disabled"])
            
    def on_scale_change(self, event):
        scale = self.scale_var.get()
        if scale == "Custom Width":
            self.lbl_width.grid(row=1, column=2, padx=5, pady=5)
            self.entry_width.grid(row=1, column=3, padx=5, pady=5)
        else:
            self.lbl_width.grid_forget()
            self.entry_width.grid_forget()

    def start_convert(self):
        self.btn_convert.config(state="disabled")
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        ffmpeg = get_ffmpeg()
        fmt = self.fmt_var.get()
        scale = self.scale_var.get()
        crf = self.crf_var.get()
        
        total = len(self.files)
        self.progress["maximum"] = total
        
        success = 0
        errors = []
        
        for i, path in enumerate(self.files):
            self.lbl_status.config(text=f"Processing {i+1}/{total}: {path.name}")
            self.progress["value"] = i
            
            try:
                cmd = [ffmpeg, "-i", str(path)]
                
                # Output filename
                suffix = path.suffix
                if "MP4" in fmt: suffix = ".mp4"
                elif "MOV" in fmt: suffix = ".mov"
                elif "MKV" in fmt: suffix = ".mkv"
                
                out_name = f"{path.stem}_conv{suffix}"
                output_path = path.parent / out_name
                
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
                if scale == "50%":
                    vf.append("scale=iw/2:-2")
                elif scale == "25%":
                    vf.append("scale=iw/4:-2")
                elif scale == "Custom Width":
                    try:
                        w = int(self.entry_width.get())
                        vf.append(f"scale={w}:-2")
                    except:
                        pass
                
                if vf:
                    cmd.extend(["-vf", ",".join(vf)])
                
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
    app = VideoConvertGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_gui(sys.argv[1])
