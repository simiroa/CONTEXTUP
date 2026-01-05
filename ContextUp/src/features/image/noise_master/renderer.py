"""
Noise Master - Renderer (GPU-first).
"""

from __future__ import annotations

import os
import time
import numpy as np
from typing import List, Dict, Any

from .layers import LayerConfig
from .generators import generate
from . import effects as effects_cpu
from . import effects_gpu as effects_gpu
from .gpu_backend import get_xp, to_numpy, GPU_AVAILABLE


def _create_uv_grid(xp, width: int, height: int):
    x = xp.linspace(0.0, 1.0, width, dtype=xp.float32)
    y = xp.linspace(0.0, 1.0, height, dtype=xp.float32)
    xv, yv = xp.meshgrid(x, y)
    return xv, yv


def _transform_uv(xp, u, v, scale=1.0, ratio=0.0,
                  rotation_deg=0.0, offset_x=0.0, offset_y=0.0):
    u = u - 0.5
    v = v - 0.5

    rx = 2.0 ** ratio if ratio >= 0 else 1.0
    ry = 2.0 ** (-ratio) if ratio < 0 else 1.0
    u = u * rx
    v = v * ry

    scale = max(0.001, scale)
    u = u * scale
    v = v * scale

    if rotation_deg != 0.0:
        rad = xp.deg2rad(rotation_deg)
        c, s = xp.cos(rad), xp.sin(rad)
        u_rot = u * c - v * s
        v_rot = u * s + v * c
        u, v = u_rot, v_rot

    u = u + offset_x
    v = v + offset_y
    return u, v


def _map_to_torus(xp, u, v):
    angle_u = u * 2.0 * xp.pi
    angle_v = v * 2.0 * xp.pi
    r = 1.0 / (2.0 * xp.pi)
    x = xp.cos(angle_u) * r
    y = xp.sin(angle_u) * r
    z = xp.cos(angle_v) * r
    w = xp.sin(angle_v) * r
    return x, y, z, w


def _rotate_4d(xp, x, y, z, w, angle_deg):
    if angle_deg == 0:
        return x, y, z, w
    rad = xp.deg2rad(angle_deg)
    c, s = xp.cos(rad), xp.sin(rad)
    nx = x * c - z * s
    nz = x * s + z * c
    ny = y * c - w * s
    nw = y * s + w * c
    return nx, ny, nz, nw


def _match_layer_channels(xp, base, layer):
    if base.ndim == 2 and layer.ndim == 3:
        base = xp.repeat(base[..., None], layer.shape[-1], axis=-1)
    elif base.ndim == 3 and layer.ndim == 2:
        layer = xp.repeat(layer[..., None], base.shape[-1], axis=-1)
    return base, layer


def _blend_layers(xp, base, layer, mode: str, opacity: float):
    if np.isscalar(opacity):
        if float(opacity) <= 0.0:
            return base

    base, layer = _match_layer_channels(xp, base, layer)
    if mode == "normal":
        result = layer
    elif mode == "add":
        result = xp.minimum(base + layer, 1.0)
    elif mode == "multiply":
        result = base * layer
    elif mode == "screen":
        result = 1.0 - (1.0 - base) * (1.0 - layer)
    elif mode == "overlay":
        mask = base < 0.5
        low = 2.0 * base * layer
        high = 1.0 - 2.0 * (1.0 - base) * (1.0 - layer)
        result = xp.where(mask, low, high)
    elif mode == "difference":
        result = xp.abs(base - layer)
    elif mode in ["max", "lighten"]:
        result = xp.maximum(base, layer)
    elif mode in ["min", "darken"]:
        result = xp.minimum(base, layer)
    elif mode == "subtract":
        result = xp.maximum(base - layer, 0.0)
    else:
        result = layer
    return base * (1.0 - opacity) + result * opacity


def _downsample_gpu(xp, arr, target_size: int):
    if target_size <= 0:
        return arr
    if xp.__name__ != "cupy":
        return arr
    h, w = arr.shape[0], arr.shape[1]
    if h <= target_size or w <= target_size:
        return arr
    factor = h // target_size
    if factor < 2:
        return arr
    h2 = target_size * factor
    w2 = target_size * factor
    if arr.ndim == 2:
        cropped = arr[:h2, :w2]
        return cropped.reshape(target_size, factor, target_size, factor).mean(axis=(1, 3))
    if arr.ndim == 3:
        cropped = arr[:h2, :w2, :]
        c = cropped.shape[-1]
        return cropped.reshape(target_size, factor, target_size, factor, c).mean(axis=(1, 3))
    return arr


