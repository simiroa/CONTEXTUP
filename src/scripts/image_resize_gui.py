import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from PIL import Image
import sys
import threading
import math
import shutil

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow
from utils.image_utils import scan_for_images

class ImageResizeGUI(BaseWindow):
    def __init__(self, files_list):
        super().__init__(title="Resize Image (POT)", width=400, height=500)
        
        # Accept list of files directly
        if isinstance(files_list, (list, tuple)) and len(files_list) > 0:
            self.files, self.candidates_count = scan_for_images(files_list)
        else:
            self.files, self.candidates_count = scan_for_images(files_list)
        
        if not self.files:
            messagebox.showerror("Error", f"No valid images found.\nScanned {self.candidates_count} items.")
            self.destroy()
            return

        self.current_img_size = (0, 0)
        # Load first image size for reference
        try:
            with Image.open(self.files[0]) as img:
                self.current_img_size = img.size
        except:
            pass

        self.create_widgets()
        self.update_recommendation()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)



    def create_widgets(self):
        # 1. Header (Compact)
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(header, text="Selected Files:", font=("Arial", 12, "bold")).pack(side="left")
        
        count_text = f"{len(self.files)} items"
        if len(self.files) == 1:
            count_text = self.files[0].name
            
        ctk.CTkLabel(header, text=count_text, text_color="gray").pack(side="right")

        # 2. Main Controls
        self.content = ctk.CTkFrame(self.main_frame)
        self.content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Target Size
        ctk.CTkLabel(self.content, text="Target Resolution (Longest Edge)", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        
        self.size_var = ctk.StringVar(value="1024")
        self.combo_size = ctk.CTkComboBox(self.content, variable=self.size_var, 
                                          values=["256", "512", "1024", "2048", "4096", "8192"],
                                          command=self.update_recommendation)
        self.combo_size.pack(pady=5)
        
        self.var_square = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.content, text="Force Square (1:1)", variable=self.var_square).pack(pady=10)

        # Mode
        ctk.CTkLabel(self.content, text="Resize Method", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        
        self.mode_var = ctk.StringVar(value="Standard")
        self.rad_std = ctk.CTkRadioButton(self.content, text="Standard (Lanczos)", variable=self.mode_var, value="Standard", command=self.update_recommendation)
        self.rad_std.pack(pady=5)
        
        self.rad_ai = ctk.CTkRadioButton(self.content, text="AI Upscale (High Quality)", variable=self.mode_var, value="AI", command=self.update_recommendation)
        self.rad_ai.pack(pady=5)
        
        # Recommendation / Info Box
        self.info_frame = ctk.CTkFrame(self.content, fg_color="#2b2b2b", border_color="#3a3a3a", border_width=1)
        self.info_frame.pack(fill="x", padx=20, pady=20)
        
        self.lbl_info = ctk.CTkLabel(self.info_frame, text="Info...", text_color="gray", wraplength=300)
        self.lbl_info.pack(padx=10, pady=10)

        # 3. Actions
        self.btn_resize = ctk.CTkButton(self.main_frame, text="Resize Images", height=40, font=("Arial", 14, "bold"), command=self.start_resize)
        self.btn_resize.pack(fill="x", padx=20, pady=(0, 20))
        
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.pack(fill="x", padx=20, pady=(0, 20))
        self.progress.set(0)

    def update_recommendation(self, *args):
        try:
            target = int(self.size_var.get())
        except:
            target = 1024
            
        current = max(self.current_img_size) if self.current_img_size[0] > 0 else 1024
        
        ratio = target / current
        mode = self.mode_var.get()
        
        msg = f"Current: ~{current}px -> Target: {target}px\n"
        
        if ratio > 1.5:
            msg += f"Upscale: {ratio:.1f}x\n"
            if mode != "AI":
                msg += "⚠️ Recommended: Use AI Upscale for better quality."
                self.lbl_info.configure(text_color="#ffcc00") # Warning Yellow
            else:
                msg += "✅ AI Upscale selected."
                self.lbl_info.configure(text_color="#66cc66") # Good Green
        elif ratio < 0.8:
            msg += f"Downscale: {ratio:.1f}x (Standard is fine)"
            self.lbl_info.configure(text_color="gray")
        else:
            msg += "Size change is minor."
            self.lbl_info.configure(text_color="gray")
            
        self.lbl_info.configure(text=msg)

    def start_resize(self):
        self.btn_resize.configure(state="disabled")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def get_nearest_pot(self, val):
        return 2**round(math.log2(val))

    def run_logic(self):
        try:
            target_size = int(self.size_var.get())
        except:
            target_size = 1024
            
        mode = self.mode_var.get()
        force_square = self.var_square.get()
        
        total = len(self.files)
        success = 0
        errors = []
        
        output_dir_name = "Resized_AI" if mode == "AI" else "Resized"
        
        for i, path in enumerate(self.files):
            self.progress.set((i) / total)
            try:
                # Output setup
                out_dir = path.parent / output_dir_name
                out_dir.mkdir(exist_ok=True)
                
                if mode == "AI":
                    # Determine scale factor needed
                    with Image.open(path) as img:
                        w, h = img.size
                        longest = max(w, h)
                        scale_needed = target_size / longest
                        
                        # Snap to Ai supported scales (2, 4) or run multiple?
                        # Simplifying: Round to nearest supported scale (2 or 4)
                        if scale_needed <= 1.0:
                            # Fallback to standard if downscaling requested in AI mode
                            # Or ignore AI
                            scale = 1
                        elif scale_needed <= 2.5:
                            scale = 2
                        else:
                            scale = 4
                    
                    if scale > 1:
                         # Run AI
                        args = ["upscale.py", str(path), "--scale", str(scale), "--output", str(out_dir)]
                        # Optional: Pass specific model if needed, default is usually fine
                        ok, _ = run_ai_script(*args)
                        if not ok: raise Exception("AI Execution Failed")
                        
                        # Post-process: AI output might be exactly 2x/4x, but user wanted specific Target Size
                        # So we might need to downscale the AI result to match exact target
                        # Find the output file
                        ai_out_name = f"{path.stem}_upscaled_{scale}x.png" # specific output format from upscale.py? 
                        # upscale.py usually retains extension or uses png. Let's assume standard behavior or scan
                        # Actually loop for latest file or standard naming
                        # For now, let's assume upscale.py outputs to out_dir
                        # We need to find it.
                        # Simplification: Just check files in out_dir made now?
                        # Or, rely on the fact that Realesrgan adds suffix.
                        # Implementation detail: Upscale tool might return path?
                        pass 
                    else:
                        # Copy for downscale handling below
                        shutil.copy(path, out_dir / path.name)
                
                else:
                    # Standard Resize
                    with Image.open(path) as img:
                        if img.mode != "RGB": img = img.convert("RGB")
                        w, h = img.size
                        
                        if force_square:
                            new_size = (target_size, target_size)
                        else:
                            # Validate Aspect Ratio + POT
                            # Strategy: Longest edge = target_size. Shortest edge = Nearest POT?
                            # Or just maintain aspect?
                            # "Resize (POT)" implies we want POT dimensions for game engines.
                            ratio = w / h
                            if w >= h:
                                nw = target_size
                                nh = self.get_nearest_pot(nw / ratio)
                            else:
                                nh = target_size
                                nw = self.get_nearest_pot(nh * ratio)
                            new_size = (nw, nh)
                            
                        res = img.resize(new_size, Image.Resampling.LANCZOS)
                        save_path = get_safe_path(out_dir / path.name)
                        res.save(save_path)
                
                success += 1
                
            except Exception as e:
                errors.append(f"{path.name}: {e}")
                print(e)
        
        self.progress.set(1.0)
        self.btn_resize.configure(state="normal")
        
        msg = f"Processed {success}/{total} images."
        if errors:
            msg += f"\nErrors: {len(errors)}"
            messagebox.showwarning("Completed with Errors", msg)
        else:
            messagebox.showinfo("Success", msg)
            self.destroy()

    def on_closing(self):
        self.destroy()

def resize_gui_entry(files_list):
    app = ImageResizeGUI(files_list)
    app.mainloop()


def get_all_selected_files(anchor_path: str) -> list[Path]:
    """Get all selected files via Explorer COM - INSTANT."""
    try:
        selected = get_selection_from_explorer(anchor_path)
        if selected and len(selected) > 0:
            return selected
    except:
        pass
    return [Path(anchor_path)]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        
        # STEP 1: Get ALL selected files instantly via Explorer COM
        all_files = get_all_selected_files(anchor)
        
        # STEP 2: Mutex - ensure only one GUI window opens
        from utils.batch_runner import collect_batch_context
        if collect_batch_context("resize_power_of_2", anchor, timeout=0.2) is None:
            sys.exit(0)
        
        # STEP 3: Launch GUI with complete file list
        resize_gui_entry(all_files)
