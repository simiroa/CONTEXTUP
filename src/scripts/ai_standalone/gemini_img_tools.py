"""
Texture Generation & PBR Tools using CV2 and Gemini 2.5.
"""
import sys
import os
import cv2
import numpy as np
from pathlib import Path

import traceback

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

from utils.logger import setup_logger
logger = setup_logger("TextureGen")

logger.info("Starting texture_gen.py")

try:
    from google import genai
    from google.genai import types
    logger.info("Successfully imported google.genai")
except ImportError as e:
    logger.error(f"Failed to import google.genai: {e}")
    # We will handle this gracefully in the GUI or main execution
    genai = None

from PIL import Image, ImageTk
import customtkinter as ctk
import threading
import time
from tkinter import messagebox, Canvas, filedialog
import io

from PIL import ImageGrab

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

try:
    from core.settings import load_settings
    from utils.gui_lib import BaseWindow
    from utils.explorer import get_selection_from_explorer
    logger.info("Successfully imported local modules")
except Exception as e:
    logger.error(f"Failed to import local modules: {e}")
    raise

def get_gemini_client():
    if genai is None:
        return None
    settings = load_settings()
    api_key = settings.get('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def imread_unicode(path):
    """Reads an image from a path that may contain non-ASCII characters."""
    try:
        # Read file as byte stream and decode
        stream = np.fromfile(path, np.uint8)
        return cv2.imdecode(stream, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.error(f"imread_unicode failed for {path}: {e}")
        return None

def get_unique_path(path: Path) -> Path:
    """Returns a unique path by appending a counter if the file already exists."""
    if not path.exists(): return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter:02d}{suffix}"
        if not new_path.exists(): return new_path
        counter += 1

class HistoryManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.history = [] # List of image paths
        self.current_index = -1
        
    def add(self, image: np.ndarray):
        # Save to cache
        timestamp = int(time.time() * 1000)
        filename = f"history_{timestamp}.png"
        path = self.cache_dir / filename
        cv2.imwrite(str(path), image)
        
        # If we are in the middle of history, truncate future
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
            
        self.history.append(path)
        self.current_index = len(self.history) - 1
        
    def undo(self):
        if self.can_undo():
            self.current_index -= 1
            return self._load_current()
        return None
        
    def redo(self):
        if self.can_redo():
            self.current_index += 1
            return self._load_current()
        return None
        
    def _load_current(self):
        if 0 <= self.current_index < len(self.history):
            path = self.history[self.current_index]
            if path.exists():
                return imread_unicode(str(path))
        return None
        
    def can_undo(self): return self.current_index > 0
    def can_redo(self): return self.current_index < len(self.history) - 1

# --- Core Logic Functions (CV2 PBR) ---

def generate_normal_map(img, strength=1.0):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    x_grad = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    y_grad = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    z = np.ones_like(x_grad) * (1.0 / strength)
    normal = np.dstack((-x_grad, -y_grad, z))
    norm = np.linalg.norm(normal, axis=2)
    normal = normal / norm[:, :, np.newaxis]
    normal = ((normal + 1) * 0.5 * 255).astype(np.uint8)
    return cv2.cvtColor(normal, cv2.COLOR_RGB2BGR)

def generate_roughness_map(img, invert=False, contrast=1.0):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if invert:
        gray = 255 - gray
    if contrast != 1.0:
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)
        gray = cv2.addWeighted(gray, alpha_c, gray, 0, gamma_c)
    return gray

