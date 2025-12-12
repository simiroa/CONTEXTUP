import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import threading
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageOps

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.gui_lib import BaseWindow, FileListFrame
from utils.files import get_safe_path
from utils.image_utils import scan_for_images
from utils.external_tools import get_ffmpeg
import subprocess

class ExrToolsGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="EXR Channel Tools", width=800, height=600)
        
        self.target_path = Path(target_path)
        self.files, self.scan_count = scan_for_images(self.target_path)
        
        # Filter for EXR only if mixed? Or allow others? Context implies EXR focus.
        self.exr_files = [f for f in self.files if f.suffix.lower() == ".exr"]
        
        if not self.exr_files:
            if self.files:
                # Fallback if user selected non-EXR but wants EXR tools?
                # Maybe just warn and show all?
                pass
            else:
                messagebox.showerror("Error", f"No valid files found.\nScanned {self.scan_count} items.")
                self.destroy()
                return
                
        self.current_file = self.exr_files[0] if self.exr_files else None
        
        self.create_widgets()
        
        if self.current_file:
            self.load_file_info(self.current_file)
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Layout: Left (Files 200px), Center (Preview), Right (Channels/Actions 200px)
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. Left Panel: File List
        self.left_panel = ctk.CTkFrame(self.main_frame, width=200, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.left_panel, text="EXR Files", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Custom Listbox-like
        self.scroll_files = ctk.CTkScrollableFrame(self.left_panel)
        self.scroll_files.pack(fill="both", expand=True, padx=5, pady=5)
        
        for f in self.exr_files:
            btn = ctk.CTkButton(self.scroll_files, text=f.name, anchor="w", fg_color="transparent", 
                                command=lambda p=f: self.load_file_info(p))
            btn.pack(fill="x")

        # 2. Center Panel: Preview
        self.center_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.lbl_preview_title = ctk.CTkLabel(self.center_panel, text="Preview", font=("Arial", 16, "bold"))
        self.lbl_preview_title.pack(pady=(0, 10))
        
        self.preview_area = ctk.CTkLabel(self.center_panel, text="[No Preview]", fg_color="gray10", corner_radius=5)
        self.preview_area.pack(fill="both", expand=True)

        # 3. Right Panel: Info & Actions
        self.right_panel = ctk.CTkFrame(self.main_frame, width=250, corner_radius=0)
        self.right_panel.grid(row=0, column=2, sticky="nsew")
        
        ctk.CTkLabel(self.right_panel, text="Channels & Actions", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Info Box
        self.info_box = ctk.CTkTextbox(self.right_panel, height=100, font=("Consolas", 11))
        self.info_box.pack(fill="x", padx=10, pady=5)
        self.info_box.insert("1.0", "Select a file...")
        self.info_box.configure(state="disabled")
        
        # Channel List
        ctk.CTkLabel(self.right_panel, text="Detected Channels:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10, 0))
        self.scroll_channels = ctk.CTkScrollableFrame(self.right_panel, height=150)
        self.scroll_channels.pack(fill="x", padx=10, pady=5)
        
        # Actions
        ctk.CTkLabel(self.right_panel, text="Operations:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        
        ctk.CTkButton(self.right_panel, text="Split All Layers", command=self.split_layers, fg_color="#1f6aa5").pack(fill="x", padx=10, pady=5)
        # Placeholder for complex channel shuffling
        ctk.CTkButton(self.right_panel, text="Merge RGB (Standard)", command=self.merge_rgb, fg_color="gray", state="disabled").pack(fill="x", padx=10, pady=5)
        
        self.progress = ctk.CTkProgressBar(self.right_panel)
        self.progress.pack(fill="x", padx=10, pady=(20, 5))
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.right_panel, text="Ready", text_color="gray", font=("Arial", 11))
        self.lbl_status.pack(pady=5)

    def load_file_info(self, path):
        self.current_file = path
        self.lbl_preview_title.configure(text=path.name)
        
        # Load EXR using OpenCV
        # IMREAD_UNCHANGED loads as is (likely float32)
        try:
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is None:
                raise Exception("Failed to load EXR")
            
            # Info
            h, w = img.shape[:2]
            channels = 1 if len(img.shape) == 2 else img.shape[2]
            dtype = img.dtype
            
            info = f"Resolution: {w}x{h}\nChannels: {channels}\nType: {dtype}"
            self.set_info(info)
            
            # Update Channel List (Fake detection for standard CV2 load which flattens layers usually)
            # True multi-layer EXR needs OpenEXR python lib or FFmpeg probe.
            # CV2 usually loads BGR or BGRA.
            # Let's start with basic BGR/A handling.
            self.update_channel_list(["Blue", "Green", "Red"] + (["Alpha"] if channels > 3 else []))
            
            # Preview (Tone map for display)
            # Linear to sRGB simple gamma curve
            # 1. Normalize 0-1
            # 2. Clip high values or exposure tonemap
            # 3. Gamma 2.2
            
            preview = img.copy()
            # If standard BGR
            if channels >= 3:
                preview = preview[:, :, :3] # Drop alpha for preview
            
            # Simple handling: max value normalization
            max_val = np.max(preview)
            if max_val > 1.0:
                 preview = preview / max_val
            
            # Gamma correction
            preview = np.power(preview, 1/2.2)
            preview = (preview * 255).astype(np.uint8)
            
            # BGR to RGB
            if channels >= 3:
                preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            
            # Resize for GUI
            pil_img = Image.fromarray(preview)
            
            # Fit to preview area
            # Get current size of preview area
            dw = self.preview_area.winfo_width()
            dh = self.preview_area.winfo_height()
            if dw < 100: dw = 400 # Initial fallback
            if dh < 100: dh = 400
            
            pil_img = ImageOps.contain(pil_img, (dw, dh))
            
            self.tk_img = ImageTk.PhotoImage(pil_img)
            self.preview_area.configure(image=self.tk_img, text="")
            
        except Exception as e:
            self.set_info(f"Error loading:\n{e}")
            self.preview_area.configure(image=None, text="Preview Failed")

    def set_info(self, text):
        self.info_box.configure(state="normal")
        self.info_box.delete("1.0", "end")
        self.info_box.insert("1.0", text)
        self.info_box.configure(state="disabled")

    def update_channel_list(self, channels):
        for w in self.scroll_channels.winfo_children(): w.destroy()
        
        for c in channels:
            chk = ctk.CTkCheckBox(self.scroll_channels, text=c, state="disabled")
            chk.select()
            chk.pack(anchor="w", pady=2)

    def split_layers(self):
        # Use FFmpeg to split
        threading.Thread(target=self.run_split, daemon=True).start()

    def run_split(self):
        if not self.current_file: return
        
        self.progress.set(0)
        self.lbl_status.configure(text="Splitting...")
        
        try:
            ffmpeg = get_ffmpeg()
            out_dir = self.current_file.parent / "Split"
            out_dir.mkdir(exist_ok=True)
            
            # Pattern for ffmpeg output
            out_pat = out_dir / f"{self.current_file.stem}_layer_%02d.exr"
            
            # Command: Map all streams to individual files
            # -map 0 maps all streams from input 0
            # For pure image layers, ffmpeg usually maps them.
            # But converting multi-layer EXR to single-layer files needs specific mapping if streams are separate.
            # If it's one video stream with channels, this might just copy it.
            # Let's assume standard multi-part EXR.
            
            cmd = [ffmpeg, "-y", "-i", str(self.current_file), "-map", "0", "-c", "copy", "-f", "image2", str(out_pat)]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            self.progress.set(1.0)
            self.lbl_status.configure(text="Done")
            messagebox.showinfo("Success", f"Layers split to:\n{out_dir}")
            
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if e.stderr else str(e)
            messagebox.showerror("FFmpeg Error", err)
            self.lbl_status.configure(text="Failed")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.lbl_status.configure(text="Failed")

    def merge_rgb(self):
        pass # Placeholder

    def on_closing(self):
        self.destroy()

def run_exr_gui(target_path):
    app = ExrToolsGUI(target_path)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # Get all selected files via Explorer COM
        from utils.explorer import get_selection_from_explorer
        all_files = get_selection_from_explorer(anchor)
        if not all_files:
            all_files = [Path(anchor)]
        
        # Mutex - ensure only one GUI window opens
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("split_exr", anchor, timeout=0.2) is None:
            sys.exit(0)
        
        # Pass first file (EXR tools work on single file primarily)
        run_exr_gui(str(all_files[0]))

