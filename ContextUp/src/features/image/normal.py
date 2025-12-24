"""
Normal Map and Simple PBR Tools.
Provides utilities for normal map manipulation and legacy PBR generation.
"""
import sys
from pathlib import Path
from tkinter import messagebox

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # features/image -> src
sys.path.append(str(src_dir))

from core.logger import setup_logger
from utils.explorer import get_selection_from_explorer
from utils.gui_lib import BaseWindow
import customtkinter as ctk
from PIL import Image

logger = setup_logger("normal_tools")


def flip_normal_green(target_path, selection=None):
    """
    Flip Green channel of normal map (DirectX <-> OpenGL conversion).
    No GUI - instant execution with notification.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        messagebox.showerror("Error", "Required libraries (Pillow, NumPy) are missing. Please run setup.")
        return
    
    try:
        # Get selection
        if selection is None:
            selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [Path(target_path)]
        
        count = 0
        for path in selection:
            path = Path(path)
            if not path.exists():
                continue
                
            logger.info(f"Flipping green channel: {path}")
            
            img = Image.open(path)
            
            # Ensure RGB/RGBA
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
            
            arr = np.array(img)
            
            # Flip Green channel (index 1)
            arr[:, :, 1] = 255 - arr[:, :, 1]
            
            result = Image.fromarray(arr)
            out_path = path.parent / f"{path.stem}_flipped{path.suffix}"
            result.save(out_path)
            
            logger.info(f"Saved: {out_path}")
            count += 1
        
        messagebox.showinfo("Complete", f"Flipped {count} normal map(s).\nOutput: *_flipped.*")
        
    except Exception as e:
        logger.error(f"Normal flip failed: {e}", exc_info=True)
        messagebox.showerror("Error", f"Failed to flip normal: {e}")


class NormalStrengthGUI(BaseWindow):
    def __init__(self, target_path, selection=None):
        super().__init__(title="ContextUp Normal & Roughness Gen", width=450, height=700, icon_name="simple_pbr")
        
        # Handle selection
        if selection:
            self.files = selection
        else:
            self.files = get_selection_from_explorer(target_path) or [Path(target_path)]
            
        # Filter existing
        self.files = [Path(p) for p in self.files if Path(p).exists()]
        
        self.create_widgets()
        
    def create_widgets(self):
        # 0. Header (Standardized)
        self.add_header("Normal & Roughness Generator")
        
        # 1. Preview Area (New)
        self.preview_frame = ctk.CTkFrame(self.main_frame, height=250, fg_color="#2b2b2b")
        self.preview_frame.pack(fill="x", padx=10, pady=10)
        self.preview_frame.pack_propagate(False)
        
        self.lbl_preview = ctk.CTkLabel(self.preview_frame, text="Loading Preview...")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")
        
        # Load preview image (first file)
        self.preview_img_orig = None
        if self.files:
            try:
                img = Image.open(self.files[0]).convert('RGB')
                # Resize for performance/display
                aspect = img.height / img.width
                w = 300
                h = int(w * aspect)
                if h > 220: # Cap height
                    h = 220
                    w = int(h / aspect)
                self.preview_img_orig = img.resize((w, h), Image.Resampling.LANCZOS)
            except Exception as e:
                self.lbl_preview.configure(text=f"Preview Fail: {e}")

        # 2. Controls
        ctrl_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=15, pady=5)
        
        # Normal Strength
        ctk.CTkLabel(ctrl_frame, text="Normal Strength:", font=("", 12, "bold")).pack(anchor="w")
        
        n_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        n_row.pack(fill="x")
        self.lbl_norm_val = ctk.CTkLabel(n_row, text="1.0", width=30)
        self.lbl_norm_val.pack(side="right")
        self.slider_normal = ctk.CTkSlider(n_row, from_=0.1, to=5.0, number_of_steps=49, command=self.update_preview)
        self.slider_normal.pack(fill="x", padx=(0, 5))
        self.slider_normal.set(1.0)
        
        # Roughness Contrast
        ctk.CTkLabel(ctrl_frame, text="Roughness Contrast:", font=("", 12, "bold")).pack(anchor="w", pady=(10, 0))
        
        r_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        r_row.pack(fill="x")
        self.lbl_rough_val = ctk.CTkLabel(r_row, text="1.0", width=30)
        self.lbl_rough_val.pack(side="right")
        self.slider_rough = ctk.CTkSlider(r_row, from_=0.5, to=2.0, number_of_steps=30, command=self.update_preview)
        self.slider_rough.pack(fill="x", padx=(0, 5))
        self.slider_rough.set(1.0)
        
        # Info
        ctk.CTkLabel(self.main_frame, text="Preview shows Normal map only.", 
                     text_color="gray", font=("", 10)).pack(pady=(5, 10))
        
        # Buttons
        self.btn_run = ctk.CTkButton(self.main_frame, text=f"Save {len(self.files)} Maps", height=40, 
                                     fg_color="#00b894", hover_color="#00cec9",
                                     font=("", 13, "bold"), command=self.start_gen)
        self.btn_run.pack(fill="x", padx=20, pady=10)
        
        # Initial trigger
        if self.preview_img_orig:
            self.update_preview()

    def update_preview(self, _=None):
        # Update Labels
        n_str = self.slider_normal.get()
        r_con = self.slider_rough.get()
        self.lbl_norm_val.configure(text=f"{n_str:.1f}")
        self.lbl_rough_val.configure(text=f"{r_con:.1f}")
        
        # Generate Preview
        if self.preview_img_orig:
            # We only show Normal map in preview for now? Or side-by-side?
            # Let's show Normal map as it's the main visual change
            norm, _ = self.generate_maps(self.preview_img_orig, n_str, r_con)
            
            # Convert to CTkImage
            ctk_img = ctk.CTkImage(light_image=norm, dark_image=norm, size=norm.size)
            self.lbl_preview.configure(image=ctk_img, text="")

    def generate_maps(self, img_pil, strength, contrast):
        """Core logic: Returns (normal_pil, roughness_pil)"""
        import numpy as np
        from PIL import ImageEnhance
        
        # Convert to arrays
        if img_pil.mode != 'L':
            gray = img_pil.convert('L')
        else:
            gray = img_pil
            
        # === Roughness ===
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(gray)
            img_con = enhancer.enhance(contrast)
        else:
            img_con = gray
            
        arr = np.array(img_con, dtype=np.float32) / 255.0
        rough_arr = (1.0 - arr) * 255
        rough_img = Image.fromarray(rough_arr.astype(np.uint8))
        
        # === Normal ===
        # Use SCIPY if available, else numpy gradient
        arr_n = np.array(gray, dtype=np.float32) / 255.0
        
        try:
            from scipy.ndimage import sobel
            dx = sobel(arr_n, axis=1)
            dy = sobel(arr_n, axis=0)
        except ImportError:
            dx = np.gradient(arr_n, axis=1)
            dy = np.gradient(arr_n, axis=0)
            
        dx *= strength
        dy *= strength
        dz = np.ones_like(arr_n)
        
        length = np.sqrt(dx*dx + dy*dy + dz*dz)
        np.place(length, length==0, 1)
        
        nx = (dx / length + 1) * 0.5 * 255
        ny = (dy / length + 1) * 0.5 * 255
        nz = (dz / length + 1) * 0.5 * 255
        
        norm_arr = np.stack([nx, ny, nz], axis=-1).astype(np.uint8)
        norm_img = Image.fromarray(norm_arr)
        
        return norm_img, rough_img

    def start_gen(self):
        try:
            import numpy
            from PIL import Image
        except ImportError:
            messagebox.showerror("Error", "Required libraries (Pillow, NumPy) are missing.")
            return

        self.btn_run.configure(state="disabled", text="Saving...")
        import threading
        threading.Thread(target=self.run_process, daemon=True).start()
        
    def run_process(self):
        count = 0
        errors = []
        
        n_str = self.slider_normal.get()
        r_con = self.slider_rough.get()
        
        for path in self.files:
            try:
                img = Image.open(path)
                norm, rough = self.generate_maps(img, n_str, r_con)
                
                norm.save(path.parent / f"{path.stem}_normal.png")
                rough.save(path.parent / f"{path.stem}_roughness.png")
                count += 1
            except Exception as e:
                errors.append(f"{path.name}: {e}")
                
        self.main_frame.after(0, lambda: self._finish(count, errors))
        
    def _finish(self, count, errors):
        self.btn_run.configure(state="normal", text=f"Save {len(self.files)} Maps")
        if errors:
            messagebox.showwarning("Finished with Errors", "\n".join(errors))
        else:
            messagebox.showinfo("Success", f"Saved maps for {count} files.")
            self.destroy()

def generate_simple_normal_roughness(target_path, selection=None):
    """Launch GUI for generation."""
    try:
        from utils.gui_lib import BaseWindow
        import customtkinter as ctk
        
        app = NormalStrengthGUI(target_path, selection)
        app.mainloop()
        
    except Exception as e:
        # Fallback if GUI fails? Or just show error
        messagebox.showerror("Error", f"Failed to launch GUI: {e}")


if __name__ == "__main__":
    # Test entry point
    if len(sys.argv) > 2:
        action = sys.argv[1]
        path = sys.argv[2]
        
        if action == "flip":
            flip_normal_green(path)
        elif action == "simple":
            generate_simple_normal_roughness(path)
    else:
        print("Usage: python normal_tools.py <flip|simple> <path>")
