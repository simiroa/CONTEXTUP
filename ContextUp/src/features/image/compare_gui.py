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
        
        self.title("ContextUp Image Compare")
        self.geometry("1100x800")
        self.minsize(800, 600)
        
        # State
        self.files = [Path(f) for f in files]  # Allow more than 4 initial files, but UI might limit view
        self.images: List[Optional[np.ndarray]] = []
        self.original_pils: List[Optional[Image.Image]] = []
        self.photo_images: List[Optional[ImageTk.PhotoImage]] = []
        self.current_channel = "RGB"
        self.current_mode = "Side by Side"
        self.zoom_level = 1.0
        self.pan_offset = [0, 0]
        self._drag_start = (0, 0)
        
        self._build_ui()
        self._load_initial_images()
        
        self.lift()
        self.focus_force()

    def _build_ui(self):
        # Top toolbar
        toolbar = ctk.CTkFrame(self, height=50, fg_color="#222")
        toolbar.pack(fill="x", padx=10, pady=(10, 0))
        toolbar.pack_propagate(False)
        
        # Left side: Selectors
        left_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_box.pack(side="left", fill="y", padx=5)

        ctk.CTkLabel(left_box, text="Mode:", font=("", 11, "bold")).pack(side="left", padx=(10, 5))
        self.mode_var = ctk.StringVar(value="Side by Side")
        self.mode_menu = ctk.CTkOptionMenu(toolbar, variable=self.mode_var,
                                           values=["Side by Side", "Slider", "Difference", "Grid"],
                                           width=110, height=28, command=self._on_mode_change)
        self.mode_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(toolbar, text="Channel:", font=("", 11, "bold")).pack(side="left", padx=(15, 5))
        self.channel_var = ctk.StringVar(value="RGB")
        self.channel_menu = ctk.CTkOptionMenu(toolbar, variable=self.channel_var,
                                              values=["RGB", "R", "G", "B", "A"],
                                              width=80, height=28, command=self._on_channel_change)
        self.channel_menu.pack(side="left", padx=5)
        
        # Center side: Stats
        self.stats_label = ctk.CTkLabel(toolbar, text="", font=("", 11), text_color="#00b894")
        self.stats_label.pack(side="left", expand=True)
        
        # Right side: Actions
        right_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_box.pack(side="right", fill="y", padx=5)

        ctk.CTkButton(right_box, text="+ Add Image", width=90, height=28,
                     fg_color="#333", hover_color="#444",
                     command=self._add_image).pack(side="left", padx=5)
        
        # Main canvas area
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#111")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#111", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Slider (for slider mode) - Custom Overlay style
        self.slider_overlay = ctk.CTkFrame(self.canvas_frame, height=40, fg_color="#222", corner_radius=10)
        self.slider_overlay.place(relx=0.5, rely=0.9, anchor="center")
        
        self.slider = ctk.CTkSlider(self.slider_overlay, from_=0, to=100, width=300,
                                   command=self._on_slider_change)
        self.slider.set(50)
        self.slider.pack(padx=20, pady=10)
        self.slider_overlay.place_forget()  # Hidden by default
        
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
        for f in self.files:
            self._add_image_to_slots(str(f))
        
        # Update EXR channels if first file is EXR
        if self.files and self.files[0].suffix.lower() == ".exr":
            channels = get_exr_channels(str(self.files[0]))
            if channels:
                all_channels = ["RGB", "R", "G", "B", "A"] + [c for c in channels if c not in "RGBArgba"]
                self.channel_menu.configure(values=all_channels)
        
        self._update_display()

    def _add_image_to_slots(self, path: str):
        """Add a new image to the internal lists."""
        arr = load_image(path, self.current_channel)
        if arr is not None:
            self.images.append(arr)
            self.original_pils.append(array_to_pil(arr))
            self.photo_images.append(None)
            if Path(path) not in self.files:
                self.files.append(Path(path))

    def _load_image_at(self, index: int, path: str):
        """Load image at specific index."""
        arr = load_image(path, self.current_channel)
        if arr is not None:
            self.images[index] = arr
            self.original_pils[index] = array_to_pil(arr)
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
            pil_img = self.original_pils[i]
            if not pil_img: continue
            
            # Synchronized View Calculation
            base_scale = min(panel_w / pil_img.width, ch / pil_img.height) * 0.95
            scale = base_scale * self.zoom_level
            
            new_w = int(pil_img.width * scale)
            new_h = int(pil_img.height * scale)
            
            if new_w > 0 and new_h > 0:
                img_display = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_display)
                self.photo_images[i] = photo
                
                x = idx * panel_w + panel_w // 2 + self.pan_offset[0]
                y = ch // 2 + self.pan_offset[1]
                self.canvas.create_image(x, y, image=photo, anchor="center")
            
            # Labels and Interactive Buttons
            label_y = 20
            img_name = self.files[i].name if i < len(self.files) else f"Image {i+1}"
            
            self.canvas.create_text(idx * panel_w + 10, label_y, text=img_name, fill="#00b894", 
                                   anchor="nw", font=("", 10, "bold"))
            
            btn_y = label_y + 20
            rid = self.canvas.create_text(idx * panel_w + 10, btn_y, text="[Replace]", fill="#888", 
                                   anchor="nw", font=("", 9))
            self.canvas.tag_bind(rid, "<Button-1>", lambda e, idx=i: self._replace_image(idx))
            
            xid = self.canvas.create_text(idx * panel_w + 70, btn_y, text="[Remove]", fill="#cc4444", 
                                   anchor="nw", font=("", 9))
            self.canvas.tag_bind(xid, "<Button-1>", lambda e, idx=i: self._remove_image(idx))

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
            arr = load_image(str(f), self.current_channel)
            if arr is not None:
                self.images[i] = arr
                self.original_pils[i] = array_to_pil(arr)
        self._update_display()

    def _on_mode_change(self, value):
        """Handle mode selection change."""
        # Toggle slider visibility
        if value == "Slider":
            self.slider_overlay.place(relx=0.5, rely=0.9, anchor="center")
        else:
            self.slider_overlay.place_forget()
        self._update_display()

    def _on_slider_change(self, value):
        """Handle slider movement."""
        self._update_display()

    def _on_mouse_move(self, event):
        """Show pixel info on mouse move."""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        valid_indices = [i for i, img in enumerate(self.images) if img is not None]
        if not valid_indices: return

        # Simple logic: detect which image mouse is over (assuming Side-by-Side)
        mode = self.mode_var.get()
        if mode == "Side by Side":
            n = len(valid_indices)
            panel_w = cw // n
            idx = event.x // panel_w
            if idx < n:
                img_idx = valid_indices[idx]
                arr = self.images[img_idx]
                pil_img = self.original_pils[img_idx]
                
                # Reverse scale to get original pixel coordinates
                base_scale = min(panel_w / pil_img.width, ch / pil_img.height) * 0.95
                scale = base_scale * self.zoom_level
                
                # Image center on canvas
                cx = idx * panel_w + panel_w // 2 + self.pan_offset[0]
                cy = ch // 2 + self.pan_offset[1]
                
                rel_x = (event.x - cx) / scale + pil_img.width / 2
                rel_y = (event.y - cy) / scale + pil_img.height / 2
                
                px, py = int(rel_x), int(rel_y)
                if 0 <= px < arr.shape[1] and 0 <= py < arr.shape[0]:
                    val = arr[py, px]
                    if len(val) >= 3:
                        rgb = [int(v * 255) for v in val]
                        self.pixel_label.configure(text=f"Pos: {px}, {py} | RGB: {rgb[0]}, {rgb[1]}, {rgb[2]}", text_color="#00b894")
                    else:
                        self.pixel_label.configure(text=f"Pos: {px}, {py} | Val: {val[0]:.3f}", text_color="#00b894")
                else:
                    self.pixel_label.configure(text="Outside Image", text_color="#888")

    def _on_scroll(self, event):
        """Handle mouse wheel for zoom."""
        if event.delta > 0:
            self.zoom_level = min(20.0, self.zoom_level * 1.2)
        else:
            self.zoom_level = max(0.05, self.zoom_level / 1.2)
        self._update_display()

    def _on_click(self, event):
        """Handle click for pan start."""
        self._drag_start = (event.x, event.y)

    def _on_drag(self, event):
        """Handle drag for panning."""
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self.pan_offset[0] += dx
        self.pan_offset[1] += dy
        self._drag_start = (event.x, event.y)
        self._update_display()

    def _on_resize(self, event):
        """Handle canvas resize."""
        self.after(100, self._update_display)

    def _add_image(self):
        """Add image via file dialog."""
        filetypes = [
            ("Images", "*.png *.jpg *.jpeg *.exr *.tiff *.tga *.bmp"),
            ("All files", "*.*")
        ]
        paths = filedialog.askopenfilenames(filetypes=filetypes)
        if paths:
            for path in paths:
                self._add_image_to_slots(path)
            self._update_display()
            
    def _replace_image(self, index: int):
        """Replace image at index via file dialog."""
        filetypes = [
            ("Images", "*.png *.jpg *.jpeg *.exr *.tiff *.tga *.bmp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            arr = load_image(path, self.current_channel)
            if arr is not None:
                self.images[index] = arr
                self.original_pils[index] = array_to_pil(arr)
                self.files[index] = Path(path)
                self._update_display()

    def _remove_image(self, index: int):
        """Remove image at index."""
        if 0 <= index < len(self.images):
            self.images.pop(index)
            self.original_pils.pop(index)
            self.photo_images.pop(index)
            self.files.pop(index)
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
