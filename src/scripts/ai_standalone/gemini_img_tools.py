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
from tkinter import messagebox, Canvas
import io

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
        # Force update to ensure canvas has dimensions before loading image
        self.update() 
        self.viewer.load_image(self.cv_img)

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
        
        # Status Label
        self.status_label = ctk.CTkLabel(self.right_panel, text="Ready", text_color="gray", font=("Arial", 12))
        self.status_label.pack(side="top", anchor="ne", padx=10, pady=5)
        
        # Image Viewer
        self.viewer = ImageViewer(self.right_panel)
        self.viewer.pack(fill="both", expand=True)

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
        ctk.CTkLabel(self.bottom_bar, text="AI Prompt:").pack(anchor="w", padx=10, pady=(5,0))
        self.prompt_entry = ctk.CTkTextbox(self.bottom_bar, height=50)
        self.prompt_entry.pack(fill="x", padx=10, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(btn_frame, text="Reset to Original", command=self.reset_image, fg_color="gray", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Generate (Gemini 2.5)", command=self.run_ai_request, fg_color="#1f6aa5", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Save Result", command=self.save_result, fg_color="green", width=120).pack(side="right", padx=5)

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
        ctk.CTkLabel(self.tab_tile, text="Make Tileable", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.tab_tile, text="Method: Offset & Blur (Local)").pack(pady=5)
        ctk.CTkButton(self.tab_tile, text="Apply Offset", command=self.apply_offset).pack(pady=10)
        
        ctk.CTkLabel(self.tab_tile, text="AI Infill / Scale:").pack(pady=(20, 5))
        self.var_ai_infill = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.tab_tile, text="Enable AI Infill", variable=self.var_ai_infill, command=self.update_prompt_from_ui).pack(pady=5)
        
        self.slider_tile_scale = ctk.CTkSlider(self.tab_tile, from_=0.1, to=10.0, number_of_steps=100, command=self.update_prompt_from_ui)
        self.slider_tile_scale.set(1.0)
        self.slider_tile_scale.pack(fill="x", padx=10)

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
        prompt = ""
        
        # Global Type Context
        img_type = self.image_type.get()
        type_context = f"Input image is a {img_type}." if img_type != "Select Type" else ""

        if tab == "Style":
            style = self.style_mode.get()
            strength = self.slider_style_strength.get()
            # Convert strength to descriptive text for better AI adherence
            str_desc = "subtle" if strength < 0.3 else "moderate" if strength < 0.7 else "strong"
            prompt = f"{type_context} Transform this texture into {style} style. Style strength: {str_desc} ({strength:.1f}). Maintain the original structure and composition."
            
        elif tab == "PBR Gen":
            ai_target = self.pbr_ai_target.get()
            if ai_target == "None (Local Only)":
                prompt = "AI Generation is disabled in this mode. Use 'Generate PBR Maps (Local)' button above, or select a map type to generate via AI."
            else:
                prompt = f"{type_context} Generate a high-quality {ai_target} for this texture. Ensure it is accurate and aligned with the original details."
            scale = self.slider_tile_scale.get()
            infill = "Enable AI Infill to generate missing details and expand borders." if self.var_ai_infill.get() else ""
            prompt = f"{type_context} Make this texture seamless and tileable. Scale pattern by {scale:.1f}x. Fix edges and blend seams naturally. {infill}"
            
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
                instruction = "Analyze this texture and provide a comma-separated list of keywords (tags) suitable for Stable Diffusion/ComfyUI positive prompt. Include material tags, quality tags, and lighting tags."
            else:
                instruction = "Analyze this texture in detail. Describe its material, pattern, roughness, and suggest PBR settings."
            
            prompt = f"{type_context} {instruction} Output text only. Do not generate an image."

        elif tab == "Outpaint":
            direction = self.outpaint_dir.get()
            scale = self.slider_outpaint.get()
            prompt = f"{type_context} Outpaint this image. Expand the canvas in {direction} direction(s) by {scale:.1f}x. Fill the new areas naturally matching the existing texture."

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
        self.status_label.configure(text="Reset to Original", text_color="green")

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
                self.status_label.configure(text="Sending to Gemini 2.5...", text_color="yellow")
                
                # Prepare Image
                rgb_img = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_img)
                
                # Call Gemini 2.5 Flash Image
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt, pil_img]
                )
                
                # Handle Response Parts
                text_output = ""
                image_found = False
                
                if response.parts:
                    for part in response.parts:
                        if part.text:
                            text_output += part.text + "\n"
                        elif part.inline_data:
                            # Convert inline data to image
                            image_data = part.inline_data.data # bytes
                            image = Image.open(io.BytesIO(image_data))
                            
                            # Convert back to CV2 for internal state
                            self.cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                            self.viewer.load_image(self.cv_img)
                            self.processed_img = self.cv_img
                            image_found = True
                            self.status_label.configure(text="Image Generated", text_color="green")
                
                if text_output:
                    if self.tab_view.get() == "Analysis":
                        self.txt_analysis.delete("1.0", "end")
                        self.txt_analysis.insert("1.0", text_output)
                        self.status_label.configure(text="Analysis Complete", text_color="green")
                    elif not image_found:
                        # If we expected an image but got text (e.g. refusal or description)
                        messagebox.showinfo("AI Response", f"Model returned text:\n\n{text_output}")
                        self.status_label.configure(text="Text Response Received", text_color="green")

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "Quota" in err_msg or "ResourceExhausted" in err_msg:
                    self.status_label.configure(text="Error: Quota Exceeded", text_color="red")
                    messagebox.showerror("API Error", "Gemini API Quota Exceeded.\nPlease wait a minute or check your plan.")
                else:
                    self.status_label.configure(text="Error: API Failed", text_color="red")
                    print(f"API Error: {e}")
                    messagebox.showerror("API Error", f"An error occurred:\n{err_msg[:200]}...")
        
        threading.Thread(target=_process, daemon=True).start()

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
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=f"{self.current_image_path.stem}_edited.png")
        if path:
            cv2.imwrite(path, self.processed_img)
            messagebox.showinfo("Saved", f"Saved to {path}")

    def generate_all_pbr(self):
        # Create a new folder for PBR maps
        pbr_dir = self.current_image_path.parent / f"{self.current_image_path.stem}_PBR_Gen"
        pbr_dir.mkdir(exist_ok=True)
        
        base_name = self.current_image_path.stem
        
        def _process():
            count = 0
            try:
                if self.var_normal.get():
                    self.status_label.configure(text="Generating Normal...", text_color="yellow")
                    res = generate_normal_map(self.cv_img, self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Normal.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_rough.get():
                    self.status_label.configure(text="Generating Roughness...", text_color="yellow")
                    res = generate_roughness_map(self.cv_img, self.var_invert.get(), contrast=self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Roughness.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_disp.get():
                    self.status_label.configure(text="Generating Displacement...", text_color="yellow")
                    res = generate_displacement_map(self.cv_img)
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Displacement.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_occ.get():
                    self.status_label.configure(text="Generating Occlusion...", text_color="yellow")
                    res = generate_occlusion_map(self.cv_img, self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Occlusion.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_metal.get():
                    self.status_label.configure(text="Generating Metallic...", text_color="yellow")
                    res = generate_metallic_map(self.cv_img, self.slider_strength.get())
                    cv2.imwrite(str(pbr_dir / f"{base_name}_Metallic.png"), res)
                    count += 1
                    time.sleep(0.1)
                    
                if self.var_orm.get():
                    self.status_label.configure(text="Generating ORM Pack...", text_color="yellow")
                    occ = generate_occlusion_map(self.cv_img, self.slider_strength.get())
                    rough = generate_roughness_map(self.cv_img, self.var_invert.get(), contrast=self.slider_strength.get())
                    metal = generate_metallic_map(self.cv_img, self.slider_strength.get())
                    
                    if len(occ.shape) == 3: occ = cv2.cvtColor(occ, cv2.COLOR_BGR2GRAY)
                    if len(rough.shape) == 3: rough = cv2.cvtColor(rough, cv2.COLOR_BGR2GRAY)
                    if len(metal.shape) == 3: metal = cv2.cvtColor(metal, cv2.COLOR_BGR2GRAY)
                    
                    orm = cv2.merge([occ, rough, metal])
                    cv2.imwrite(str(pbr_dir / f"{base_name}_ORM.png"), orm)
                    count += 1
                
                self.status_label.configure(text=f"Saved {count} maps", text_color="green")
                messagebox.showinfo("Success", f"Generated {count} maps.")
                
            except Exception as e:
                self.status_label.configure(text=f"Error: {e}", text_color="red")
                print(e)

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
