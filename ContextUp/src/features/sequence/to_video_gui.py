"""
Sequence to Video GUI
Convert image sequences to video files using FFmpeg.
"""
import sys
import subprocess
import threading
import re
from pathlib import Path
from PIL import Image

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/video -> src
sys.path.append(str(src_dir))


def main():
    """Main entry - deferred imports for fast startup."""
    import customtkinter as ctk
    from tkinter import messagebox
    
    from utils.gui_lib import BaseWindow, THEME_BORDER, THEME_CARD, THEME_BTN_PRIMARY, THEME_BTN_HOVER
    from utils.files import get_safe_path
    from utils.i18n import t

    class SequenceToVideoGUI(BaseWindow):
        def __init__(self, target_path):
            super().__init__(title="ContextUp Sequence to Video", width=500, height=700, icon_name="sequence_to_video")
            
            self.target_path = Path(target_path)
            self.folder = self.target_path.parent if self.target_path.is_file() else self.target_path
            
            self.detect_sequence()
            
            if self.frame_count < 2:
                messagebox.showerror(t("common.error"), "Not a sequence (single file detected).")
                self.destroy()
                return

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
                # Find ALL number groups and use the LAST one as sequence number
                all_matches = list(re.finditer(r"(\d+)", ref))
                if all_matches:
                    match = all_matches[-1]  # Use last number group as sequence number
                    padding = len(match.group(1))
                    prefix = ref[:match.start()]
                    suffix = ref[match.end():]
                    self.guess_pattern = f"{prefix}%0{padding}d{suffix}"
                    self.start_num = int(match.group(1))
                    self.seq_name = prefix.strip("._-") or self.folder.name
                
                # Get resolution from first image
                try:
                    with Image.open(self.seq_files[0]) as img:
                        self.img_width, self.img_height = img.size
                        self.img_res = f"{self.img_width} x {self.img_height}"
                except Exception as e:
                    self.img_res = "Unknown Resolution"
                
                # Get Range (use last number group as sequence number)
                try:
                    first_matches = list(re.finditer(r"(\d+)", img_files[0]))
                    last_matches = list(re.finditer(r"(\d+)", img_files[-1]))
                    if first_matches and last_matches:
                        first_num = first_matches[-1].group(1)  # Last number group
                        last_num = last_matches[-1].group(1)    # Last number group
                        self.seq_range = f"{first_num} - {last_num}"
                    else:
                        self.seq_range = "N/A"
                except:
                    self.seq_range = "N/A"

            else:
                self.seq_files = []
                self.img_res = "N/A"
                self.seq_range = "N/A"

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
            
            self.btn_cancel = ctk.CTkButton(btn_row, text="Cancel", height=45, fg_color="transparent", 
                                            border_width=1, border_color=THEME_BORDER, text_color=("gray10", "gray90"), command=self.destroy)
            self.btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            self.btn_run = ctk.CTkButton(btn_row, text="Create Video", height=45, 
                                        font=ctk.CTkFont(size=14, weight="bold"), 
                                        fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER,
                                        command=self.start_conversion)
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
            
            # Info Card (Replaces File List)
            info_card = ctk.CTkFrame(body_frame, corner_radius=10)
            # Actually let's use a darker card color if available, or just transparent with border
            # Checking imports... THEME_BTN_PRIMARY is imported. Let's use standard card look.
            # We don't have THEME_CARD imported, let's just use "gray10" or similar for dark premium feel
            info_card.configure(fg_color=THEME_CARD, border_width=1, border_color=THEME_BORDER)
            info_card.pack(fill="x", pady=(0, 20))
            
            # Inner Grid
            info_card.grid_columnconfigure(1, weight=1)
            info_card.grid_columnconfigure(3, weight=1)
            
            # Row 1: Range & Count
            ctk.CTkLabel(info_card, text="Range:", text_color="gray").grid(row=0, column=0, padx=(15, 5), pady=(15, 5), sticky="w")
            ctk.CTkLabel(info_card, text=self.seq_range, font=("", 12, "bold")).grid(row=0, column=1, padx=0, pady=(15, 5), sticky="w")
            
            ctk.CTkLabel(info_card, text="Count:", text_color="gray").grid(row=0, column=2, padx=(15, 5), pady=(15, 5), sticky="w")
            ctk.CTkLabel(info_card, text=f"{self.frame_count} frames", font=("", 12, "bold")).grid(row=0, column=3, padx=(0, 15), pady=(15, 5), sticky="w")
            
            # Row 2: Resolution & Type
            ctk.CTkLabel(info_card, text="Resolution:", text_color="gray").grid(row=1, column=0, padx=(15, 5), pady=(5, 15), sticky="w")
            ctk.CTkLabel(info_card, text=self.img_res, font=("", 12, "bold")).grid(row=1, column=1, padx=0, pady=(5, 15), sticky="w")
            
            # You could add file type here if needed
            ext = self.seq_files[0].suffix if self.seq_files else ""
            ctk.CTkLabel(info_card, text="Type:", text_color="gray").grid(row=1, column=2, padx=(15, 5), pady=(5, 15), sticky="w")
            ctk.CTkLabel(info_card, text=ext.upper(), font=("", 12, "bold")).grid(row=1, column=3, padx=(0, 15), pady=(5, 15), sticky="w")
            
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
            
            # Row 2: Format (MP4 / MOV)
            ctk.CTkLabel(content, text="Format:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=(0, 10), pady=10, sticky="w")
            
            self.var_format = ctk.StringVar(value="MP4")
            format_frame = ctk.CTkFrame(content, fg_color="transparent")
            format_frame.grid(row=2, column=1, padx=0, pady=10, sticky="ew")
            
            ctk.CTkRadioButton(format_frame, text="MP4 (H.264)", variable=self.var_format, value="MP4", 
                              fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER,
                              command=self.on_format_change).pack(side="left", padx=(0, 20))
            ctk.CTkRadioButton(format_frame, text="MOV (ProRes)", variable=self.var_format, value="MOV",
                              fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER,
                              command=self.on_format_change).pack(side="left")
            
            # Dynamic Options Container
            self.options_container = ctk.CTkFrame(content, fg_color="transparent")
            self.options_container.grid(row=3, column=0, columnspan=2, padx=0, pady=5, sticky="ew")
            self.options_container.grid_columnconfigure(1, weight=1)
            
            # MP4 Options Frame (Bitrate Slider)
            self.mp4_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
            
            ctk.CTkLabel(self.mp4_frame, text="Bitrate:", text_color="gray").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
            
            bitrate_inner = ctk.CTkFrame(self.mp4_frame, fg_color="transparent")
            bitrate_inner.grid(row=0, column=1, padx=0, pady=5, sticky="ew")
            bitrate_inner.grid_columnconfigure(0, weight=1)
            self.mp4_frame.grid_columnconfigure(1, weight=1)
            
            self.var_bitrate = ctk.IntVar(value=20)  # Default 20 Mbps
            self.slider_bitrate = ctk.CTkSlider(bitrate_inner, from_=5, to=100, variable=self.var_bitrate,
                                                 command=self.on_settings_change)
            self.slider_bitrate.grid(row=0, column=0, padx=(0, 10), sticky="ew")
            
            self.lbl_bitrate = ctk.CTkLabel(bitrate_inner, text="20 Mbps", width=70)
            self.lbl_bitrate.grid(row=0, column=1, sticky="e")
            
            # MOV Options Frame (ProRes Preset + Alpha)
            self.mov_frame = ctk.CTkFrame(self.options_container, fg_color="transparent")
            
            ctk.CTkLabel(self.mov_frame, text="Preset:", text_color="gray").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
            
            self.prores_presets = ["ProRes 422", "ProRes 422 HQ", "ProRes 4444", "ProRes 4444 XQ"]
            self.var_prores = ctk.StringVar(value="ProRes 422 HQ")
            ctk.CTkOptionMenu(self.mov_frame, variable=self.var_prores, values=self.prores_presets,
                             command=self.on_settings_change).grid(row=0, column=1, padx=0, pady=5, sticky="ew")
            self.mov_frame.grid_columnconfigure(1, weight=1)
            
            self.var_alpha = ctk.BooleanVar(value=False)
            self.chk_alpha = ctk.CTkCheckBox(self.mov_frame, text="Include Alpha Channel", variable=self.var_alpha,
                                             command=self.on_settings_change)
            self.chk_alpha.grid(row=1, column=0, columnspan=2, padx=0, pady=5, sticky="w")
            
            # Row 4: Skip Frame checkbox
            self.var_skip = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(content, text="Skip First Frame (Unreal Engine Fix)", variable=self.var_skip).grid(row=4, column=0, columnspan=2, padx=0, pady=(10, 5), sticky="w")
            
            # Row 5: Estimated Size
            size_frame = ctk.CTkFrame(content, fg_color=THEME_CARD, corner_radius=8)
            size_frame.grid(row=5, column=0, columnspan=2, padx=0, pady=(10, 0), sticky="ew")
            
            ctk.CTkLabel(size_frame, text="📦 Estimated Size:", text_color="gray").pack(side="left", padx=(10, 5), pady=8)
            self.lbl_estimated_size = ctk.CTkLabel(size_frame, text="~0 MB", font=ctk.CTkFont(weight="bold"))
            self.lbl_estimated_size.pack(side="left", padx=5, pady=8)
            
            # Initialize with MP4 options visible
            self.on_format_change()
            
        def on_format_change(self, *args):
            """Toggle between MP4 and MOV options."""
            for widget in self.options_container.winfo_children():
                widget.grid_forget()
            
            if self.var_format.get() == "MP4":
                self.mp4_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
            else:
                self.mov_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
            
            self.update_estimated_size()
        
        def on_settings_change(self, *args):
            """Update UI when settings change."""
            # Update bitrate label
            bitrate = self.var_bitrate.get()
            self.lbl_bitrate.configure(text=f"{bitrate} Mbps")
            self.update_estimated_size()
        
        def update_estimated_size(self):
            """Calculate and display estimated file size."""
            try:
                fps = int(self.entry_fps.get())
            except:
                fps = 30
            
            duration_sec = self.frame_count / fps
            pixels = getattr(self, 'img_width', 1920) * getattr(self, 'img_height', 1080)
            
            if self.var_format.get() == "MP4":
                # H.264: use bitrate directly
                bitrate_mbps = self.var_bitrate.get()
                size_mb = (bitrate_mbps * duration_sec) / 8
            else:
                # ProRes: estimate based on preset and resolution
                preset = self.var_prores.get()
                has_alpha = self.var_alpha.get()
                
                # ProRes bitrates per frame at 1920x1080 (MB/frame approximation)
                prores_rates = {
                    "ProRes 422": 0.06,
                    "ProRes 422 HQ": 0.1,
                    "ProRes 4444": 0.15,
                    "ProRes 4444 XQ": 0.22
                }
                
                base_rate = prores_rates.get(preset, 0.1)
                # Scale by resolution
                scale = pixels / (1920 * 1080)
                rate = base_rate * scale
                
                # Alpha adds ~25% more
                if has_alpha and "4444" in preset:
                    rate *= 1.25
                
                size_mb = rate * self.frame_count
            
            # Format output
            if size_mb >= 1000:
                size_str = f"~{size_mb / 1000:.1f} GB"
            else:
                size_str = f"~{size_mb:.0f} MB"
            
            self.lbl_estimated_size.configure(text=size_str)


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
                    
                start_num = self.start_num + (1 if self.var_skip.get() else 0)
                
                # Output setup based on format
                output_name = self.folder.name
                ffmpeg_args = []
                
                if self.var_format.get() == "MP4":
                    # H.264 with bitrate control
                    bitrate = self.var_bitrate.get()
                    output_name += f"_{bitrate}mbps.mp4"
                    ffmpeg_args = [
                        "-c:v", "libx264", 
                        "-pix_fmt", "yuv420p", 
                        "-b:v", f"{bitrate}M",
                        "-preset", "medium"
                    ]
                else:
                    # ProRes MOV
                    preset = self.var_prores.get()
                    has_alpha = self.var_alpha.get()
                    
                    # ProRes profiles: 0=Proxy, 1=LT, 2=422, 3=422HQ, 4=4444, 5=4444XQ
                    prores_profiles = {
                        "ProRes 422": ("2", "yuv422p10le", "_422"),
                        "ProRes 422 HQ": ("3", "yuv422p10le", "_422hq"),
                        "ProRes 4444": ("4", "yuva444p10le" if has_alpha else "yuv444p10le", "_4444"),
                        "ProRes 4444 XQ": ("5", "yuva444p10le" if has_alpha else "yuv444p10le", "_4444xq"),
                    }
                    
                    profile, pix_fmt, suffix = prores_profiles.get(preset, ("3", "yuv422p10le", "_422hq"))
                    if has_alpha and "4444" in preset:
                        suffix += "_alpha"
                    
                    output_name += f"{suffix}.mov"
                    ffmpeg_args = ["-c:v", "prores_ks", "-profile:v", profile, "-pix_fmt", pix_fmt]
                    
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
    if "--dev" in sys.argv:
        # Dev/Test mode - use dummy data to test GUI
        import customtkinter as ctk
        from tkinter import messagebox
        from utils.gui_lib import BaseWindow, THEME_BORDER, THEME_CARD
        from utils.files import get_safe_path
        from utils.i18n import t
        
        class DummySequenceToVideoGUI(BaseWindow):
            """Test GUI with dummy data."""
            def __init__(self):
                super().__init__(title="ContextUp Sequence to Video", width=500, height=700, icon_name="sequence_to_video")
                
                # Dummy sequence data
                self.folder = Path.cwd()
                self.frame_count = 150
                self.seq_name = "sc04_05_render"
                self.seq_range = "0001 - 0150"
                self.img_res = "1920 x 1080"
                self.img_width = 1920
                self.img_height = 1080
                self.guess_pattern = "sc04_05_render_%04d.png"
                self.start_num = 1
                self.seq_files = [Path(f"dummy_{i:04d}.png") for i in range(1, 151)]
                
                self.create_widgets()
                
            def create_widgets(self):
                # Deferred import of main() to get create_widgets
                SequenceToVideoGUI = main()
                # Borrow create_widgets from actual class
                SequenceToVideoGUI.create_widgets(self)
            
            def on_format_change(self, *args):
                SequenceToVideoGUI = main()
                SequenceToVideoGUI.on_format_change(self, *args)
            
            def on_settings_change(self, *args):
                SequenceToVideoGUI = main()
                SequenceToVideoGUI.on_settings_change(self, *args)
            
            def update_estimated_size(self):
                SequenceToVideoGUI = main()
                SequenceToVideoGUI.update_estimated_size(self)
            
            def start_conversion(self):
                messagebox.showinfo("Dev Mode", f"Format: {self.var_format.get()}\n" +
                                   (f"Bitrate: {self.var_bitrate.get()} Mbps" if self.var_format.get() == "MP4" 
                                    else f"Preset: {self.var_prores.get()}, Alpha: {self.var_alpha.get()}"))
        
        print("[DEV] Launching with dummy sequence data...")
        app = DummySequenceToVideoGUI()
        app.mainloop()
        
    elif len(sys.argv) > 1:
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
        print("Sequence to Video: No file provided. Use --dev for dummy test.")
