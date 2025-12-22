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
from utils.files import get_safe_path
from utils.gui_lib import BaseWindow, FileListFrame
from utils.i18n import t
from core.config import MenuConfig

class VideoConvertGUI(BaseWindow):
    def __init__(self, target_path, demo=False):
        # Sync Name
        self.tool_name = "ContextUp Video Converter"
        try:
             config = MenuConfig()
             item = config.get_item_by_id("video_convert")
             if item: self.tool_name = item.get("name", self.tool_name)
        except: pass

        super().__init__(title=self.tool_name, width=600, height=660, icon_name="video_convert")
        
        self.demo_mode = demo
        self.target_path = target_path
        
        if demo:
            self.selection = []
            self.files = []
        else:
            self.selection = get_selection_from_explorer(target_path)
            
            if not self.selection:
                self.selection = [target_path]
                
            # Filter video files
            video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
            self.files = [Path(p) for p in self.selection if Path(p).suffix.lower() in video_exts]
            
            if not self.files:
                messagebox.showerror(t("common.error"), t("video_convert_gui.no_video_selected"))
                self.destroy()
                return

        self.var_new_folder = ctk.BooleanVar(value=True) # Default ON
        self.cancel_flag = False  # Cancel pattern for long FFmpeg encoding
        self.current_process = None  # Track running FFmpeg process
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)


    def create_widgets(self):
        # 1. Header
        self.add_header(f"{self.tool_name} ({len(self.files)})", font_size=20)
        
        # 2. File List
        from utils.gui_lib import FileListFrame
        self.file_scroll = FileListFrame(self.main_frame, self.files, height=180)
        self.file_scroll.pack(fill="x", padx=20, pady=(0, 10))
        
        # 3. Parameters (2-Column Grid)
        param_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        param_frame.pack(fill="x", padx=20, pady=5)
        param_frame.grid_columnconfigure(0, weight=1)
        param_frame.grid_columnconfigure(1, weight=1)
        
        # Left Column: Format & Scale
        left_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text=t("video_convert_gui.format_label"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        
        # Check for NVENC
        self.has_nvenc = self.check_nvenc()
        formats = []
        if self.has_nvenc:
            formats.append("MP4 (H.264 NVENC)")
            
        formats.extend([
            "MP4 (H.264 High)", 
            "MP4 (H.264 Low/Proxy)", 
            "MOV (ProRes 422)", 
            "MOV (ProRes 4444)", 
            "MOV (DNxHD)",
            "MKV (Copy Stream)",
            "GIF (High Quality)"
        ])
        
        self.fmt_var = ctk.StringVar(value=formats[0])
        self.fmt_combo = ctk.CTkComboBox(left_frame, variable=self.fmt_var, values=formats, command=self.on_fmt_change)
        self.fmt_combo.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(left_frame, text=t("video_convert_gui.scale_label"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.scale_var = ctk.StringVar(value="100%")
        self.scale_combo = ctk.CTkComboBox(left_frame, variable=self.scale_var, values=["100%", "50%", "25%", "Custom Width"], command=self.on_scale_change)
        self.scale_combo.pack(fill="x", pady=(0, 5))
        
        self.entry_width = ctk.CTkEntry(left_frame, placeholder_text=t("video_convert_gui.width_placeholder"))
        
        # Right Column: Quality
        right_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.lbl_crf = ctk.CTkLabel(right_frame, text=t("video_convert_gui.quality_crf"), font=ctk.CTkFont(weight="bold"))
        self.lbl_crf.pack(anchor="w", pady=(5, 2))
        
        range_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        range_frame.pack(fill="x")
        
        self.crf_var = tk.IntVar(value=23)
        self.slider_crf = ctk.CTkSlider(range_frame, from_=0, to=51, number_of_steps=51, variable=self.crf_var, command=self.update_crf_label)
        self.slider_crf.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.lbl_crf_val = ctk.CTkLabel(range_frame, text="23", width=30)
        self.lbl_crf_val.pack(side="right")
        
        ctk.CTkLabel(right_frame, text=t("video_convert_gui.quality_hint"), text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(2, 0))

        # 4. Footer
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", padx=20, pady=(20, 5))
        
        self.progress = ctk.CTkProgressBar(footer_frame, height=10)
        self.progress.pack(fill="x", pady=(0, 15))
        self.progress.set(0)
        
        # Options
        opt_row = ctk.CTkFrame(footer_frame, fg_color="transparent")
        opt_row.pack(fill="x", pady=(0, 15))
        
        ctk.CTkCheckBox(opt_row, text=t("video_convert_gui.save_to_folder"), variable=self.var_new_folder).pack(side="left", padx=(0, 20))
        self.var_delete_org = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_row, text=t("image_convert_gui.delete_original"), variable=self.var_delete_org, text_color="#E74C3C").pack(side="left")

        # Buttons
        btn_row = ctk.CTkFrame(footer_frame, fg_color="transparent")
        btn_row.pack(fill="x")
        
        self.btn_cancel = ctk.CTkButton(btn_row, text=t("common.cancel"), height=45, fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90"), command=self.cancel_or_close)
        self.btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_convert = ctk.CTkButton(btn_row, text=t("video_convert_gui.start_conversion"), height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_convert)
        self.btn_convert.pack(side="left", fill="x", expand=True, padx=(0, 0))
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text=t("video_convert_gui.ready_to_convert"), text_color="gray", font=("", 11))
        self.lbl_status.pack(pady=(0, 5))

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
            self.entry_width.pack(fill="x", pady=(0, 5))
            self.adjust_window_size()
        else:
            self.entry_width.pack_forget()
            self.adjust_window_size()

    def check_nvenc(self):
        """Check if NVIDIA NVENC encoder is available."""
        try:
            ffmpeg = get_ffmpeg()
            # Run ffmpeg -encoders and check for h264_nvenc
            res = subprocess.run([ffmpeg, "-encoders"], capture_output=True, text=True, errors="ignore")
            # Look for "V..... h264_nvenc"
            return "h264_nvenc" in res.stdout
        except:
            return False

    def cancel_or_close(self):
        """Cancel processing if running, otherwise close window."""
        if self.btn_convert.cget("state") == "disabled":
            self.cancel_flag = True
            self.lbl_status.configure(text=t("video_convert_gui.cancelling"))
            # Terminate running FFmpeg process if exists
            if self.current_process and self.current_process.poll() is None:
                try:
                    self.current_process.terminate()
                except:
                    pass
        else:
            self.destroy()

    def start_convert(self):
        # CRITICAL: Reset cancel flag before each run
        self.cancel_flag = False
        self.current_process = None
        
        self.btn_convert.configure(state="disabled", text=t("video_convert_gui.converting"))
        self.btn_cancel.configure(fg_color="#C0392B", hover_color="#E74C3C", text_color="white")
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
            # Check cancel flag before each file
            if self.cancel_flag:
                break
                
            self.lbl_status.configure(text=t("video_convert_gui.processing_file", current=i+1, total=total, name=path.name))
            self.progress.set(i / total)
            
            try:
                cmd = [ffmpeg, "-i", str(path)]
                
                # Output filename
                suffix = path.suffix
                if "MP4" in fmt: suffix = ".mp4"
                elif "MOV" in fmt: suffix = ".mov"
                elif "MKV" in fmt: suffix = ".mkv"
                elif "GIF" in fmt: suffix = ".gif"
                
                # Determine output directory
                if self.var_new_folder.get():
                    base_dir = path.parent / "Converted"
                    if base_dir not in out_dir_cache:
                        safe_dir = base_dir if not base_dir.exists() else get_safe_path(base_dir)
                        safe_dir.mkdir(exist_ok=True)
                        out_dir_cache[base_dir] = safe_dir
                    out_dir = out_dir_cache[base_dir]
                    out_name = f"{path.stem}{suffix}" 
                else:
                    out_dir = path.parent
                    out_name = f"{path.stem}_conv{suffix}"
                
                output_path = get_safe_path(out_dir / out_name)
                
                # Video Codec
                if "NVENC" in fmt:
                    # NVENC doesn't support CRF in the same way, usually uses -cq or -qp.
                    # Simplified: -c:v h264_nvenc -cq <crf> -preset p7
                    # 18(High) -> roughly 19-20? 
                    # Let's map CRF to CQ roughly.
                    cmd.extend(["-c:v", "h264_nvenc", "-cq", str(crf), "-preset", "p6", "-c:a", "aac"])
                    
                elif "H.264" in fmt:
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
                    
                elif "GIF" in fmt:
                    # High quality GIF generation
                    # 1. Palette gen
                    # 2. Palette use
                    # We need a complex filter.
                    
                    # Determining Scale first to inject into filter
                    scale_filter = ""
                    if scale == "50%": scale_filter = ",scale=iw/2:-1"
                    elif scale == "25%": scale_filter = ",scale=iw/4:-1"
                    elif scale == "Custom Width":
                        try:
                            w = int(self.entry_width.get())
                            scale_filter = f",scale={w}:-1"
                        except: pass
                    
                    # Full filter chain
                    # fps=15 (good balance), flags=lanczos
                    filter_str = f"fps=15{scale_filter}:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
                    
                    cmd.extend(["-vf", filter_str, "-c:v", "gif"])
                
                # Scaling for non-GIF (GIF handled scaling in filter above)
                if "GIF" not in fmt:
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
                
                # Check cancel before running FFmpeg
                if self.cancel_flag:
                    break
                
                # Run without startupinfo for now to debug 0xC0000135
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.current_process.wait()
                
                if self.cancel_flag:
                    break
                    
                if self.current_process.returncode != 0:
                    _, stderr = self.current_process.communicate()
                    raise subprocess.CalledProcessError(self.current_process.returncode, cmd, stderr=stderr.decode() if stderr else "")
                
                self.current_process = None
                success += 1
                
                # Handle Deletion
                if self.var_delete_org.get() and path.exists():
                    try:
                        import os
                        os.remove(path)
                    except Exception as e:
                        errors.append(f"Delete failed: {path.name} ({str(e)})")
                
            except subprocess.CalledProcessError as e:
                errors.append(f"{path.name}: {e.stderr}")
            except Exception as e:
                errors.append(f"{path.name}: {str(e)}")
                
        self.progress.set(1.0)
        self.btn_convert.configure(state="normal", text=t("video_convert_gui.start_conversion"))
        self.btn_cancel.configure(fg_color="transparent", hover_color=None, text_color="gray")
        
        if self.cancel_flag:
            self.lbl_status.configure(text=t("common.cancelled"))
            messagebox.showinfo(t("common.cancelled"), t("video_convert_gui.conversion_cancelled"))
        else:
            self.lbl_status.configure(text=t("video_convert_gui.conversion_complete"))
            
            msg = f"Converted {success}/{total} files."
            if errors:
                msg += "\n\n" + t("common.errors") + ":\n" + "\n".join(errors[:5])
                messagebox.showwarning(t("dialogs.operation_complete"), msg)
            else:
                messagebox.showinfo(t("common.success"), msg)
                self.destroy()

    def on_closing(self):
        self.destroy()

def run_gui(target_path):
    app = VideoConvertGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    # Demo mode for screenshots
    if "--demo" in sys.argv:
        app = VideoConvertGUI(None, demo=True)
        app.mainloop()
    elif len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # Mutex - ensure only one GUI window opens
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("video_convert", anchor, timeout=0.2) is None:
            sys.exit(0)
        
        run_gui(anchor)
    else:
        run_gui(str(Path.home() / "Videos"))

