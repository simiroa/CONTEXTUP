"""
Image Compare GUI - Multi-image comparison with EXR channel support
"""
import sys
import threading
from pathlib import Path
from typing import List, Optional
import tkinter as tk
from tkinter import messagebox, filedialog

try:
    import customtkinter as ctk
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "CustomTkinter is required.")
    sys.exit(1)

from PIL import Image, ImageTk
import numpy as np

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from features.image.compare_core import (
    load_image, get_exr_channels, compute_diff, compute_ssim, 
    array_to_pil, create_side_by_side
)
from utils.i18n import t
from core.logger import setup_logger

logger = setup_logger("image_compare")


class ImageCompareGUI(ctk.CTk):
    """Image comparison GUI with EXR channel support."""
    
    def __init__(self, files: List[str]):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.title("Image Compare")
        self.geometry("900x650")
        self.minsize(700, 500)
        
        # State
        self.files = [Path(f) for f in files[:4]]  # Max 4 images
        self.images: List[Optional[np.ndarray]] = [None] * 4
        self.photo_images: List[Optional[ImageTk.PhotoImage]] = [None] * 4
        self.current_channel = "RGB"
        self.current_mode = "Side by Side"
        self.zoom_level = 1.0
        self.pan_offset = [0, 0]
        
        self._build_ui()
        self._load_initial_images()
        
        self.lift()
        self.focus_force()

    def _build_ui(self):
        # Top toolbar
        toolbar = ctk.CTkFrame(self, height=40)
        toolbar.pack(fill="x", padx=10, pady=(10, 5))
        toolbar.pack_propagate(False)
        
        # Channel selector
        ctk.CTkLabel(toolbar, text="Channel:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(5, 2))
        self.channel_var = ctk.StringVar(value="RGB")
        self.channel_menu = ctk.CTkOptionMenu(toolbar, variable=self.channel_var,
                                              values=["RGB", "R", "G", "B", "A"],
                                              width=80, command=self._on_channel_change)
        self.channel_menu.pack(side="left", padx=5)
        
        # Mode selector
        ctk.CTkLabel(toolbar, text="Mode:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(15, 2))
        self.mode_var = ctk.StringVar(value="Side by Side")
        self.mode_menu = ctk.CTkOptionMenu(toolbar, variable=self.mode_var,
                                           values=["Side by Side", "Slider", "Difference", "Grid"],
                                           width=100, command=self._on_mode_change)
        self.mode_menu.pack(side="left", padx=5)
        
        # Stats label
        self.stats_label = ctk.CTkLabel(toolbar, text="", font=ctk.CTkFont(size=11))
        self.stats_label.pack(side="left", padx=20)
        
        # Add image button
        ctk.CTkButton(toolbar, text="+ Add", width=60, height=28,
                     command=self._add_image).pack(side="right", padx=5)
        
        # Main canvas area
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Slider (for slider mode)
        self.slider_frame = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.slider_frame.pack(fill="x", padx=10)
        
        self.slider = ctk.CTkSlider(self.slider_frame, from_=0, to=100, 
                                   command=self._on_slider_change)
        self.slider.set(50)
        self.slider.pack(fill="x", padx=20, pady=5)
        self.slider_frame.pack_forget()  # Hidden by default
        
        # Bottom bar
        bottom = ctk.CTkFrame(self, height=45, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(5, 10))
        
        # Pixel info
        self.pixel_label = ctk.CTkLabel(bottom, text="Hover for pixel info", 
                                        font=ctk.CTkFont(size=10), text_color="#888")
        self.pixel_label.pack(side="left", padx=10)
        
        # Buttons
        ctk.CTkButton(bottom, text="Save Diff", width=80, height=28,
                     command=self._save_diff).pack(side="right", padx=5)
        ctk.CTkButton(bottom, text="Reset Zoom", width=80, height=28,
                     fg_color="transparent", border_width=1,
                     command=self._reset_zoom).pack(side="right", padx=5)
        
        # Canvas bindings
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Configure>", self._on_resize)

    def _load_initial_images(self):
        """Load initial images from file list."""
        for i, f in enumerate(self.files[:4]):
            self._load_image_at(i, str(f))
        
        # Update EXR channels if first file is EXR
        if self.files and self.files[0].suffix.lower() == ".exr":
            channels = get_exr_channels(str(self.files[0]))
            if channels:
                all_channels = ["RGB", "R", "G", "B", "A"] + [c for c in channels if c not in "RGBArgba"]
                self.channel_menu.configure(values=all_channels)
        
        self._update_display()

    def _load_image_at(self, index: int, path: str):
        """Load image at specific index."""
        arr = load_image(path, self.current_channel)
        if arr is not None:
            self.images[index] = arr
            if index >= len(self.files):
                self.files.append(Path(path))
            else:
                self.files[index] = Path(path)

    def _update_display(self):
        """Update canvas with current images and mode."""
        self.canvas.delete("all")
        
        # Get canvas size
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        
        valid_images = [img for img in self.images if img is not None]
        if not valid_images:
            self.canvas.create_text(cw//2, ch//2, text="No images loaded", 
                                   fill="#666", font=("Arial", 14))
            return
        
        mode = self.mode_var.get()
        
        if mode == "Difference" and len(valid_images) >= 2:
            self._draw_difference(cw, ch)
        elif mode == "Slider" and len(valid_images) >= 2:
            self._draw_slider(cw, ch)
        elif mode == "Grid":
            self._draw_grid(cw, ch)
        else:  # Side by Side
            self._draw_side_by_side(cw, ch)
        
        # Update stats
        self._update_stats()

    def _draw_side_by_side(self, cw: int, ch: int):
        """Draw images side by side."""
        valid = [(i, img) for i, img in enumerate(self.images) if img is not None]
        if not valid:
            return
        
        n = len(valid)
        panel_w = cw // n
        
        for idx, (i, arr) in enumerate(valid):
            pil_img = array_to_pil(arr)
            
            # Fit to panel
            scale = min(panel_w / pil_img.width, ch / pil_img.height) * self.zoom_level
            new_w = int(pil_img.width * scale)
            new_h = int(pil_img.height * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_img)
            self.photo_images[i] = photo
            
            x = idx * panel_w + panel_w // 2
            y = ch // 2
            self.canvas.create_image(x, y, image=photo, anchor="center")
            
            # Label
            label = self.files[i].name if i < len(self.files) else f"Image {i+1}"
            self.canvas.create_text(x, 15, text=label, fill="#aaa", font=("Arial", 9))

    def _draw_difference(self, cw: int, ch: int):
        """Draw difference visualization."""
        if self.images[0] is None or self.images[1] is None:
            return
        
        diff, count = compute_diff(self.images[0], self.images[1])
        
        # Show original A, B, and diff
        panel_w = cw // 3
        
        for idx, (arr, label) in enumerate([
            (self.images[0], "A"),
            (self.images[1], "B"),
            (diff, "Diff")
        ]):
            pil_img = array_to_pil(arr)
            scale = min(panel_w / pil_img.width, ch / pil_img.height) * 0.9
            new_w = int(pil_img.width * scale)
            new_h = int(pil_img.height * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_img)
            self.photo_images[idx] = photo
            
            x = idx * panel_w + panel_w // 2
            self.canvas.create_image(x, ch // 2, image=photo, anchor="center")
            self.canvas.create_text(x, 15, text=label, fill="#aaa", font=("Arial", 10))

    def _draw_slider(self, cw: int, ch: int):
        """Draw slider comparison."""
        if self.images[0] is None or self.images[1] is None:
            return
        
        self.slider_frame.pack(fill="x", padx=10)
        
        # Get slider position (0-100)
        pos = self.slider.get() / 100.0
        
        img_a = array_to_pil(self.images[0])
        img_b = array_to_pil(self.images[1])
        
        # Resize both to fit canvas
        scale = min(cw / img_a.width, ch / img_a.height) * 0.9
        new_w = int(img_a.width * scale)
        new_h = int(img_a.height * scale)
        
        img_a = img_a.resize((new_w, new_h), Image.LANCZOS)
        img_b = img_b.resize((new_w, new_h), Image.LANCZOS)
        
        # Composite
        split_x = int(new_w * pos)
        composite = Image.new("RGB", (new_w, new_h))
        composite.paste(img_a.crop((0, 0, split_x, new_h)), (0, 0))
        composite.paste(img_b.crop((split_x, 0, new_w, new_h)), (split_x, 0))
        
        photo = ImageTk.PhotoImage(composite)
        self.photo_images[0] = photo
        
        self.canvas.create_image(cw // 2, ch // 2, image=photo, anchor="center")
        
        # Draw split line
        line_x = cw // 2 - new_w // 2 + split_x
        self.canvas.create_line(line_x, 0, line_x, ch, fill="#fff", width=2)

    def _draw_grid(self, cw: int, ch: int):
        """Draw 2x2 grid."""
        valid = [(i, img) for i, img in enumerate(self.images) if img is not None]
        if not valid:
            return
        
        # Calculate grid layout
        cols = 2 if len(valid) > 1 else 1
        rows = (len(valid) + cols - 1) // cols
        
        panel_w = cw // cols
        panel_h = ch // rows
        
        for idx, (i, arr) in enumerate(valid):
            row = idx // cols
            col = idx % cols
            
            pil_img = array_to_pil(arr)
            scale = min(panel_w / pil_img.width, panel_h / pil_img.height) * 0.85
            new_w = int(pil_img.width * scale)
            new_h = int(pil_img.height * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_img)
            self.photo_images[i] = photo
            
            x = col * panel_w + panel_w // 2
            y = row * panel_h + panel_h // 2
            self.canvas.create_image(x, y, image=photo, anchor="center")
            
            label = self.files[i].name if i < len(self.files) else f"Image {i+1}"
            self.canvas.create_text(x, row * panel_h + 12, text=label, 
                                   fill="#aaa", font=("Arial", 9))

    def _update_stats(self):
        """Update statistics label."""
        valid = [img for img in self.images if img is not None]
        
        if len(valid) >= 2:
            try:
                diff, count = compute_diff(valid[0], valid[1])
                ssim = compute_ssim(valid[0], valid[1])
                self.stats_label.configure(text=f"SSIM: {ssim:.4f}  |  Diff Pixels: {count:,}")
            except:
                self.stats_label.configure(text="")
        else:
            n = len(valid)
            self.stats_label.configure(text=f"{n} image(s) loaded")

    def _on_channel_change(self, value):
        """Handle channel selection change."""
        self.current_channel = value
        # Reload all images with new channel
        for i, f in enumerate(self.files):
            if f:
                self._load_image_at(i, str(f))
        self._update_display()

    def _on_mode_change(self, value):
        """Handle mode selection change."""
        # Hide slider if not in slider mode
        if value != "Slider":
            self.slider_frame.pack_forget()
        self._update_display()

    def _on_slider_change(self, value):
        """Handle slider movement."""
        self._update_display()

    def _on_mouse_move(self, event):
        """Show pixel info on mouse move."""
        # TODO: Implement pixel value display
        pass

    def _on_scroll(self, event):
        """Handle mouse wheel for zoom."""
        if event.delta > 0:
            self.zoom_level = min(5.0, self.zoom_level * 1.1)
        else:
            self.zoom_level = max(0.1, self.zoom_level / 1.1)
        self._update_display()

    def _on_click(self, event):
        """Handle click for pan start."""
        self._drag_start = (event.x, event.y)

    def _on_drag(self, event):
        """Handle drag for panning."""
        # TODO: Implement panning
        pass

    def _on_resize(self, event):
        """Handle canvas resize."""
        self.after(100, self._update_display)

    def _add_image(self):
        """Add image via file dialog."""
        filetypes = [
            ("Images", "*.png *.jpg *.jpeg *.exr *.tiff *.tga *.bmp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            # Find first empty slot
            for i in range(4):
                if self.images[i] is None:
                    self._load_image_at(i, path)
                    break
            self._update_display()

    def _save_diff(self):
        """Save difference image."""
        if self.images[0] is None or self.images[1] is None:
            messagebox.showwarning("Warning", "Need at least 2 images")
            return
        
        diff, _ = compute_diff(self.images[0], self.images[1])
        result = create_side_by_side(self.images[0], self.images[1], diff)
        
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")]
        )
        if path:
            result.save(path)
            messagebox.showinfo("Saved", f"Saved to {Path(path).name}")

    def _reset_zoom(self):
        """Reset zoom to 100%."""
        self.zoom_level = 1.0
        self.pan_offset = [0, 0]
        self._update_display()


def launch_compare_gui(target_path: str = None, selection=None):
    """Entry point for menu.py"""
    from utils.batch_runner import collect_batch_context
    
    paths = collect_batch_context("image_compare", target_path)
    if not paths:
        return
    
    # Filter to image files
    image_exts = {".png", ".jpg", ".jpeg", ".exr", ".tiff", ".tif", ".tga", ".bmp"}
    images = [p for p in paths if Path(p).suffix.lower() in image_exts]
    
    if not images:
        messagebox.showwarning("Warning", "이미지 파일을 선택해주세요.")
        return
    
    gui = ImageCompareGUI(images)
    gui.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        files = [arg for arg in sys.argv[1:] if Path(arg).exists()]
        if files:
            gui = ImageCompareGUI(files)
            gui.mainloop()
    else:
        print("Usage: compare_gui.py <image1> [image2] [image3] [image4]")