def generate_displacement_map(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def generate_occlusion_map(img, strength=1.0):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    invGamma = 1.0 / (0.5 * strength) 
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(gray, table)

def generate_metallic_map(img, strength=1.0):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return (gray * 0.2 * strength).astype(np.uint8)

def make_tileable_synthesis(img, overlap=0.15):
    h, w = img.shape[:2]
    shift_x = w // 2
    shift_y = h // 2
    img_roll = np.roll(img, shift_x, axis=1)
    img_roll = np.roll(img_roll, shift_y, axis=0)
    mask = np.zeros((h, w), dtype=np.float32)
    sw = int(w * overlap)
    sh = int(h * overlap)
    img_blur = cv2.GaussianBlur(img_roll, (21, 21), 0)
    cv2.line(mask, (w//2, 0), (w//2, h), 1.0, sw)
    cv2.line(mask, (0, h//2), (w, h//2), 1.0, sh)
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    mask_3c = np.dstack((mask, mask, mask))
    res = (img_roll.astype(np.float32) * (1.0 - mask_3c) + img_blur.astype(np.float32) * mask_3c).astype(np.uint8)
    return res

# --- Image Viewer Class ---

class ImageViewer(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.canvas = Canvas(self, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.image = None
        self.tk_image = None
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom) # Linux scroll
        self.canvas.bind("<Button-5>", self.on_zoom) # Linux scroll
        self.canvas.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        if self.image:
            self.redraw()

    def load_image(self, cv_img):
        self.image = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        self.reset_view()
        self.redraw()

    def reset_view(self):
        if not self.image: return
        # Fit to window
        cw = self.canvas.winfo_width() or 500
        ch = self.canvas.winfo_height() or 500
        iw, ih = self.image.size
        self.scale = min(cw/iw, ch/ih) * 0.9
        self.pan_x = cw // 2
        self.pan_y = ch // 2
        self.redraw()

    def redraw(self):
        if not self.image: return
        
        w, h = self.image.size
        new_w = int(w * self.scale)
        new_h = int(h * self.scale)
        
        if new_w <= 0 or new_h <= 0: return
        
        resized = self.image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        
        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, image=self.tk_image, anchor="center")

    def on_drag_start(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag_motion(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.pan_x += dx
        self.pan_y += dy
        self.start_x = event.x
        self.start_y = event.y
        self.redraw()

    def on_zoom(self, event):
        if event.num == 5 or event.delta < 0:
            self.scale *= 0.9
        else:
            self.scale *= 1.1
        self.redraw()

# --- Main GUI Class ---

class GeminiImageToolsGUI(BaseWindow):
    def __init__(self, target_path=None, start_tab="Style"):
        super().__init__(title="Gemini Image Tools (Gemini 2.5)", width=1200, height=900)
        
        self.target_path = target_path
        self.start_tab = start_tab
        self.selection = []
        self.last_api_request = 0
        self.api_delay = 2.0 
        
        if target_path:
            try:
                self.selection = get_selection_from_explorer(target_path)
                if not self.selection:
                    p = Path(target_path)
                    if p.is_file(): self.selection = [p]
            except Exception as e:
                print(f"Selection error: {e}")
                logger.error(f"Selection error: {e}")
                
        if not self.selection:
            messagebox.showerror("Error", "No image selected.")
            self.destroy()
            return
            
        self.current_image_path = self.selection[0]
        
        try:
            # Use unicode-aware loader
            self.original_img = imread_unicode(str(self.current_image_path))
            if self.original_img is None:
                raise ValueError("Image loaded as None")
            self.cv_img = self.original_img.copy()
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            self.cv_img = None
            
        if self.cv_img is None:
            messagebox.showerror("Error", "Failed to load image.\n(Check file path or format)")
            self.destroy()
            return

        self.create_widgets()
        
        # History Init
        cache_dir = current_dir / ".cache"
        self.history = HistoryManager(cache_dir)
        self.history.add(self.cv_img)
        
        # Force update to ensure canvas has dimensions before loading image
        self.update() 
        self.viewer.load_image(self.cv_img)
        self.update_info_header()
        
        # Initial Prompt Update
        self.update_prompt_from_ui()
        

            
        # Clipboard Bind
        self.bind("<Control-v>", self.paste_from_clipboard)



    def refresh_preview(self, event=None):
        # Renamed from update_pbr_preview to avoid potential conflicts
        print("DEBUG: refresh_preview called")
        try:
            strength = self.slider_strength.get()
            invert = self.var_invert.get()
            
            if self.var_normal.get():
                res = generate_normal_map(self.cv_img, strength)
            elif self.var_rough.get():
                res = generate_roughness_map(self.cv_img, invert, contrast=strength)
            elif self.var_disp.get():
                res = generate_displacement_map(self.cv_img)
            elif self.var_occ.get():
                res = generate_occlusion_map(self.cv_img, strength)
            elif self.var_metal.get():
                res = generate_metallic_map(self.cv_img, strength)
            else:
                res = self.cv_img
                
            self.viewer.load_image(res)
            self.processed_img = res
        except Exception as e:
            print(f"Error in refresh_preview: {e}")

    def create_widgets(self):
        # Main Layout: Grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Content Frame
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        self.content_frame.grid_columnconfigure(0, weight=0)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Left Panel
        self.left_panel = ctk.CTkFrame(self.content_frame, width=350)
        self.left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 5), pady=0)
        
        # Right Panel
        self.right_panel = ctk.CTkFrame(self.content_frame)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        
        # Info Header
        self.info_frame = ctk.CTkFrame(self.right_panel, height=30, fg_color="transparent")
        self.info_frame.pack(side="top", fill="x", padx=10, pady=(5, 0))
        
        self.lbl_info = ctk.CTkLabel(self.info_frame, text="", text_color="gray", font=("Arial", 12, "bold"))
        self.lbl_info.pack(side="top", anchor="center")
        
        # Image Viewer
        self.viewer = ImageViewer(self.right_panel)
        self.viewer.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        
        # Navigation Bar (Bottom of Right Panel)
        self.nav_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent", height=30)
        self.nav_frame.pack(side="bottom", fill="x", pady=(0, 5))
        
        # Centered Navigation Container
        self.nav_container = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.nav_container.pack(side="top", anchor="center")
        
        # Open Button
        self.btn_open = ctk.CTkButton(self.nav_container, text="📂", width=30, height=24, command=self.open_file_dialog, fg_color="transparent", text_color="gray", hover_color="#333333")
        self.btn_open.pack(side="left", padx=5)
        
        self.btn_prev_arrow = ctk.CTkButton(self.nav_container, text="<", width=30, height=24, command=self.do_undo, state="disabled")
        self.btn_prev_arrow.pack(side="left", padx=5)
        
        self.lbl_counter = ctk.CTkLabel(self.nav_container, text="1 / 1", font=("Arial", 12), text_color="gray")
        self.lbl_counter.pack(side="left", padx=10)
        
        self.btn_next_arrow = ctk.CTkButton(self.nav_container, text=">", width=30, height=24, command=self.do_redo, state="disabled")
        self.btn_next_arrow.pack(side="left", padx=5)
        
        # Clear/Close Button
        self.btn_clear = ctk.CTkButton(self.nav_container, text="🗑️", width=30, height=24, command=self.close_image, fg_color="transparent", text_color="gray", hover_color="#333333")
        self.btn_clear.pack(side="left", padx=5)

        # Global Image Type Selector
        ctk.CTkLabel(self.left_panel, text="Image Type:", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5), padx=10, anchor="w")
        self.image_type = ctk.StringVar(value="Select Type")
        ctk.CTkComboBox(self.left_panel, variable=self.image_type, values=["Select Type", "UV Texture", "Tileable Texture", "Photo", "Sketch"], command=self.update_prompt_from_ui).pack(fill="x", padx=10, pady=(0, 10))
        
        # Tabs
        self.tab_view = ctk.CTkTabview(self.left_panel, command=self.on_tab_change)
        self.tab_view.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tab_style = self.tab_view.add("Style")
        self.tab_pbr = self.tab_view.add("PBR Gen")
        self.tab_tile = self.tab_view.add("Tileable")
        self.tab_weather = self.tab_view.add("Weathering")
        self.tab_analyze = self.tab_view.add("Analysis")
        self.tab_outpaint = self.tab_view.add("Outpaint")
        self.tab_inpaint = self.tab_view.add("Inpaint")
        
        self.setup_style_tab()
        self.setup_pbr_tab()
        self.setup_tile_tab()
        self.setup_weather_tab()
        self.setup_analyze_tab()
        self.setup_outpaint_tab()
        self.setup_inpaint_tab()
        
        # Set initial tab
        if self.start_tab:
            try:
                self.tab_view.set(self.start_tab)
            except ValueError:
                print(f"Tab '{self.start_tab}' not found, defaulting to Style")
        
        # Unified Bottom Bar
        self.bottom_bar = ctk.CTkFrame(self.main_frame, height=150)
        self.bottom_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Prompt Area
        prompt_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        prompt_frame.pack(fill="x", padx=10, pady=(5,0))
        
        ctk.CTkLabel(prompt_frame, text="AI Prompt:").pack(side="left", anchor="w")
        ctk.CTkButton(prompt_frame, text="[JSON]", width=50, height=20, fg_color="transparent", border_width=1, text_color="gray", command=self.show_prompt_json).pack(side="left", padx=10)
        
        self.prompt_entry = ctk.CTkTextbox(self.bottom_bar, height=50)
        self.prompt_entry.pack(fill="x", padx=10, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        # Left Side: Generate -> Reset -> Status
        ctk.CTkButton(btn_frame, text="Generate (Gemini 2.5)", command=self.run_ai_request, fg_color="#1f6aa5", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Reset to Original", command=self.reset_image, fg_color="gray", width=120).pack(side="left", padx=5)
        
        self.status_label = ctk.CTkLabel(btn_frame, text="Ready", text_color="gray", font=("Arial", 12))
        self.status_label.pack(side="left", padx=15)
        
        # Right Side: Save & Copy
        ctk.CTkButton(btn_frame, text="Save As...", command=self.save_result, fg_color="green", width=100).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Copy", command=self.copy_to_clipboard, fg_color="#E67E22", width=80).pack(side="right", padx=5)

    def setup_style_tab(self):
        ctk.CTkLabel(self.tab_style, text="AI Style Transfer", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.style_mode = ctk.StringVar(value="Realistic")
        ctk.CTkComboBox(self.tab_style, variable=self.style_mode, values=["Realistic", "Stylized", "Cartoon", "Cyberpunk", "Sketch", "Oil Painting"], command=self.update_prompt_from_ui).pack(pady=10)
        
        ctk.CTkLabel(self.tab_style, text="Style Strength:").pack(pady=(20, 5))
        self.slider_style_strength = ctk.CTkSlider(self.tab_style, from_=0.0, to=1.0, number_of_steps=20, command=self.update_prompt_from_ui)
        self.slider_style_strength.set(0.7)
        self.slider_style_strength.pack(fill="x", padx=10)
        
        # Removed Seamless Tiling Checkbox as requested (handled by Global Type)

    def setup_pbr_tab(self):
        ctk.CTkLabel(self.tab_pbr, text="Generate PBR Maps (CV2)", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.var_normal = ctk.BooleanVar(value=False) # Default to False to show original image first
        self.var_rough = ctk.BooleanVar(value=False)
        self.var_disp = ctk.BooleanVar(value=False)
        self.var_occ = ctk.BooleanVar(value=False)
        self.var_metal = ctk.BooleanVar(value=False)
        self.var_orm = ctk.BooleanVar(value=False)
        
        # Updated to use refresh_preview
        for txt, var in [("Normal Map", self.var_normal), ("Roughness Map", self.var_rough), ("Displacement", self.var_disp), ("Occlusion (AO)", self.var_occ), ("Metallic", self.var_metal)]:
            ctk.CTkCheckBox(self.tab_pbr, text=txt, variable=var, command=self.refresh_preview).pack(anchor="w", padx=10, pady=2)
        
        ctk.CTkSwitch(self.tab_pbr, text="ORM Pack (R=Occ, G=Rough, B=Met)", variable=self.var_orm).pack(pady=10)
        
        ctk.CTkLabel(self.tab_pbr, text="Strength / Contrast:").pack(pady=(10, 5))
        # Updated to use refresh_preview
        self.slider_strength = ctk.CTkSlider(self.tab_pbr, from_=0.1, to=5.0, number_of_steps=50, command=lambda x: self.refresh_preview())
        self.slider_strength.set(1.0)
        self.slider_strength.pack(fill="x", padx=10)
        
        self.var_invert = ctk.BooleanVar(value=False)
        # Updated to use refresh_preview
        ctk.CTkCheckBox(self.tab_pbr, text="Invert (Roughness)", variable=self.var_invert, command=self.refresh_preview).pack(pady=5)
        
        ctk.CTkButton(self.tab_pbr, text="Generate PBR Maps (Local)", command=self.generate_all_pbr).pack(pady=20)

        # AI Section
        ctk.CTkLabel(self.tab_pbr, text="AI Map Generation (Single):", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.pbr_ai_target = ctk.StringVar(value="None (Local Only)")
        ctk.CTkComboBox(self.tab_pbr, variable=self.pbr_ai_target, values=["None (Local Only)", "Normal Map", "Roughness Map", "Displacement Map", "Occlusion Map"], command=self.update_prompt_from_ui).pack(pady=5)
        ctk.CTkLabel(self.tab_pbr, text="* Select a map type to enable AI generation button", font=ctk.CTkFont(size=10), text_color="gray").pack()

    def setup_tile_tab(self):
        ctk.CTkLabel(self.tab_tile, text="Make Tileable (AI)", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(self.tab_tile, text="Texture Scale Factor:", anchor="w").pack(fill="x", padx=10, pady=(10, 0))
        self.slider_tile_scale = ctk.CTkSlider(self.tab_tile, from_=0.5, to=2.0, number_of_steps=30, command=self.update_prompt_from_ui)
        self.slider_tile_scale.set(1.0)
        self.slider_tile_scale.pack(fill="x", padx=10, pady=5)
        
        # Scale Labels
        scale_frame = ctk.CTkFrame(self.tab_tile, fg_color="transparent")
        scale_frame.pack(fill="x", padx=10)
        ctk.CTkLabel(scale_frame, text="0.5x (Zoom Out)", font=("", 10)).pack(side="left")
        ctk.CTkLabel(scale_frame, text="2.0x (Zoom In)", font=("", 10)).pack(side="right")
        
        ctk.CTkLabel(self.tab_tile, text="Description / Context (Optional):", anchor="w").pack(fill="x", padx=10, pady=(20, 0))
        self.entry_tile_desc = ctk.CTkEntry(self.tab_tile, placeholder_text="e.g. Concrete wall, Fabric pattern...")
        self.entry_tile_desc.pack(fill="x", padx=10, pady=5)
        self.entry_tile_desc.pack(fill="x", padx=10, pady=5)
        self.entry_tile_desc.bind("<KeyRelease>", self.update_prompt_from_ui)
        
        # Check Tiling Button
        self.btn_check_tile = ctk.CTkButton(self.tab_tile, text="🔍 Check Tiling (Offset 50%)", command=self.toggle_tiling_check, fg_color="transparent", border_width=1, text_color="gray")
        self.btn_check_tile.pack(pady=15)

    def toggle_tiling_check(self):
        if self.cv_img is None: return
        
        if not hasattr(self, 'is_tiling_check'): self.is_tiling_check = False
        
        if self.is_tiling_check:
            # Restore
            self.viewer.load_image(self.cv_img)
            self.is_tiling_check = False
            self.btn_check_tile.configure(text="🔍 Check Tiling (Offset 50%)", fg_color="transparent", text_color="gray")
        else:
            # Apply Offset
            h, w = self.cv_img.shape[:2]
            img_roll = np.roll(self.cv_img, w // 2, axis=1)
            img_roll = np.roll(img_roll, h // 2, axis=0)
            
            # Draw crosshair to show seam
            cv2.line(img_roll, (w//2, 0), (w//2, h), (0, 255, 0), 1)
            cv2.line(img_roll, (0, h//2), (w, h//2), (0, 255, 0), 1)
            
            self.viewer.load_image(img_roll)
            self.is_tiling_check = True
            self.btn_check_tile.configure(text="🔙 Restore View", fg_color="#2b2b2b", text_color="white")

    def setup_weather_tab(self):
        ctk.CTkLabel(self.tab_weather, text="AI Weathering", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.weather_mode = ctk.StringVar(value="Rust")
        ctk.CTkComboBox(self.tab_weather, variable=self.weather_mode, values=["Rust", "Dirt", "Moss", "Scratches", "Old Paper", "Worn Edges"], command=self.update_prompt_from_ui).pack(pady=10)
        
        ctk.CTkLabel(self.tab_weather, text="Intensity:").pack(pady=5)
        self.slider_weather = ctk.CTkSlider(self.tab_weather, from_=0.0, to=1.0, number_of_steps=20, command=self.update_prompt_from_ui)
        self.slider_weather.set(0.5)
        self.slider_weather.pack(fill="x", padx=10)

    def setup_analyze_tab(self):
        ctk.CTkLabel(self.tab_analyze, text="Gemini Vision Analysis", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(self.tab_analyze, text="Output Format:").pack(pady=(5, 0))
        self.analyze_style = ctk.StringVar(value="General Analysis")
        ctk.CTkComboBox(self.tab_analyze, variable=self.analyze_style, 
                        values=["General Analysis", "Midjourney Prompt", "Flux Prompt", "ComfyUI Prompt"],
                        command=self.update_prompt_from_ui).pack(pady=5)

        self.txt_analysis = ctk.CTkTextbox(self.tab_analyze, height=200)
        self.txt_analysis.pack(fill="x", padx=5, pady=5)
        
        btn_frame = ctk.CTkFrame(self.tab_analyze, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_frame, text="Analyze Texture", command=self.run_analysis).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Copy to Clipboard", command=self.copy_analysis_to_clipboard, fg_color="gray").pack(side="right", expand=True, padx=5)

    def copy_analysis_to_clipboard(self):
        text = self.txt_analysis.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status_label.configure(text="Copied to Clipboard", text_color="green")
            messagebox.showinfo("Copied", "Analysis text copied to clipboard.")

    def setup_outpaint_tab(self):
        ctk.CTkLabel(self.tab_outpaint, text="AI Outpainting", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.tab_outpaint, text="Expand Direction:").pack(pady=5)
        self.outpaint_dir = ctk.StringVar(value="All Sides")
        ctk.CTkComboBox(self.tab_outpaint, variable=self.outpaint_dir, values=["All Sides", "Horizontal", "Vertical"], command=self.update_prompt_from_ui).pack(pady=5)
        
        ctk.CTkLabel(self.tab_outpaint, text="Expansion Scale:").pack(pady=(20, 5))
        self.slider_outpaint = ctk.CTkSlider(self.tab_outpaint, from_=1.1, to=2.0, number_of_steps=18, command=self.update_prompt_from_ui)
        self.slider_outpaint.set(1.5)
        self.slider_outpaint.pack(fill="x", padx=10)

    def setup_inpaint_tab(self):
        ctk.CTkLabel(self.tab_inpaint, text="Object Removal / Replace", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(self.tab_inpaint, text="Target Object (to remove/change):").pack(pady=(10, 0), anchor="w", padx=10)
        self.entry_inpaint_target = ctk.CTkEntry(self.tab_inpaint)
        self.entry_inpaint_target.pack(fill="x", padx=10, pady=5)
        self.entry_inpaint_target.bind("<KeyRelease>", self.update_prompt_from_ui)
        
        ctk.CTkLabel(self.tab_inpaint, text="Replacement (leave empty to remove):").pack(pady=(10, 0), anchor="w", padx=10)
        self.entry_inpaint_replace = ctk.CTkEntry(self.tab_inpaint)
        self.entry_inpaint_replace.pack(fill="x", padx=10, pady=5)
        self.entry_inpaint_replace.bind("<KeyRelease>", self.update_prompt_from_ui)

    def on_tab_change(self):
        self.update_prompt_from_ui()

    def update_prompt_from_ui(self, event=None):
        tab = self.tab_view.get()
        # Debug print to check if tab is correct
        # print(f"DEBUG: Current Tab: {tab}")
        
        prompt = ""
        
        # Global Type Context
        img_type = self.image_type.get()
        type_context = f"Input image is a {img_type}." if img_type != "Select Type" else ""

        if tab == "Style":
            style = self.style_mode.get()
            strength = self.slider_style_strength.get()
            # Convert strength to descriptive text for better AI adherence
            str_desc = "subtle" if strength < 0.3 else "moderate" if strength < 0.7 else "strong"
            prompt = f"{type_context} Transform this texture into {style} style. Style strength: {str_desc} ({strength:.1f}). Preserve the underlying pattern, geometry, and composition while applying the artistic style. The result should look like a high-quality texture."
            
        elif tab == "PBR Gen":
            ai_target = self.pbr_ai_target.get()
            if ai_target == "None (Local Only)":
                prompt = "AI Generation is disabled in this mode. Use 'Generate PBR Maps (Local)' button above, or select a map type to generate via AI."
            else:
                tech_spec = ""
                if "Normal" in ai_target:
                    tech_spec = "Generate a tangent space normal map (purple/blue base). High frequency details should be crisp and defined. The map should accurately represent the surface depth."
                elif "Roughness" in ai_target:
                    tech_spec = "Generate a grayscale roughness map. White represents rough areas, Black represents glossy/smooth areas. Ensure high contrast where necessary."
                elif "Displacement" in ai_target:
                    tech_spec = "Generate a grayscale height/displacement map. White represents high points, Black represents low points. Smooth transitions for gradients."
                elif "Occlusion" in ai_target:
                    tech_spec = "Generate an ambient occlusion map. Darken crevices, corners, and deep areas. The rest should be white."
                
                prompt = f"{type_context} Generate a high-quality {ai_target} for this texture. {tech_spec} Ensure it is accurate and aligned with the original details."

        elif tab == "Tileable":
            scale = self.slider_tile_scale.get()
            desc = self.entry_tile_desc.get().strip()
            desc_text = f"Context: {desc}." if desc else ""
            
            prompt = f"{type_context} {desc_text} Generate a seamless tileable texture based on this image. The texture should represent the surface material shown. Scale the details by a factor of {scale:.1f}x (where >1 means zoom in/larger details, <1 means zoom out/smaller details). The result MUST be seamlessly tileable on all sides (x and y axes). Eliminate any visible seams or borders. Maintain a consistent texture density. Output the texture only."
            
        elif tab == "Weathering":
             mode = self.weather_mode.get()
             intensity = self.slider_weather.get()
             prompt = f"{type_context} Apply {mode} weathering effect. Intensity: {intensity:.1f} (0-1). Make it look worn and realistic."
             
        elif tab == "Analysis":
            style = self.analyze_style.get()
            if style == "Midjourney Prompt":
                instruction = "Analyze this texture and write a highly detailed Midjourney v6 prompt to recreate it. Focus on lighting, material properties, and camera settings. Format: '/imagine prompt: ... --v 6.0'"
            elif style == "Flux Prompt":
                instruction = "Analyze this texture and write a natural language prompt optimized for Flux.1 models. Describe the texture flow, details, and atmosphere vividly."
            elif style == "ComfyUI Prompt":
                instruction = "Analyze this texture and provide a comma-separated list of keywords (tags) suitable for Stable Diffusion/ComfyUI positive prompt. Use Danbooru-style tags where applicable. Include material tags, quality tags, and lighting tags."
            else:
                instruction = "Analyze this texture in detail. Describe its material, pattern, roughness, and suggest PBR settings."
            
            prompt = f"{type_context} {instruction} Output text only. Do not generate an image."

        elif tab == "Outpaint":
            direction = self.outpaint_dir.get()
            scale = self.slider_outpaint.get()
            prompt = f"{type_context} Outpaint this image. The input image is a crop. Generate a larger, zoomed-out view of this texture/scene, extending the patterns seamlessly in {direction} direction(s) by {scale:.1f}x. Maintain the same resolution and detail level. Fill the new areas naturally matching the existing texture."

        elif tab == "Inpaint":
            target = self.entry_inpaint_target.get()
            replace = self.entry_inpaint_replace.get()
            if not target:
                prompt = "Please specify a target object to remove or replace."
            elif not replace:
                prompt = f"{type_context} Remove the '{target}' from this image. Fill the area naturally to match the background."
            else:
                prompt = f"{type_context} Replace the '{target}' with '{replace}' in this image. Blend it naturally with the lighting and perspective."

        self.prompt_entry.delete("1.0", "end")
        self.prompt_entry.insert("1.0", prompt)

    def check_rate_limit(self):
        now = time.time()
        if now - self.last_api_request < self.api_delay:
            wait_time = self.api_delay - (now - self.last_api_request)
            self.status_label.configure(text=f"Wait {wait_time:.1f}s...", text_color="orange")
            return False
        self.last_api_request = now
        self.status_label.configure(text="Processing...", text_color="yellow")
        return True

    def reset_image(self):
        self.cv_img = self.original_img.copy()
        self.viewer.load_image(self.cv_img)
        self.history.add(self.cv_img)
        self.update_history_buttons()
        self.status_label.configure(text="Reset to Original", text_color="green")
        
    def update_info_header(self):
        if self.cv_img is None: return
        h, w = self.cv_img.shape[:2]
        filename = self.current_image_path.name
        folder = self.current_image_path.parent.name
        self.lbl_info.configure(text=f"File: {filename} | Folder: {folder} | Res: {w}x{h}")
        
    def do_undo(self):
        img = self.history.undo()
        if img is not None:
            self.cv_img = img
            self.viewer.load_image(self.cv_img)
            self.update_history_buttons()
            self.update_info_header()
            
    def do_redo(self):
        img = self.history.redo()
        if img is not None:
            self.cv_img = img
            self.viewer.load_image(self.cv_img)
            self.update_history_buttons()
            self.update_info_header()
            
    def update_history_buttons(self):
        can_undo = self.history.can_undo()
        can_redo = self.history.can_redo()
        
        self.btn_prev_arrow.configure(state="normal" if can_undo else "disabled")
        self.btn_next_arrow.configure(state="normal" if can_redo else "disabled")
        
        # Update Counter
        current = self.history.current_index + 1
        total = len(self.history.history)
        self.lbl_counter.configure(text=f"{current} / {total}")

    def run_ai_request(self):
        if not self.check_rate_limit(): return
        
        prompt = self.prompt_entry.get("1.0", "end").strip()
        if not prompt:
            self.status_label.configure(text="Error: No Prompt", text_color="red")
            return
            
        client = get_gemini_client()
        if not client:
            messagebox.showerror("Error", "Gemini API Key not configured.")
            return

        def _process():
            try:
                # Determine Model based on Tab
                current_tab = self.tab_view.get()
                if current_tab == "Analysis":
                    # Analysis requires a multimodal understanding model
                    model_name = "gemini-2.5-flash"
                else:
                    # Generation/Editing requires an image generation model
                    model_name = "gemini-2.5-flash-image"
                
                self.status_label.configure(text=f"Sending to {model_name}...", text_color="yellow")

                # Prepare Image
                is_success, buffer = cv2.imencode(".png", self.cv_img)
                if not is_success:
                    raise ValueError("Failed to encode image")
                img_bytes = buffer.tobytes()

                # Call Gemini API
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                    ]
                )
                
                # Handle Response Parts
                text_output = ""
                image_found = False
                new_cv_img = None
                
                if response.parts:
                    for part in response.parts:
                        if part.text:
                            text_output += part.text + "\n"
                        elif part.inline_data:
                            # Convert inline data to image
                            image_data = part.inline_data.data # bytes
                            image = Image.open(io.BytesIO(image_data))
                            
                            # Convert back to CV2 for internal state
                            new_cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                            image_found = True
                
                # Schedule UI update on main thread
                self.after(0, lambda: self._handle_ai_response(text_output, new_cv_img, image_found))

            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self._handle_ai_error(err_msg))
        
        threading.Thread(target=_process, daemon=True).start()

    def _handle_ai_response(self, text_output, new_cv_img, image_found):
        if image_found and new_cv_img is not None:
            self.cv_img = new_cv_img
            self.viewer.load_image(self.cv_img)
            self.processed_img = self.cv_img
            
            # Add to history
            self.history.add(self.cv_img)
            self.update_history_buttons()
            self.update_info_header()
            
            # --- Auto-Save Logic ---
            try:
                timestamp = int(time.time())
                save_name = f"{self.current_image_path.stem}_gen_{timestamp}.png"
                save_path = self.current_image_path.parent / save_name
                cv2.imwrite(str(save_path), self.cv_img)
                self.status_label.configure(text=f"Saved: {save_name}", text_color="green")
                print(f"Auto-saved to: {save_path}")
            except Exception as e:
                print(f"Auto-save failed: {e}")
                self.status_label.configure(text="Generated (Auto-save failed)", text_color="orange")
        
        if text_output:
            if self.tab_view.get() == "Analysis":
                self.txt_analysis.delete("1.0", "end")
                self.txt_analysis.insert("1.0", text_output)
                if not image_found: self.status_label.configure(text="Analysis Complete", text_color="green")
            elif not image_found:
                # If we expected an image but got text (e.g. refusal or description)
                messagebox.showinfo("AI Response", f"Model returned text:\n\n{text_output}")
                self.status_label.configure(text="Text Response Received", text_color="green")

    def _handle_ai_error(self, err_msg):
        if "429" in err_msg or "Quota" in err_msg or "ResourceExhausted" in err_msg:
            self.status_label.configure(text="Error: Quota Exceeded", text_color="red")
            messagebox.showerror("API Error", "Gemini API Quota Exceeded.\nPlease wait a minute or check your plan.")
        else:
            self.status_label.configure(text="Error: API Failed", text_color="red")
            print(f"API Error: {err_msg}")
            messagebox.showerror("API Error", f"An error occurred:\n{err_msg[:200]}...")

    def run_analysis(self):
        # Switch to Analysis tab to ensure output is visible
        self.tab_view.set("Analysis")
        # Update prompt for analysis
        self.update_prompt_from_ui()
        # Run the request
        self.run_ai_request()
        
    def save_result(self):
        if not hasattr(self, 'processed_img') or self.processed_img is None:
             self.processed_img = self.cv_img
             
        from tkinter import filedialog
        initial_name = f"{self.current_image_path.stem}_edited.png"
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=initial_name)
        if path:
            # Use unique path if file exists (though dialog usually handles this, we enforce policy)
            save_path = Path(path)
            if save_path.exists():
                save_path = get_unique_path(save_path)
                
            cv2.imwrite(str(save_path), self.processed_img)
            messagebox.showinfo("Saved", f"Saved to {save_path.name}")

    def copy_to_clipboard(self):
        """Copy current image to clipboard using PowerShell."""
        if self.cv_img is None: return
        
        try:
            # Save to temp file
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                
            cv2.imwrite(str(tmp_path), self.cv_img)
            
            # PowerShell command to set clipboard
            cmd = f"Set-Clipboard -Path '{str(tmp_path)}'"
            subprocess.run(["powershell", "-Command", cmd], check=True)
            
            # Clean up (optional, but good practice. Windows might lock it briefly)
            # self.after(1000, lambda: tmp_path.unlink(missing_ok=True)) 
            
            self.status_label.configure(text="Copied to Clipboard", text_color="green")
            
        except Exception as e:
            print(f"Clipboard Error: {e}")
            self.status_label.configure(text="Clipboard Error", text_color="red")

    def show_prompt_json(self):
        """Show the current prompt in a JSON format."""
        import json
        prompt = self.prompt_entry.get("1.0", "end").strip()
        
        data = {
            "system_instruction": "You are a texture generation expert...", # Simplified for view
            "user_prompt": prompt,
            "model": "gemini-2.5-flash-image" if self.tab_view.get() != "Analysis" else "gemini-2.5-flash"
        }
        
        json_str = json.dumps(data, indent=2)
        
        # Popup
        top = ctk.CTkToplevel(self)
        top.title("Prompt Inspection")
        top.geometry("500x400")
        
        txt = ctk.CTkTextbox(top, font=("Consolas", 12))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", json_str)

    def close_image(self):
        self.cv_img = None
        self.original_img = None
        self.viewer.image = None
        self.viewer.canvas.delete("all")
        self.lbl_info.configure(text="No Image Loaded")
        self.lbl_counter.configure(text="- / -")
        self.status_label.configure(text="Image Closed", text_color="gray")
        # Clear history
        self.history = HistoryManager(current_dir / ".cache")
        self.update_history_buttons()

    def paste_from_clipboard(self, event=None):
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                # Convert to CV2
                cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                self.load_new_image_from_cv(cv_img, "Clipboard_Image")
            elif isinstance(img, list): # File paths
                self.load_new_image(img[0])
        except Exception as e:
            print(f"Clipboard error: {e}")

    def open_file_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tga")])
        if path:
            self.load_new_image(path)

    def load_new_image(self, path):
        print(f"DEBUG: Loading new image from {path}")
        try:
            cv_img = imread_unicode(str(path))
            if cv_img is None:
                print("DEBUG: Failed to read image (None result)")
                messagebox.showerror("Error", "Failed to load image.\nFormat not supported or file corrupted.")
                return
                
            self.current_image_path = Path(path)
            self.load_new_image_from_cv(cv_img, self.current_image_path.name)
            
        except Exception as e:
            print(f"ERROR in load_new_image: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def load_new_image_from_cv(self, cv_img, name="Image"):
        self.cv_img = cv_img
        self.original_img = cv_img.copy()
        
        # Reset History for new image
        self.history = HistoryManager(current_dir / ".cache")
        self.history.add(self.cv_img)
        
        self.viewer.load_image(self.cv_img)
        self.update_history_buttons()
        
        # Update Info
        h, w = self.cv_img.shape[:2]
        folder = self.current_image_path.parent.name if hasattr(self, 'current_image_path') else "Clipboard"
        self.lbl_info.configure(text=f"File: {name} | Folder: {folder} | Res: {w}x{h}")
        self.status_label.configure(text="Image Loaded", text_color="green")

    def generate_all_pbr(self):
        # Create a new folder for PBR maps
        pbr_dir = self.current_image_path.parent / f"{self.current_image_path.stem}_PBR_Gen"
        pbr_dir.mkdir(exist_ok=True)
        
        base_name = self.current_image_path.stem
        
        def _update_status(text, color="yellow"):
            self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

        def _show_success(count):
            self.after(0, lambda: messagebox.showinfo("Success", f"Generated {count} maps."))

        def _show_error(e):
            self.after(0, lambda: self.status_label.configure(text=f"Error: {e}", text_color="red"))
            print(e)

        def _process():
            count = 0
            try:
                if self.var_normal.get():
                    _update_status("Generating Normal...")
                    res = generate_normal_map(self.cv_img, self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Normal.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_rough.get():
                    _update_status("Generating Roughness...")
                    res = generate_roughness_map(self.cv_img, self.var_invert.get(), contrast=self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Roughness.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_disp.get():
                    _update_status("Generating Displacement...")
                    res = generate_displacement_map(self.cv_img)
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Displacement.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_occ.get():
                    _update_status("Generating Occlusion...")
                    res = generate_occlusion_map(self.cv_img, self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Occlusion.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_metal.get():
                    _update_status("Generating Metallic...")
                    res = generate_metallic_map(self.cv_img, self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Metallic.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_orm.get():
                    _update_status("Generating ORM Pack...")
                    occ = generate_occlusion_map(self.cv_img, self.slider_strength.get())
                    rough = generate_roughness_map(self.cv_img, self.var_invert.get(), contrast=self.slider_strength.get())
                    metal = generate_metallic_map(self.cv_img, self.slider_strength.get())
                    
                    if len(occ.shape) == 3: occ = cv2.cvtColor(occ, cv2.COLOR_BGR2GRAY)
                    if len(rough.shape) == 3: rough = cv2.cvtColor(rough, cv2.COLOR_BGR2GRAY)
                    if len(metal.shape) == 3: metal = cv2.cvtColor(metal, cv2.COLOR_BGR2GRAY)
                    
                    orm = cv2.merge([occ, rough, metal])
                    cv2.imwrite(str(pbr_dir / f"{base_name}_ORM.png"), orm)
                    count += 1
                
                _update_status(f"Saved {count} maps", "green")
                _show_success(count)
                
            except Exception as e:
                _show_error(e)

        threading.Thread(target=_process, daemon=True).start()
        
    def apply_offset(self):
        res = make_tileable_synthesis(self.cv_img)
        self.viewer.load_image(res)
        self.processed_img = res
        self.status_label.configure(text="Applied Offset", text_color="green")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app = GeminiImageToolsGUI(sys.argv[1])
        app.mainloop()
