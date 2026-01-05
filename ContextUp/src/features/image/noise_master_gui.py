"""
Noise Master GUI (GPU-first).
"""

from __future__ import annotations

import sys
import threading
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from tkinter import messagebox, filedialog

import customtkinter as ctk
from PIL import Image, ImageTk

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

from utils.gui_lib import setup_theme, THEME_CARD, THEME_BORDER, THEME_BTN_PRIMARY, THEME_BTN_HOVER, THEME_BTN_DANGER, THEME_BTN_DANGER_HOVER
from features.image.noise_master import NoiseRenderer, LayerConfig, to_8bit_image, to_16bit_image, generate_normal_map
from features.image.noise_master.gui_widgets import SliderWithInput, CollapsibleSection, LayerItem
from features.image.noise_master.gpu_backend import GPU_AVAILABLE
DEFAULT_RENDER_SIZE = 512
INTERACTIVE_RENDER_SIZE = 256
GPU_PREVIEW_DOWNSAMPLE = 128
PREVIEW_DISPLAY_SIZE = 512

NOISE_TYPES = [
    "fbm",
    "perlin",
    "simplex",
    "voronoi",
    "wave",
    "magic",
    "gradient",
    "brick",
    "white_noise",
    "gabor",
]

LAYER_KINDS = ["Generator", "Effect"]

EFFECT_TYPES = [
    "Warp",
    "Erosion",
    "Tone",
    "Clamp",
    "Normalize",
    "Quantize",
    "Blur",
    "Sharpen",
    "Invert",
    "Ridged",
    "Slope",
    "Curvature",
]

MASK_MODES = ["Multiply", "Add", "Subtract", "Max", "Min"]
CURVATURE_MODES = ["Cavity", "Ridge", "Abs"]

VORONOI_RETURN_TYPES = ["F1", "F2", "Smooth F1", "Distance to Edge", "N-Sphere Radius"]
VORONOI_OUTPUTS = ["Distance", "Color", "Position", "Radius"]
VORONOI_METRICS = ["Euclidean", "Manhattan", "Chebyshev", "Minkowski"]

GRADIENT_TYPES = [
    "Linear",
    "Quadratic",
    "Easing",
    "Diagonal",
    "Radial",
    "Sphere",
    "Quadratic Sphere",
]

WAVE_TYPES = ["Bands", "Rings"]
WAVE_DIRS = ["X", "Y", "Z", "Diagonal"]
WAVE_PROFILES = ["Sine", "Saw", "Tri"]

FRACTAL_TYPES = ["FBM", "Multifractal", "Hybrid", "Ridged", "Hetero"]

OUTPUT_MODES = ["Heightmap", "Normal"]
NORMAL_FORMATS = ["OpenGL", "DirectX"]
BIT_DEPTHS = ["8-bit", "16-bit"]


def _default_layer(name: str) -> dict:
    cfg = LayerConfig()
    data = asdict(cfg)
    data["uid"] = uuid.uuid4().hex
    data["name"] = name
    return data


def _default_effect_layer(name: str) -> dict:
    data = _default_layer(name)
    data["layer_kind"] = "effect"
    data["effect_type"] = "warp"
    data["input_source"] = "stack_below"
    data["masks"] = []
    return data


def _clamp(value: float, vmin: float, vmax: float) -> float:
    return max(vmin, min(vmax, value))


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


class NoiseMasterWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_theme()

        self.title("Noise Master (GPU)")
        self.geometry("1400x900")
        self.minsize(1100, 700)

        self.render_size = DEFAULT_RENDER_SIZE
        self.preview_display_size = PREVIEW_DISPLAY_SIZE
        self.use_gpu = True
        self.preview_downsample = GPU_PREVIEW_DOWNSAMPLE if GPU_AVAILABLE else None

        self.renderer = NoiseRenderer(self.render_size, self.render_size)

        self.layers = [_default_layer("Layer 1")]
        self.selected_idx = 0

        self._render_request_id = 0
        self._render_after_id = None
        self._rendering_after_id = None
        self._render_thread = None
        self._pending_full = False
        self._render_busy = False
        self._last_render_time = 0.0
        self._suspend_updates = False

        self._build_ui()
        self._refresh_layers()
        self._load_selected_layer()
        self._schedule_render(full=True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_layer_panel()
        self._build_preview_panel()
        self._build_property_panel()
    def _build_top_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
        bar.grid_columnconfigure(8, weight=1)

        ctk.CTkLabel(bar, text="Resolution").grid(row=0, column=0, padx=(0, 6))
        self.size_var = ctk.StringVar(value=str(self.render_size))
        size_menu = ctk.CTkOptionMenu(
            bar, variable=self.size_var,
            values=["256", "512", "1024", "2048"],
            command=self._on_size_change, width=80
        )
        size_menu.grid(row=0, column=1, padx=(0, 12))

        self.btn_render = ctk.CTkButton(
            bar, text="Render", width=80,
            fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER,
            command=lambda: self._schedule_render(full=True)
        )
        self.btn_render.grid(row=0, column=2, padx=(0, 8))

        self.btn_export = ctk.CTkButton(
            bar, text="Export", width=80,
            fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER,
            command=self._export_image
        )
        self.btn_export.grid(row=0, column=3, padx=(0, 8))

        gpu_text = "GPU: Available" if GPU_AVAILABLE else "GPU: CPU fallback"
        self.lbl_gpu = ctk.CTkLabel(bar, text=gpu_text, text_color="gray")
        self.lbl_gpu.grid(row=0, column=4, padx=(0, 12))

        self.lbl_time = ctk.CTkLabel(bar, text="", text_color="gray")
        self.lbl_time.grid(row=0, column=5, padx=(0, 12))

    def _build_layer_panel(self):
        panel = ctk.CTkFrame(
            self, fg_color=THEME_CARD, corner_radius=8,
            border_color=THEME_BORDER, border_width=1
        )
        panel.grid(row=1, column=0, sticky="ns", padx=8, pady=8)
        panel.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

        ctk.CTkLabel(header, text="Layers", font=("", 12, "bold")).pack(side="left")

        btn_add = ctk.CTkButton(
            header, text="+", width=24, height=24,
            fg_color=THEME_BTN_PRIMARY, hover_color=THEME_BTN_HOVER,
            command=self._add_layer
        )
        btn_add.pack(side="right", padx=2)

        btn_add_fx = ctk.CTkButton(
            header, text="FX", width=32, height=24,
            fg_color="#2d6a4f", hover_color="#1b4332",
            command=self._add_effect_layer
        )
        btn_add_fx.pack(side="right", padx=2)

        btn_dup = ctk.CTkButton(
            header, text="Dup", width=40, height=24,
            fg_color="#444", hover_color="#555",
            command=self._duplicate_layer
        )
        btn_dup.pack(side="right", padx=2)

        btn_del = ctk.CTkButton(
            header, text="Del", width=40, height=24,
            fg_color=THEME_BTN_DANGER, hover_color=THEME_BTN_DANGER_HOVER,
            command=self._delete_layer
        )
        btn_del.pack(side="right", padx=2)

        self.layer_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent", width=260, height=600)
        self.layer_scroll.grid(row=1, column=0, sticky="ns", padx=6, pady=(0, 6))

    def _build_preview_panel(self):
        panel = ctk.CTkFrame(
            self, fg_color=THEME_CARD, corner_radius=8,
            border_color=THEME_BORDER, border_width=1
        )
        panel.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(panel, text="")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.render_overlay = ctk.CTkLabel(
            panel, text="RENDERING...", text_color="#cccccc",
            fg_color="#222222", corner_radius=6
        )
        self.render_overlay.place_forget()

        self.status_label = ctk.CTkLabel(panel, text="", text_color="gray")
        self.status_label.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))

    def _build_property_panel(self):
        panel = ctk.CTkFrame(
            self, fg_color=THEME_CARD, corner_radius=8,
            border_color=THEME_BORDER, border_width=1
        )
        panel.grid(row=1, column=2, sticky="ns", padx=8, pady=8)
        panel.grid_rowconfigure(0, weight=1)

        self.prop_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent", width=380)
        self.prop_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.controls = {}

        self.section_general = CollapsibleSection(self.prop_scroll, "General", expanded=True)
        self.section_general.pack(fill="x", pady=4)
        self._build_section_general(self.section_general.content)

        self.section_transform = CollapsibleSection(self.prop_scroll, "Transform", expanded=False)
        self.section_transform.pack(fill="x", pady=4)
        self._build_section_transform(self.section_transform.content)

        self.section_fbm = CollapsibleSection(self.prop_scroll, "Fractal", expanded=False)
        self.section_fbm.pack(fill="x", pady=4)
        self._build_section_fbm(self.section_fbm.content)

        self.section_voronoi = CollapsibleSection(self.prop_scroll, "Voronoi", expanded=False)
        self.section_voronoi.pack(fill="x", pady=4)
        self._build_section_voronoi(self.section_voronoi.content)

        self.section_wave = CollapsibleSection(self.prop_scroll, "Wave", expanded=False)
        self.section_wave.pack(fill="x", pady=4)
        self._build_section_wave(self.section_wave.content)

        self.section_magic = CollapsibleSection(self.prop_scroll, "Magic", expanded=False)
        self.section_magic.pack(fill="x", pady=4)
        self._build_section_magic(self.section_magic.content)

        self.section_gradient = CollapsibleSection(self.prop_scroll, "Gradient", expanded=False)
        self.section_gradient.pack(fill="x", pady=4)
        self._build_section_gradient(self.section_gradient.content)

        self.section_brick = CollapsibleSection(self.prop_scroll, "Brick", expanded=False)
        self.section_brick.pack(fill="x", pady=4)
        self._build_section_brick(self.section_brick.content)

        self.section_gabor = CollapsibleSection(self.prop_scroll, "Gabor", expanded=False)
        self.section_gabor.pack(fill="x", pady=4)
        self._build_section_gabor(self.section_gabor.content)

        self.section_effect = CollapsibleSection(self.prop_scroll, "Effect", expanded=False)
        self.section_effect.pack(fill="x", pady=4)
        self._build_section_effect(self.section_effect.content)

        self.section_masks = CollapsibleSection(self.prop_scroll, "Masks", expanded=False)
        self.section_masks.pack(fill="x", pady=4)
        self._build_section_masks(self.section_masks.content)

        self.section_fx_warp = CollapsibleSection(self.prop_scroll, "FX Warp", expanded=False)
        self.section_fx_warp.pack(fill="x", pady=4)
        self._build_section_fx_warp(self.section_fx_warp.content)

        self.section_fx_erosion = CollapsibleSection(self.prop_scroll, "FX Erosion", expanded=False)
        self.section_fx_erosion.pack(fill="x", pady=4)
        self._build_section_fx_erosion(self.section_fx_erosion.content)

        self.section_fx_tone = CollapsibleSection(self.prop_scroll, "FX Tone", expanded=False)
        self.section_fx_tone.pack(fill="x", pady=4)
        self._build_section_fx_tone(self.section_fx_tone.content)

        self.section_fx_clamp = CollapsibleSection(self.prop_scroll, "FX Clamp", expanded=False)
        self.section_fx_clamp.pack(fill="x", pady=4)
        self._build_section_fx_clamp(self.section_fx_clamp.content)

        self.section_fx_quantize = CollapsibleSection(self.prop_scroll, "FX Quantize", expanded=False)
        self.section_fx_quantize.pack(fill="x", pady=4)
        self._build_section_fx_quantize(self.section_fx_quantize.content)

        self.section_fx_blur = CollapsibleSection(self.prop_scroll, "FX Blur", expanded=False)
        self.section_fx_blur.pack(fill="x", pady=4)
        self._build_section_fx_blur(self.section_fx_blur.content)

        self.section_fx_sharpen = CollapsibleSection(self.prop_scroll, "FX Sharpen", expanded=False)
        self.section_fx_sharpen.pack(fill="x", pady=4)
        self._build_section_fx_sharpen(self.section_fx_sharpen.content)

        self.section_fx_slope = CollapsibleSection(self.prop_scroll, "FX Slope", expanded=False)
        self.section_fx_slope.pack(fill="x", pady=4)
        self._build_section_fx_slope(self.section_fx_slope.content)

        self.section_fx_curvature = CollapsibleSection(self.prop_scroll, "FX Curvature", expanded=False)
        self.section_fx_curvature.pack(fill="x", pady=4)
        self._build_section_fx_curvature(self.section_fx_curvature.content)

        self.section_output = CollapsibleSection(self.prop_scroll, "Output", expanded=False)
        self.section_output.pack(fill="x", pady=4)
        self._build_section_output(self.section_output.content)

        self.type_sections = {
            "fbm": [self.section_fbm],
            "perlin": [self.section_fbm],
            "simplex": [self.section_fbm],
            "voronoi": [self.section_voronoi],
            "cellular": [self.section_voronoi],
            "wave": [self.section_wave],
            "magic": [self.section_magic],
            "gradient": [self.section_gradient],
            "brick": [self.section_brick],
            "white_noise": [],
            "gabor": [self.section_gabor],
        }
        self.effect_sections = {
            "warp": [self.section_fx_warp],
            "erosion": [self.section_fx_erosion],
            "tone": [self.section_fx_tone],
            "clamp": [self.section_fx_clamp],
            "normalize": [],
            "quantize": [self.section_fx_quantize],
            "blur": [self.section_fx_blur],
            "sharpen": [self.section_fx_sharpen],
            "invert": [],
            "ridged": [],
            "slope": [self.section_fx_slope],
            "curvature": [self.section_fx_curvature],
        }
    def _build_section_general(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Name", width=90, anchor="w").pack(side="left")
        self.var_name = ctk.StringVar()
        self.entry_name = ctk.CTkEntry(row, textvariable=self.var_name, width=160)
        self.entry_name.pack(side="left", padx=5)
        self.entry_name.bind("<Return>", self._on_name_change)
        self.entry_name.bind("<FocusOut>", self._on_name_change)

        self._add_option(parent, "Layer Kind", "layer_kind", LAYER_KINDS, self._on_kind_change)
        self._add_option(parent, "Type", "type", NOISE_TYPES, self._on_type_change)
        self.chk_seamless = self._add_toggle(parent, "Seamless", "seamless")
        self.chk_normalize = self._add_toggle(parent, "Normalize", "normalize")
        self._add_slider(parent, "Seed", "seed", 0, 10000, is_int=True)
        self._add_slider(parent, "Evolution", "evolution", 0.0, 10.0)
        self._add_slider(parent, "Noise Scale", "noise_scale", 0.1, 20.0)

    def _build_section_transform(self, parent):
        self._add_slider(parent, "Scale", "scale", 0.1, 10.0)
        self._add_slider(parent, "Ratio", "ratio", -2.0, 2.0)
        self._add_slider(parent, "Rotation", "rotation", -180.0, 180.0)
        self._add_slider(parent, "Offset X", "offset_x", -5.0, 5.0)
        self._add_slider(parent, "Offset Y", "offset_y", -5.0, 5.0)

    def _build_section_fbm(self, parent):
        self._add_option(parent, "Noise Type", "noise_type", FRACTAL_TYPES)
        self._add_slider(parent, "Detail", "detail", 0.0, 15.0)
        self._add_slider(parent, "Roughness", "roughness", 0.0, 1.0)
        self._add_slider(parent, "Lacunarity", "lacunarity", 0.5, 4.0)
        self._add_slider(parent, "Distortion", "distortion", 0.0, 2.0)
        self._add_slider(parent, "Offset", "noise_offset", -1.0, 1.0)
        self._add_slider(parent, "Gain", "noise_gain", 0.0, 2.0)
    def _build_section_voronoi(self, parent):
        self._add_slider(parent, "Jitter", "jitter", 0.0, 1.0)
        self._add_option(parent, "Metric", "distance_metric", VORONOI_METRICS)
        self._add_option(parent, "Feature", "return_type", VORONOI_RETURN_TYPES)
        self._add_slider(parent, "Smooth", "smoothness", 0.0, 1.0)
        self._add_slider(parent, "Exponent", "exponent", 0.1, 4.0)
        self._add_slider(parent, "Detail", "detail", 0.0, 10.0)
        self._add_slider(parent, "Roughness", "roughness", 0.0, 1.0)
        self._add_slider(parent, "Lacunarity", "lacunarity", 0.5, 4.0)
        self._add_option(parent, "Output", "voronoi_output", VORONOI_OUTPUTS)

    def _build_section_wave(self, parent):
        self._add_option(parent, "Type", "wave_type", WAVE_TYPES)
        self._add_option(parent, "Bands Dir", "wave_dir", WAVE_DIRS)
        self._add_option(parent, "Rings Dir", "wave_rings_dir", WAVE_DIRS)
        self._add_option(parent, "Profile", "wave_profile", WAVE_PROFILES)
        self._add_slider(parent, "Phase", "phase_offset", 0.0, 6.283)
        self._add_slider(parent, "Distortion", "distortion", 0.0, 2.0)
        self._add_slider(parent, "Detail", "detail", 0.0, 6.0)
        self._add_slider(parent, "Detail Scale", "wave_detail_scale", 0.1, 5.0)
        self._add_slider(parent, "Detail Rough", "wave_detail_roughness", 0.0, 1.0)

    def _build_section_magic(self, parent):
        self._add_slider(parent, "Depth", "depth", 0, 10, is_int=True)
        self._add_slider(parent, "Distortion", "distortion", 0.0, 2.0)

    def _build_section_gradient(self, parent):
        self._add_option(parent, "Type", "subtype", GRADIENT_TYPES)

    def _build_section_brick(self, parent):
        self._add_slider(parent, "Row Offset", "row_offset", 0.0, 1.0)
        self._add_slider(parent, "Brick Ratio", "brick_ratio", 0.1, 1.0)
        self._add_slider(parent, "Row Height", "brick_row_height", 0.05, 1.0)
        self._add_slider(parent, "Offset Freq", "brick_offset_frequency", 1, 6, is_int=True)
        self._add_slider(parent, "Squash", "brick_squash", 0.2, 2.0)
        self._add_slider(parent, "Squash Freq", "brick_squash_frequency", 1, 6, is_int=True)
        self._add_slider(parent, "Mortar", "mortar_size", 0.0, 0.2)
        self._add_slider(parent, "Mortar Smooth", "mortar_smooth", 0.0, 1.0)

    def _build_section_gabor(self, parent):
        self._add_slider(parent, "Frequency", "gabor_frequency", 0.0, 10.0)
        self._add_slider(parent, "Anisotropy", "gabor_anisotropy", 0.0, 1.0)
        self._add_slider(parent, "Orientation", "gabor_orientation", 0.0, 360.0)
    def _build_section_effect(self, parent):
        self._add_option(parent, "Effect Type", "effect_type", EFFECT_TYPES, self._on_effect_type_change)

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Input", width=90, anchor="w").pack(side="left")
        self.input_source_var = ctk.StringVar(value="Stack Below")
        self.input_source_menu = ctk.CTkOptionMenu(
            row, variable=self.input_source_var, values=["Stack Below"],
            width=160, command=self._on_input_source_change
        )
        self.input_source_menu.pack(side="left", padx=5)

        self._add_toggle(parent, "Bypass", "bypass")

    def _build_section_masks(self, parent):
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", pady=2)
        ctk.CTkLabel(btn_row, text="Masks", width=90, anchor="w").pack(side="left")
        btn_add = ctk.CTkButton(btn_row, text="Add Mask", width=90, command=self._add_mask)
        btn_add.pack(side="left", padx=5)

        self.mask_list = ctk.CTkFrame(parent, fg_color="transparent")
        self.mask_list.pack(fill="x", pady=2)

    def _build_section_fx_warp(self, parent):
        self._add_option(parent, "Warp Type", "warp_type", ["fbm", "perlin", "simplex", "voronoi", "wave", "magic"])
        self._add_slider(parent, "Strength", "warp_strength", 0.0, 2.0)
        self._add_slider(parent, "Scale", "warp_scale", 0.1, 10.0)
        self._add_slider(parent, "Seed", "warp_seed", 0, 10000, is_int=True)

    def _build_section_fx_erosion(self, parent):
        self._add_option(parent, "Type", "erosion_type", ["thermal", "hydraulic"])
        self._add_slider(parent, "Iterations", "erosion_iterations", 1, 80, is_int=True)
        self._add_slider(parent, "Rain", "erosion_rain", 0.0, 1.0)
        self._add_slider(parent, "Evap", "erosion_evap", 0.0, 1.0)
        self._add_slider(parent, "Solubility", "erosion_solu", 0.0, 1.0)

    def _build_section_fx_tone(self, parent):
        self._add_slider(parent, "Gain", "tone_gain", 0.0, 3.0)
        self._add_slider(parent, "Bias", "tone_bias", -1.0, 1.0)
        self._add_slider(parent, "Gamma", "tone_gamma", 0.2, 3.0)
        self._add_slider(parent, "Contrast", "tone_contrast", 0.0, 3.0)

    def _build_section_fx_clamp(self, parent):
        self._add_slider(parent, "Min", "clamp_min", 0.0, 1.0)
        self._add_slider(parent, "Max", "clamp_max", 0.0, 1.0)

    def _build_section_fx_quantize(self, parent):
        self._add_slider(parent, "Steps", "quantize_steps", 2, 16, is_int=True)

    def _build_section_fx_blur(self, parent):
        self._add_slider(parent, "Radius", "blur_radius", 0, 8, is_int=True)
        self._add_slider(parent, "Strength", "blur_strength", 0.0, 1.0)

    def _build_section_fx_sharpen(self, parent):
        self._add_slider(parent, "Radius", "sharpen_radius", 0, 8, is_int=True)
        self._add_slider(parent, "Strength", "sharpen_strength", 0.0, 2.0)

    def _build_section_fx_slope(self, parent):
        self._add_slider(parent, "Strength", "slope_strength", 0.0, 5.0)

    def _build_section_fx_curvature(self, parent):
        self._add_option(parent, "Mode", "curvature_mode", CURVATURE_MODES)
        self._add_slider(parent, "Strength", "curvature_strength", 0.0, 5.0)

    def _build_section_output(self, parent):
        self.output_seamless_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            parent, text="Output Seamless",
            variable=self.output_seamless_var,
            command=self._on_output_seamless_change
        ).pack(anchor="w", pady=2)

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Mode", width=90, anchor="w").pack(side="left")
        self.output_mode_var = ctk.StringVar(value=OUTPUT_MODES[0])
        out_menu = ctk.CTkOptionMenu(row, variable=self.output_mode_var, values=OUTPUT_MODES, command=lambda _: self._schedule_render(full=True))
        out_menu.pack(side="left", padx=5)

        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        ctk.CTkLabel(row2, text="Bit Depth", width=90, anchor="w").pack(side="left")
        self.bit_depth_var = ctk.StringVar(value=BIT_DEPTHS[0])
        depth_menu = ctk.CTkOptionMenu(row2, variable=self.bit_depth_var, values=BIT_DEPTHS)
        depth_menu.pack(side="left", padx=5)

        row3 = ctk.CTkFrame(parent, fg_color="transparent")
        row3.pack(fill="x", pady=2)
        ctk.CTkLabel(row3, text="Normal", width=90, anchor="w").pack(side="left")
        self.normal_format_var = ctk.StringVar(value=NORMAL_FORMATS[0])
        fmt_menu = ctk.CTkOptionMenu(row3, variable=self.normal_format_var, values=NORMAL_FORMATS, command=lambda _: self._schedule_render(full=True))
        fmt_menu.pack(side="left", padx=5)

        self.normal_strength_slider = SliderWithInput(parent, "Strength", 0.1, 5.0, 1.0, self._on_normal_strength)
        self.normal_strength_slider.pack(fill="x", pady=2)
        self.normal_strength_slider.slider.bind("<ButtonRelease-1>", lambda e: self._schedule_render(full=True))
    def _add_option(self, parent, label, field, values, on_change=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=90, anchor="w").pack(side="left")
        var = ctk.StringVar(value=values[0])

        def _handler(val):
            if self._suspend_updates:
                return
            self._set_field(field, val, full=True)
            if on_change:
                on_change(val)

        opt = ctk.CTkOptionMenu(row, variable=var, values=values, width=160, command=_handler)
        opt.pack(side="left", padx=5)
        self.controls[field] = {"type": "option", "var": var, "widget": opt}
        return opt

    def _add_toggle(self, parent, label, field):
        var = ctk.BooleanVar(value=False)

        def _handler():
            if self._suspend_updates:
                return
            self._set_field(field, var.get(), full=True)

        cb = ctk.CTkCheckBox(parent, text=label, variable=var, command=_handler)
        cb.pack(anchor="w", pady=2)
        self.controls[field] = {"type": "toggle", "var": var, "widget": cb}
        return cb

    def _add_slider(self, parent, label, field, vmin, vmax, is_int=False):
        slider = SliderWithInput(parent, label, vmin, vmax, 0, command=lambda v: self._set_field(field, v, full=False), is_int=is_int)
        slider.pack(fill="x", pady=2)
        slider.slider.bind("<ButtonRelease-1>", lambda e: self._schedule_render(full=True))
        self.controls[field] = {"type": "slider", "widget": slider}
        return slider

    def _set_field(self, field, value, full: bool):
        if self._suspend_updates:
            return
        layer = self._get_selected_layer()
        if layer is None:
            return
        if field in ["layer_kind", "effect_type"]:
            layer[field] = value
            return
        layer[field] = value
        self._schedule_render(full=full)

    def _on_normal_strength(self, value):
        if self._suspend_updates:
            return
        self._schedule_render(full=False)

    def _on_output_seamless_change(self):
        if self._suspend_updates:
            return
        self._update_seamless_ui()
        self._schedule_render(full=True)

    def _get_normal_strength(self) -> float:
        try:
            return float(self.normal_strength_slider.entry_var.get())
        except (ValueError, TypeError):
            return 1.0

    def _get_selected_layer(self):
        if self.selected_idx is None or self.selected_idx < 0:
            return None
        if self.selected_idx >= len(self.layers):
            return None
        return self.layers[self.selected_idx]

    def _label_kind(self, value: str) -> str:
        return "Effect" if str(value).lower() == "effect" else "Generator"

    def _label_effect(self, value: str) -> str:
        key = str(value).lower().replace(" ", "_")
        mapping = {
            "warp": "Warp",
            "erosion": "Erosion",
            "tone": "Tone",
            "clamp": "Clamp",
            "normalize": "Normalize",
            "quantize": "Quantize",
            "blur": "Blur",
            "sharpen": "Sharpen",
            "invert": "Invert",
            "ridged": "Ridged",
            "slope": "Slope",
            "curvature": "Curvature",
        }
        return mapping.get(key, str(value))

    def _normalize_kind(self, label: str) -> str:
        return "effect" if str(label).lower().startswith("e") else "generator"

    def _normalize_effect(self, label: str) -> str:
        return str(label).lower().replace(" ", "_")

    def _set_control_state(self, field: str, enabled: bool):
        ctrl = self.controls.get(field)
        if not ctrl:
            return
        state = "normal" if enabled else "disabled"
        if ctrl["type"] == "option":
            ctrl["widget"].configure(state=state)
        elif ctrl["type"] == "toggle":
            ctrl["widget"].configure(state=state)
        elif ctrl["type"] == "slider":
            ctrl["widget"].slider.configure(state=state)
            ctrl["widget"].entry.configure(state=state)

    def _label_mask_mode(self, value: str) -> str:
        v = str(value).lower()
        if v in ["add", "plus"]:
            return "Add"
        if v in ["subtract", "sub", "minus"]:
            return "Subtract"
        if v in ["max", "lighten"]:
            return "Max"
        if v in ["min", "darken"]:
            return "Min"
        return "Multiply"

    def _normalize_mask_mode(self, label: str) -> str:
        return str(label).lower()

    def _get_source_options(self):
        options = ["Stack Below"]
        mapping = {"Stack Below": "stack_below"}
        if self.selected_idx is None:
            return options, mapping
        for idx in range(self.selected_idx + 1, len(self.layers)):
            layer = self.layers[idx]
            uid = layer.get("uid", "")
            if not uid:
                continue
            name = layer.get("name", f"Layer {idx + 1}")
            label = f"{name} [{idx + 1}]"
            mapping[label] = f"layer:{uid}"
            options.append(label)
        return options, mapping

    def _source_label(self, source: str, mapping: dict) -> str:
        for label, value in mapping.items():
            if value == source:
                return label
        return "Stack Below"

    def _refresh_effect_input_options(self):
        if not hasattr(self, "input_source_menu"):
            return
        layer = self._get_selected_layer()
        if not layer or str(layer.get("layer_kind", "generator")).lower() != "effect":
            self.input_source_menu.configure(values=["Stack Below"])
            self.input_source_var.set("Stack Below")
            return
        options, mapping = self._get_source_options()
        self._input_source_map = mapping
        self.input_source_menu.configure(values=options)
        current = layer.get("input_source", "stack_below")
        self.input_source_var.set(self._source_label(current, mapping))

    def _on_input_source_change(self, value):
        layer = self._get_selected_layer()
        if layer is None:
            return
        mapping = getattr(self, "_input_source_map", {"Stack Below": "stack_below"})
        layer["input_source"] = mapping.get(value, "stack_below")
        self._schedule_render(full=True)

    def _refresh_masks_ui(self):
        if not hasattr(self, "mask_list"):
            return
        for child in self.mask_list.winfo_children():
            child.destroy()
        layer = self._get_selected_layer()
        if not layer or str(layer.get("layer_kind", "generator")).lower() != "effect":
            return
        masks = layer.get("masks", [])
        options, mapping = self._get_source_options()
        for idx, mask in enumerate(masks):
            row = ctk.CTkFrame(self.mask_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(2, weight=1)

            src_label = self._source_label(mask.get("source", "stack_below"), mapping)
            var_source = ctk.StringVar(value=src_label)
            src_menu = ctk.CTkOptionMenu(
                row, variable=var_source, values=options, width=140,
                command=lambda val, i=idx: self._on_mask_source_change(i, val)
            )
            src_menu.grid(row=0, column=0, padx=2)

            var_mode = ctk.StringVar(value=self._label_mask_mode(mask.get("mode", "multiply")))
            mode_menu = ctk.CTkOptionMenu(
                row, variable=var_mode, values=MASK_MODES, width=90,
                command=lambda val, i=idx: self._on_mask_mode_change(i, val)
            )
            mode_menu.grid(row=0, column=1, padx=2)

            strength_val = float(mask.get("strength", 1.0))
            strength_label = ctk.CTkLabel(row, text=f"{strength_val:.2f}", width=40)
            strength_label.grid(row=0, column=4, padx=2)

            slider = ctk.CTkSlider(
                row, from_=0.0, to=1.0, width=120,
                command=lambda val, i=idx, lbl=strength_label: self._on_mask_strength_change(i, val, lbl)
            )
            slider.set(strength_val)
            slider.grid(row=0, column=2, sticky="ew", padx=2)

            var_inv = ctk.BooleanVar(value=bool(mask.get("invert", False)))
            inv_cb = ctk.CTkCheckBox(
                row, text="Inv", variable=var_inv,
                command=lambda i=idx, v=var_inv: self._on_mask_invert_change(i, v.get()),
                width=40
            )
            inv_cb.grid(row=0, column=3, padx=2)

            btn_del = ctk.CTkButton(row, text="X", width=24, height=24,
                                    fg_color=THEME_BTN_DANGER, hover_color=THEME_BTN_DANGER_HOVER,
                                    command=lambda i=idx: self._remove_mask(i))
            btn_del.grid(row=0, column=5, padx=2)

        self._mask_source_map = mapping

    def _add_mask(self):
        layer = self._get_selected_layer()
        if not layer or str(layer.get("layer_kind", "generator")).lower() != "effect":
            return
        masks = layer.setdefault("masks", [])
        masks.append({"source": "stack_below", "mode": "multiply", "strength": 1.0, "invert": False})
        self._refresh_masks_ui()
        self._schedule_render(full=True)

    def _remove_mask(self, index: int):
        layer = self._get_selected_layer()
        if not layer:
            return
        masks = layer.get("masks", [])
        if index < 0 or index >= len(masks):
            return
        masks.pop(index)
        self._refresh_masks_ui()
        self._schedule_render(full=True)

    def _on_mask_source_change(self, index: int, value: str):
        layer = self._get_selected_layer()
        if not layer:
            return
        masks = layer.get("masks", [])
        if index < 0 or index >= len(masks):
            return
        mapping = getattr(self, "_mask_source_map", {"Stack Below": "stack_below"})
        masks[index]["source"] = mapping.get(value, "stack_below")
        self._schedule_render(full=True)

    def _on_mask_mode_change(self, index: int, value: str):
        layer = self._get_selected_layer()
        if not layer:
            return
        masks = layer.get("masks", [])
        if index < 0 or index >= len(masks):
            return
        masks[index]["mode"] = self._normalize_mask_mode(value)
        self._schedule_render(full=True)

    def _on_mask_strength_change(self, index: int, value: float, label):
        layer = self._get_selected_layer()
        if not layer:
            return
        masks = layer.get("masks", [])
        if index < 0 or index >= len(masks):
            return
        masks[index]["strength"] = float(value)
        label.configure(text=f"{value:.2f}")
        self._schedule_render(full=False)

    def _on_mask_invert_change(self, index: int, value: bool):
        layer = self._get_selected_layer()
        if not layer:
            return
        masks = layer.get("masks", [])
        if index < 0 or index >= len(masks):
            return
        masks[index]["invert"] = bool(value)
        self._schedule_render(full=True)

    def _refresh_layers(self):
        for child in self.layer_scroll.winfo_children():
            child.destroy()

        def selected_idx():
            return self.selected_idx

        callbacks = {
            "select": self._select_layer,
            "rename": self._rename_layer,
            "duplicate": self._duplicate_layer_at,
            "delete": self._delete_layer_at,
            "reorder": self._reorder_layer,
            "render": lambda: self._schedule_render(full=True),
            "selected_idx": selected_idx,
        }

        for idx, layer in enumerate(self.layers):
            item = LayerItem(self.layer_scroll, layer, idx, callbacks, selected=(idx == self.selected_idx))
            item.pack(fill="x", pady=3)

    def _add_layer(self):
        name = f"Layer {len(self.layers) + 1}"
        self.layers.append(_default_layer(name))
        self.selected_idx = len(self.layers) - 1
        self._refresh_layers()
        self._load_selected_layer()
        self._schedule_render(full=True)

    def _add_effect_layer(self):
        name = f"Effect {len(self.layers) + 1}"
        self.layers.append(_default_effect_layer(name))
        self.selected_idx = len(self.layers) - 1
        self._refresh_layers()
        self._load_selected_layer()
        self._schedule_render(full=True)

    def _duplicate_layer(self):
        if self.selected_idx is None:
            return
        self._duplicate_layer_at(self.selected_idx)

    def _duplicate_layer_at(self, index: int):
        if index < 0 or index >= len(self.layers):
            return
        src = dict(self.layers[index])
        src["uid"] = uuid.uuid4().hex
        src["name"] = f"{src.get('name', 'Layer')} Copy"
        self.layers.insert(index + 1, src)
        self.selected_idx = index + 1
        self._refresh_layers()
        self._load_selected_layer()
        self._schedule_render(full=True)

    def _delete_layer(self):
        if self.selected_idx is None:
            return
        self._delete_layer_at(self.selected_idx)

    def _delete_layer_at(self, index: int):
        if index < 0 or index >= len(self.layers):
            return
        if len(self.layers) == 1:
            self.layers[0] = _default_layer("Layer 1")
            self.selected_idx = 0
        else:
            self.layers.pop(index)
            self.selected_idx = max(0, min(index, len(self.layers) - 1))
        self._refresh_layers()
        self._load_selected_layer()
        self._schedule_render(full=True)

    def _rename_layer(self, index: int):
        if index < 0 or index >= len(self.layers):
            return
        dialog = ctk.CTkInputDialog(title="Rename Layer", text="New name")
        new_name = dialog.get_input()
        if new_name:
            self.layers[index]["name"] = new_name
            if index == self.selected_idx:
                self.var_name.set(new_name)
            self._refresh_layers()

    def _reorder_layer(self, index: int, direction: int):
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.layers):
            return
        self.layers[index], self.layers[new_index] = self.layers[new_index], self.layers[index]
        if self.selected_idx == index:
            self.selected_idx = new_index
        elif self.selected_idx == new_index:
            self.selected_idx = index
        self._refresh_layers()
        self._refresh_effect_input_options()
        self._refresh_masks_ui()

    def _select_layer(self, index: int):
        self.selected_idx = index
        self._refresh_layers()
        self._load_selected_layer()
    def _load_selected_layer(self):
        layer = self._get_selected_layer()
        if layer is None:
            return
        self._suspend_updates = True

        self.var_name.set(layer.get("name", "Layer"))
        if hasattr(self, "status_label"):
            kind_label = self._label_kind(layer.get("layer_kind", "generator"))
            if str(layer.get("layer_kind", "generator")).lower() == "effect":
                detail = self._label_effect(layer.get("effect_type", "warp"))
            else:
                detail = layer.get("type", "")
            self.status_label.configure(text=f"{layer.get('name', 'Layer')} | {kind_label} | {detail}")

        for field, ctrl in self.controls.items():
            if field not in layer:
                continue
            val = layer.get(field)
            if ctrl["type"] == "option":
                if field == "layer_kind":
                    ctrl["var"].set(self._label_kind(val))
                elif field == "effect_type":
                    ctrl["var"].set(self._label_effect(val))
                else:
                    ctrl["var"].set(str(val))
            elif ctrl["type"] == "toggle":
                ctrl["var"].set(bool(val))
            elif ctrl["type"] == "slider":
                slider = ctrl["widget"]
                slider.slider.set(float(val))
                slider.entry_var.set(slider._format(val))

        self._suspend_updates = False
        self._update_type_visibility()
        self._update_seamless_ui()
        self._refresh_effect_input_options()
        self._refresh_masks_ui()

    def _on_name_change(self, event=None):
        layer = self._get_selected_layer()
        if layer is None:
            return
        new_name = self.var_name.get().strip() or "Layer"
        layer["name"] = new_name
        if hasattr(self, "status_label"):
            kind_label = self._label_kind(layer.get("layer_kind", "generator"))
            if str(layer.get("layer_kind", "generator")).lower() == "effect":
                detail = self._label_effect(layer.get("effect_type", "warp"))
            else:
                detail = layer.get("type", "")
            self.status_label.configure(text=f"{new_name} | {kind_label} | {detail}")
        self._refresh_layers()

    def _on_type_change(self, value):
        layer = self._get_selected_layer()
        if layer is None:
            return
        if str(layer.get("layer_kind", "generator")).lower() != "generator":
            return
        layer["type"] = value
        if value.lower() == "gradient":
            layer["seamless"] = False
        self._update_type_visibility()
        self._update_seamless_ui()
        if hasattr(self, "status_label"):
            kind_label = self._label_kind(layer.get("layer_kind", "generator"))
            self.status_label.configure(text=f"{layer.get('name', 'Layer')} | {kind_label} | {value}")
        self._refresh_layers()
        self._schedule_render(full=True)

    def _on_kind_change(self, value):
        layer = self._get_selected_layer()
        if layer is None:
            return
        kind = self._normalize_kind(value)
        layer["layer_kind"] = kind
        if kind == "effect":
            layer.setdefault("effect_type", "warp")
            layer.setdefault("input_source", "stack_below")
            layer.setdefault("masks", [])
            layer["seamless"] = False
        self._update_type_visibility()
        self._update_seamless_ui()
        self._refresh_effect_input_options()
        self._refresh_masks_ui()
        if hasattr(self, "status_label"):
            detail = self._label_effect(layer.get("effect_type", "warp")) if kind == "effect" else layer.get("type", "")
            self.status_label.configure(text=f"{layer.get('name', 'Layer')} | {self._label_kind(kind)} | {detail}")
        self._refresh_layers()
        self._schedule_render(full=True)

    def _on_effect_type_change(self, value):
        layer = self._get_selected_layer()
        if layer is None:
            return
        if str(layer.get("layer_kind", "generator")).lower() != "effect":
            return
        layer["effect_type"] = self._normalize_effect(value)
        self._update_type_visibility()
        if hasattr(self, "status_label"):
            self.status_label.configure(text=f"{layer.get('name', 'Layer')} | Effect | {value}")
        self._schedule_render(full=True)

    def _update_type_visibility(self):
        layer = self._get_selected_layer()
        if layer is None:
            return
        kind = str(layer.get("layer_kind", "generator")).lower()
        noise_type = layer.get("type", "fbm").lower()
        effect_type = self._normalize_effect(layer.get("effect_type", "warp"))

        all_sections = [
            self.section_general,
            self.section_transform,
            self.section_fbm,
            self.section_voronoi,
            self.section_wave,
            self.section_magic,
            self.section_gradient,
            self.section_brick,
            self.section_gabor,
            self.section_effect,
            self.section_masks,
            self.section_fx_warp,
            self.section_fx_erosion,
            self.section_fx_tone,
            self.section_fx_clamp,
            self.section_fx_quantize,
            self.section_fx_blur,
            self.section_fx_sharpen,
            self.section_fx_slope,
            self.section_fx_curvature,
            self.section_output,
        ]
        for section in all_sections:
            section.pack_forget()

        self.section_general.pack(fill="x", pady=4)
        if kind == "effect":
            for section in [self.section_effect, self.section_masks]:
                section.pack(fill="x", pady=4)
            for section in self.effect_sections.get(effect_type, []):
                section.pack(fill="x", pady=4)
        else:
            self.section_transform.pack(fill="x", pady=4)
            for section in self.type_sections.get(noise_type, []):
                section.pack(fill="x", pady=4)

        self.section_output.pack(fill="x", pady=4)

        self._set_control_state("type", kind == "generator")
        self._set_control_state("seamless", kind == "generator")
        self._set_control_state("normalize", kind == "generator")
        self._set_control_state("seed", kind == "generator")
        self._set_control_state("evolution", kind == "generator")
        self._set_control_state("noise_scale", kind == "generator")

    def _update_seamless_ui(self):
        layer = self._get_selected_layer()
        if layer is None:
            return
        kind = str(layer.get("layer_kind", "generator")).lower()
        t = layer.get("type", "fbm").lower()
        global_seamless = bool(self.output_seamless_var.get()) if hasattr(self, "output_seamless_var") else False

        if kind != "generator":
            self.chk_seamless.configure(state="disabled")
            self.controls["seamless"]["var"].set(False)
            layer["seamless"] = False
            return

        if global_seamless or t == "gradient":
            self.chk_seamless.configure(state="disabled")
            self.controls["seamless"]["var"].set(False)
            layer["seamless"] = False
        else:
            self.chk_seamless.configure(state="normal")


    def _on_size_change(self, value):
        size = _safe_int(value, DEFAULT_RENDER_SIZE)
        size = int(_clamp(size, 64, 8192))
        self.render_size = size
        self.renderer.set_size(size, size)
        self._schedule_render(full=True)
    def _schedule_render(self, full: bool = False):
        if self._suspend_updates:
            return
        if full:
            self._pending_full = True
        if self._render_after_id:
            self.after_cancel(self._render_after_id)
        delay = 120 if full else 50
        self._render_after_id = self.after(delay, self._start_render)

    def _start_render(self):
        self._render_after_id = None
        interactive = not self._pending_full
        self._pending_full = False

        layers = self._build_render_layers(interactive)
        if not layers:
            return

        render_size = self.render_size
        if interactive:
            render_size = min(self.render_size, INTERACTIVE_RENDER_SIZE)

        self.renderer.set_size(render_size, render_size)
        self._render_request_id += 1
        request_id = self._render_request_id

        if self._rendering_after_id:
            self.after_cancel(self._rendering_after_id)
        self._rendering_after_id = self.after(150, self._show_render_overlay)

        self.renderer.cancel()
        self._render_busy = True

        preview_downsample = None
        if interactive and self.use_gpu and GPU_AVAILABLE:
            preview_downsample = self.preview_downsample

        thread = threading.Thread(
            target=self._render_worker,
            args=(request_id, layers, interactive, preview_downsample),
            daemon=True,
        )
        self._render_thread = thread
        thread.start()

    def _render_worker(self, request_id, layers, interactive, preview_downsample):
        start = time.perf_counter()
        try:
            arr = self.renderer.render(
                layers,
                interactive=interactive,
                use_gpu=self.use_gpu,
                preview_downsample=preview_downsample,
                output_seamless=bool(self.output_seamless_var.get()) if hasattr(self, "output_seamless_var") else False,
            )
        except Exception as exc:
            arr = None
            self.after(0, lambda: messagebox.showerror("Render Error", str(exc)))
        elapsed = time.perf_counter() - start
        self.after(0, lambda: self._on_render_complete(request_id, arr, elapsed))

    def _on_render_complete(self, request_id, arr, elapsed):
        if request_id != self._render_request_id:
            return
        self._render_busy = False
        if self._rendering_after_id:
            self.after_cancel(self._rendering_after_id)
            self._rendering_after_id = None
        self._hide_render_overlay()

        self._last_render_time = elapsed
        self.lbl_time.configure(text=f"Render: {elapsed*1000.0:.0f} ms")
        if arr is None:
            return
        self._update_preview(arr)

    def _build_render_layers(self, interactive: bool):
        if interactive:
            layer = self._get_selected_layer()
            if layer is None:
                return []
            kind = str(layer.get("layer_kind", "generator")).lower()
            if kind == "effect":
                return [dict(l) for l in self.layers[self.selected_idx:]]
            temp = dict(layer)
            temp["visible"] = True
            return [temp]
        return [dict(layer) for layer in self.layers]

    def _show_render_overlay(self):
        self.render_overlay.place(relx=0.5, rely=0.5, anchor="center")

    def _hide_render_overlay(self):
        self.render_overlay.place_forget()

    def _update_preview(self, arr):
        mode = self.output_mode_var.get() if hasattr(self, "output_mode_var") else "Heightmap"
        if mode == "Normal":
            fmt = self.normal_format_var.get().lower() if hasattr(self, "normal_format_var") else "opengl"
            strength = self._get_normal_strength()
            img = generate_normal_map(arr, strength=strength, format=fmt)
        else:
            img = to_8bit_image(arr)

        target = self.preview_display_size
        if self.preview_label.winfo_width() > 10:
            target = min(self.preview_label.winfo_width(), self.preview_label.winfo_height())
        img = img.resize((target, target), Image.LANCZOS)

        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=self.preview_photo)

    def _export_image(self):
        path = filedialog.asksaveasfilename(
            title="Export Image",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("TIFF", "*.tif"), ("JPEG", "*.jpg")],
        )
        if not path:
            return
        thread = threading.Thread(target=self._export_worker, args=(path,), daemon=True)
        thread.start()

    def _export_worker(self, path):
        layers = self._build_render_layers(False)
        self.renderer.set_size(self.render_size, self.render_size)
        try:
            arr = self.renderer.render(
                layers,
                interactive=False,
                use_gpu=self.use_gpu,
                output_seamless=bool(self.output_seamless_var.get()) if hasattr(self, "output_seamless_var") else False,
            )
            mode = self.output_mode_var.get()
            if mode == "Normal":
                fmt = self.normal_format_var.get().lower()
                strength = self._get_normal_strength()
                img = generate_normal_map(arr, strength=strength, format=fmt)
            else:
                if self.bit_depth_var.get() == "16-bit":
                    img = to_16bit_image(arr)
                else:
                    img = to_8bit_image(arr)
            img.save(path)
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Export Error", str(exc)))
            return
        self.after(0, lambda: messagebox.showinfo("Export", "Export complete."))

    def _on_close(self):
        try:
            self.renderer.cancel()
        except Exception:
            pass
        self.destroy()

def main():
    app = NoiseMasterWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