def _to_mask(xp, arr):
    if arr.ndim == 3:
        arr = xp.mean(arr, axis=-1)
    return xp.clip(arr, 0.0, 1.0)


def _sample_bilinear(xp, img, u, v, wrap: bool = False):
    h, w = img.shape[0], img.shape[1]
    if wrap:
        u = xp.mod(u, w)
        v = xp.mod(v, h)
    else:
        u = xp.clip(u, 0.0, w - 1.0)
        v = xp.clip(v, 0.0, h - 1.0)

    x0 = xp.floor(u).astype(xp.int32)
    y0 = xp.floor(v).astype(xp.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    if wrap:
        x1 = xp.mod(x1, w)
        y1 = xp.mod(y1, h)
    else:
        x1 = xp.clip(x1, 0, w - 1)
        y1 = xp.clip(y1, 0, h - 1)

    wx = u - x0
    wy = v - y0

    if img.ndim == 2:
        c00 = img[y0, x0]
        c10 = img[y0, x1]
        c01 = img[y1, x0]
        c11 = img[y1, x1]
    else:
        c00 = img[y0, x0, :]
        c10 = img[y0, x1, :]
        c01 = img[y1, x0, :]
        c11 = img[y1, x1, :]

    c0 = c00 * (1.0 - wx) + c10 * wx
    c1 = c01 * (1.0 - wx) + c11 * wx
    return c0 * (1.0 - wy) + c1 * wy


def _build_mask(xp, masks, layer_results, stack, shape):
    if not masks:
        return None
    mask_total = xp.ones(shape, dtype=xp.float32)
    for m in masks:
        src = str(m.get("source", "stack_below")).lower()
        if src in ["stack_below", "stack", "below"]:
            mask = stack
        elif src.startswith("layer:"):
            uid = src.split(":", 1)[1]
            mask = layer_results.get(uid)
        else:
            mask = None
        if mask is None:
            continue
        mask = _to_mask(xp, mask)
        if m.get("invert", False):
            mask = 1.0 - mask
        strength = float(m.get("strength", 1.0))
        strength = max(0.0, min(1.0, strength))
        mode = str(m.get("mode", "multiply")).lower()
        if mode == "multiply":
            mask_adj = (1.0 - strength) + mask * strength
            mask_total = mask_total * mask_adj
        elif mode in ["add", "plus"]:
            mask_total = xp.clip(mask_total + mask * strength, 0.0, 1.0)
        elif mode in ["subtract", "sub", "minus"]:
            mask_total = xp.clip(mask_total - mask * strength, 0.0, 1.0)
        elif mode in ["max", "lighten"]:
            mask_total = xp.maximum(mask_total, mask * strength)
        elif mode in ["min", "darken"]:
            mask_total = xp.minimum(mask_total, mask * strength)
        else:
            mask_adj = (1.0 - strength) + mask * strength
            mask_total = mask_total * mask_adj
    return mask_total


class NoiseRenderer:
    def __init__(self, width: int = 512, height: int = 512):
        self.width = width
        self.height = height
        self._cancel_flag = False
        self.profile_enabled = os.getenv("NOISE_MASTER_PROFILE", "0").lower() not in ("", "0", "false", "no")
        self._uv_cache = {}
        self._layer_cache = {}

    def set_size(self, w: int, h: int):
        if w != self.width or h != self.height:
            self._uv_cache = {}
            self._layer_cache = {}
        self.width = w
        self.height = h

    def cancel(self):
        self._cancel_flag = True

    def _is_cancelled(self):
        return self._cancel_flag

    def _prepare_coords(self, xp, cfg: LayerConfig, u_grid, v_grid):
        t_lower = cfg.type.lower()
        seamless_excluded = ["gradient"]
        if cfg.seamless and t_lower not in seamless_excluded:
            safe_scale = max(cfg.scale, 0.0001)
            u_map = (u_grid + cfg.offset_x / safe_scale) % 1.0
            v_map = (v_grid + cfg.offset_y / safe_scale) % 1.0
            x, y, z, w = _map_to_torus(xp, u_map, v_map)
            if cfg.rotation != 0:
                x, y, z, w = _rotate_4d(xp, x, y, z, w, cfg.rotation)

            node_scale = 1.0 if t_lower in ["white_noise"] else cfg.noise_scale
            su = cfg.scale * node_scale * (2.0 ** cfg.ratio if cfg.ratio >= 0 else 1.0)
            sv = cfg.scale * node_scale * (2.0 ** (-cfg.ratio) if cfg.ratio < 0 else 1.0)
            evo = xp.full_like(x, cfg.evolution)
            coords = (x * su, y * su, z * sv, w * sv, evo)
            return coords, True, node_scale

        u, v = _transform_uv(xp, u_grid, v_grid,
                             scale=cfg.scale, ratio=cfg.ratio,
                             rotation_deg=cfg.rotation,
                             offset_x=cfg.offset_x, offset_y=cfg.offset_y)
        if t_lower not in ["gradient", "white_noise"]:
            u = u * cfg.noise_scale
            v = v * cfg.noise_scale
        node_scale = 1.0 if t_lower in ["gradient", "white_noise"] else cfg.noise_scale
        return (u, v), False, node_scale

    def _get_uv_grid(self, xp):
        key = (xp.__name__, self.width, self.height)
        cached = self._uv_cache.get(key)
        if cached:
            return cached
        u_grid, v_grid = _create_uv_grid(xp, self.width, self.height)
        self._uv_cache = {key: (u_grid, v_grid)}
        return u_grid, v_grid

    def _get_layer_cache(self, xp):
        key = (xp.__name__, self.width, self.height)
        return self._layer_cache.setdefault(key, {})

    def _generator_signature(self, cfg: LayerConfig, interactive: bool):
        return (
            "gen",
            bool(interactive),
            str(cfg.type).lower(),
            bool(cfg.seamless),
            float(cfg.evolution),
            float(cfg.noise_scale),
            bool(cfg.normalize),
            float(cfg.scale),
            float(cfg.ratio),
            float(cfg.rotation),
            float(cfg.offset_x),
            float(cfg.offset_y),
            str(cfg.noise_type),
            float(cfg.detail),
            float(cfg.roughness),
            float(cfg.lacunarity),
            float(cfg.distortion),
            float(cfg.noise_offset),
            float(cfg.noise_gain),
            int(cfg.seed),
            float(cfg.jitter),
            str(cfg.distance_metric),
            str(cfg.return_type),
            float(cfg.smoothness),
            float(cfg.exponent),
            str(cfg.voronoi_output),
            str(cfg.subtype),
            float(cfg.row_offset),
            float(cfg.brick_ratio),
            float(cfg.brick_row_height),
            int(cfg.brick_offset_frequency),
            float(cfg.brick_squash),
            int(cfg.brick_squash_frequency),
            float(cfg.mortar_size),
            float(cfg.mortar_smooth),
            int(cfg.depth),
            str(cfg.wave_type),
            str(cfg.wave_dir),
            str(cfg.wave_rings_dir),
            str(cfg.wave_profile),
            float(cfg.phase_offset),
            float(cfg.wave_detail_scale),
            float(cfg.wave_detail_roughness),
            float(cfg.gabor_frequency),
            float(cfg.gabor_anisotropy),
            float(cfg.gabor_orientation),
        )

    def _effect_signature(self, cfg: LayerConfig, input_sig, wrap: bool, interactive: bool):
        t = str(cfg.effect_type).lower().replace(" ", "_")
        base = (t, bool(wrap), bool(interactive), input_sig)
        if t == "warp":
            return base + (str(cfg.warp_type), float(cfg.warp_strength),
                           float(cfg.warp_scale), int(cfg.warp_seed))
        if t == "erosion":
            return base + (str(cfg.erosion_type), int(cfg.erosion_iterations),
                           float(cfg.erosion_rain), float(cfg.erosion_evap),
                           float(cfg.erosion_solu))
        if t in ["tone", "levels"]:
            return base + (float(cfg.tone_gain), float(cfg.tone_bias),
                           float(cfg.tone_gamma), float(cfg.tone_contrast))
        if t == "clamp":
            return base + (float(cfg.clamp_min), float(cfg.clamp_max))
        if t in ["quantize", "step", "posterize"]:
            return base + (int(cfg.quantize_steps),)
        if t == "blur":
            return base + (int(cfg.blur_radius), float(cfg.blur_strength))
        if t == "sharpen":
            return base + (int(cfg.sharpen_radius), float(cfg.sharpen_strength))
        if t == "slope":
            return base + (float(cfg.slope_strength),)
        if t == "curvature":
            return base + (str(cfg.curvature_mode), float(cfg.curvature_strength))
        return base

    def _resolve_input_signature(self, cfg: LayerConfig, stack_sig, layer_sig_results):
        src = str(getattr(cfg, "input_source", "stack_below")).lower()
        if src in ["stack_below", "stack", "below"]:
            return stack_sig
        if src.startswith("layer:"):
            uid = src.split(":", 1)[1]
            return layer_sig_results.get(uid)
        if src in ["layer", "layer_ref"] and cfg.input_layer_uid:
            return layer_sig_results.get(cfg.input_layer_uid)
        return stack_sig

    def _mask_signature(self, masks, stack_sig, layer_sig_results):
        if not masks:
            return None
        out = []
        for m in masks:
            src = str(m.get("source", "stack_below")).lower()
            if src in ["stack_below", "stack", "below"]:
                src_sig = stack_sig
            elif src.startswith("layer:"):
                uid = src.split(":", 1)[1]
                src_sig = layer_sig_results.get(uid)
            else:
                src_sig = None
            out.append((
                src,
                src_sig,
                str(m.get("mode", "multiply")).lower(),
                float(m.get("strength", 1.0)),
                bool(m.get("invert", False)),
            ))
        return tuple(out)

    def _resolve_input(self, cfg: LayerConfig, stack, layer_results):
        src = str(getattr(cfg, "input_source", "stack_below")).lower()
        if src in ["stack_below", "stack", "below"]:
            return stack
        if src in ["layer", "layer_ref"] and cfg.input_layer_uid:
            return layer_results.get(cfg.input_layer_uid)
        if src.startswith("layer:"):
            uid = src.split(":", 1)[1]
            return layer_results.get(uid)
        return stack

    def _apply_warp_effect(self, xp, cfg: LayerConfig, input_img, u_grid, v_grid,
                           use_gpu: bool, wrap: bool, cancel_check):
        if cfg.warp_strength <= 0.0:
            return input_img

        warp_cfg = LayerConfig()
        warp_cfg.type = cfg.warp_type
        warp_cfg.scale = cfg.warp_scale
        warp_cfg.noise_scale = 1.0
        warp_cfg.detail = 2.0
        warp_cfg.roughness = 0.5
        warp_cfg.lacunarity = 2.0
        warp_cfg.distortion = 0.0
        warp_cfg.normalize = True
        warp_cfg.seed = cfg.warp_seed

        warp_u = generate(
            warp_cfg, self.width, self.height,
            coords=(u_grid * cfg.warp_scale, v_grid * cfg.warp_scale),
            node_scale=1.0, use_gpu=use_gpu, cancel_check=cancel_check
        )
        if cancel_check and cancel_check():
            return input_img

        warp_cfg.seed = cfg.warp_seed + 1000
        warp_v = generate(
            warp_cfg, self.width, self.height,
            coords=(u_grid * cfg.warp_scale, v_grid * cfg.warp_scale),
            node_scale=1.0, use_gpu=use_gpu, cancel_check=cancel_check
        )
        if cancel_check and cancel_check():
            return input_img

        u = u_grid + (warp_u - 0.5) * cfg.warp_strength
        v = v_grid + (warp_v - 0.5) * cfg.warp_strength

        h, w = input_img.shape[0], input_img.shape[1]
        u_img = u * (w - 1)
        v_img = v * (h - 1)
        return _sample_bilinear(xp, input_img, u_img, v_img, wrap=wrap)

    def _apply_effect(self, xp, cfg: LayerConfig, input_img, u_grid, v_grid,
                      use_gpu: bool, wrap: bool, cancel_check):
        t = str(getattr(cfg, "effect_type", "warp")).lower().replace(" ", "_")
        if xp.__name__ == "cupy" and use_gpu:
            fx = effects_gpu
        else:
            fx = effects_cpu

        if t == "warp":
            return self._apply_warp_effect(xp, cfg, input_img, u_grid, v_grid, use_gpu, wrap, cancel_check)
        if t == "erosion":
            if input_img.ndim == 3:
                base = xp.mean(input_img, axis=-1)
            else:
                base = input_img
            if cfg.erosion_type == "thermal":
                base = fx.apply_erosion_thermal(
                    base, iterations=cfg.erosion_iterations, amount=0.1, wrap=wrap
                )
            else:
                base = fx.apply_erosion_hydraulic(
                    base, iterations=cfg.erosion_iterations,
                    rain=cfg.erosion_rain, evaporation=cfg.erosion_evap,
                    solubility=cfg.erosion_solu, wrap=wrap
                )
            if input_img.ndim == 3:
                return xp.repeat(base[..., None], input_img.shape[-1], axis=-1)
            return base
        if t == "invert":
            return fx.apply_invert(input_img)
        if t == "ridged":
            return fx.apply_ridged(input_img)
        if t in ["quantize", "step", "posterize"]:
            return fx.apply_quantize(input_img, steps=cfg.quantize_steps)
        if t in ["tone", "levels"]:
            return fx.apply_tone(input_img, gain=cfg.tone_gain, bias=cfg.tone_bias,
                                 gamma=cfg.tone_gamma, contrast=cfg.tone_contrast)
        if t == "clamp":
            return fx.apply_clamp(input_img, vmin=cfg.clamp_min, vmax=cfg.clamp_max)
        if t == "normalize":
            return fx.apply_normalize(input_img)
        if t == "blur":
            return fx.apply_blur(input_img, radius=cfg.blur_radius,
                                 strength=cfg.blur_strength, wrap=wrap)
        if t == "sharpen":
            return fx.apply_sharpen(input_img, radius=cfg.sharpen_radius,
                                    strength=cfg.sharpen_strength, wrap=wrap)
        if t == "slope":
            return fx.apply_slope(input_img, strength=cfg.slope_strength)
        if t == "curvature":
            return fx.apply_curvature(input_img, mode=cfg.curvature_mode,
                                      strength=cfg.curvature_strength, wrap=wrap)
        return input_img

    def render(self, layers_data: List[Dict[str, Any]],
               interactive: bool = False,
               use_gpu: bool = True,
               preview_downsample: int | None = None,
               output_seamless: bool = False) -> np.ndarray:
        self._cancel_flag = False
        prof = {}
        if self.profile_enabled:
            render_start = time.perf_counter()

        xp = get_xp(bool(use_gpu))
        if xp.__name__ == "cupy" and not GPU_AVAILABLE:
            xp = np

        if self.profile_enabled:
            t0 = time.perf_counter()
        u_grid, v_grid = _create_uv_grid(xp, self.width, self.height)
        if self.profile_enabled:
            prof["uv_grid"] = prof.get("uv_grid", 0.0) + (time.perf_counter() - t0)

        canvas = xp.zeros((self.height, self.width), dtype=xp.float32)
        active_layers = [d for d in layers_data if d.get("visible", True)]
        if not active_layers:
            return to_numpy(canvas)
        layer_results = {}
        layer_sig_results = {}
        stack_sig = ("base",)
        cache = self._get_layer_cache(xp)
        for layer_dict in reversed(active_layers):
            if self._is_cancelled():
                break
            cfg = LayerConfig.from_dict(layer_dict)
            if not cfg.uid:
                cfg.uid = layer_dict.get("uid", f"layer_{id(layer_dict)}")
            layer_kind = str(cfg.layer_kind).lower()
            if output_seamless and layer_kind == "generator":
                cfg.seamless = cfg.type.lower() != "gradient"
            if interactive:
                if layer_kind == "generator":
                    cfg.detail = min(cfg.detail, 3.0)
                    if cfg.type.lower() in ["voronoi", "cellular"]:
                        cfg.detail = min(cfg.detail, 2.0)

            if layer_kind == "effect":
                input_img = self._resolve_input(cfg, canvas, layer_results)
                if input_img is None:
                    continue
                input_sig = self._resolve_input_signature(cfg, stack_sig, layer_sig_results)
                if cfg.bypass:
                    layer_results[cfg.uid] = canvas
                    layer_sig_results[cfg.uid] = stack_sig
                    continue
                if float(cfg.opacity) <= 0.0:
                    layer_results[cfg.uid] = canvas
                    layer_sig_results[cfg.uid] = stack_sig
                    continue

                wrap = bool(output_seamless)
                effect_sig = self._effect_signature(cfg, input_sig, wrap, interactive)
                effect_cache = cache.get(cfg.uid)
                if effect_cache and effect_cache.get("sig") == effect_sig:
                    effect_img = effect_cache.get("out")
                else:
                    if interactive and cfg.effect_type.lower() in ["warp", "erosion"]:
                        effect_img = input_img
                    else:
                        effect_img = self._apply_effect(
                            xp, cfg, input_img, u_grid, v_grid,
                            use_gpu=bool(use_gpu), wrap=wrap, cancel_check=self._is_cancelled
                        )
                    cache[cfg.uid] = {"sig": effect_sig, "out": effect_img}

                mask_shape = input_img.shape[:2]
                mask = _build_mask(xp, cfg.masks, layer_results, canvas, mask_shape)
                mask_sig = self._mask_signature(cfg.masks, stack_sig, layer_sig_results)
                opacity = float(cfg.opacity)
                if mask is not None:
                    opacity = mask * opacity
                if mask is None and cfg.blend_mode == "normal" and float(cfg.opacity) >= 1.0:
                    canvas = effect_img
                else:
                    canvas = _blend_layers(xp, canvas, effect_img, cfg.blend_mode, opacity)
                layer_results[cfg.uid] = canvas
                layer_out_sig = ("fx", effect_sig, cfg.blend_mode, float(cfg.opacity), mask_sig)
                stack_sig = ("stack", stack_sig, layer_out_sig)
                layer_sig_results[cfg.uid] = stack_sig
                continue

            gen_sig = self._generator_signature(cfg, interactive)
            cache_entry = cache.get(cfg.uid)
            if cache_entry and cache_entry.get("sig") == gen_sig:
                layer_img = cache_entry.get("out")
            else:
                if self.profile_enabled:
                    t0 = time.perf_counter()
                coords, _, node_scale = self._prepare_coords(xp, cfg, u_grid, v_grid)
                if self.profile_enabled:
                    prof["coords"] = prof.get("coords", 0.0) + (time.perf_counter() - t0)

                if self.profile_enabled:
                    t0 = time.perf_counter()
                layer_img = generate(cfg, self.width, self.height,
                                     coords=coords, node_scale=node_scale,
                                     use_gpu=bool(use_gpu), cancel_check=self._is_cancelled)
                if self.profile_enabled:
                    prof["generate"] = prof.get("generate", 0.0) + (time.perf_counter() - t0)
                if self._is_cancelled():
                    break

                cache[cfg.uid] = {"sig": gen_sig, "out": layer_img}

            if self.profile_enabled:
                t0 = time.perf_counter()
            layer_results[cfg.uid] = layer_img
            layer_sig_results[cfg.uid] = gen_sig
            layer_out_sig = ("gen", gen_sig, cfg.blend_mode, float(cfg.opacity))
            stack_sig = ("stack", stack_sig, layer_out_sig)
            canvas = _blend_layers(xp, canvas, layer_img, cfg.blend_mode, cfg.opacity)
            if self.profile_enabled:
                prof["blend"] = prof.get("blend", 0.0) + (time.perf_counter() - t0)

        if self.profile_enabled:
            total = time.perf_counter() - render_start
            ordered = ["uv_grid", "coords", "generate", "blend"]
            parts = [f"{k}={prof.get(k, 0.0):.4f}s" for k in ordered if k in prof]
            print(f"[NoiseMaster] Render profile total={total:.4f}s " + " ".join(parts))

        keep_uids = {d.get("uid") for d in layers_data if d.get("uid")}
        if keep_uids:
            for uid in list(cache.keys()):
                if uid not in keep_uids:
                    cache.pop(uid, None)

        if preview_downsample and use_gpu and xp.__name__ == "cupy":
            canvas = _downsample_gpu(xp, canvas, int(preview_downsample))
        return to_numpy(canvas).astype(np.float32)
