"""
Noise Master - Generator dispatcher.
"""

from __future__ import annotations

import numpy as np
from typing import Optional

from .layers import LayerConfig
from .gpu_backend import GPU_AVAILABLE, get_xp, to_numpy

from .noise_perlin import perlin_fractal_distorted
from .noise_perlin_gpu import perlin_fractal_distorted_gpu
from .noise_patterns import (
    white_noise,
    magic_texture,
    wave_texture,
    gabor_texture,
    gradient_texture,
    brick_texture,
)
from .noise_patterns_gpu import (
    white_noise as white_noise_gpu,
    magic_texture as magic_texture_gpu,
    wave_texture as wave_texture_gpu,
    gabor_texture as gabor_texture_gpu,
    gradient_texture as gradient_texture_gpu,
    brick_texture as brick_texture_gpu,
)
from .noise_voronoi import voronoi_texture
from .noise_voronoi_gpu import voronoi_texture_gpu

__all__ = ["generate"]


def _create_uv_grid(width: int, height: int):
    x = np.linspace(0.0, 1.0, width, dtype=np.float32)
    y = np.linspace(0.0, 1.0, height, dtype=np.float32)
    xv, yv = np.meshgrid(x, y)
    return xv, yv


def generate(cfg: LayerConfig, width: int, height: int,
             coords: Optional[tuple] = None,
             node_scale: Optional[float] = None,
             use_gpu: bool = True,
             cancel_check=None):
    use_gpu = bool(use_gpu and GPU_AVAILABLE)
    xp = get_xp(use_gpu)

    if coords is None:
        u, v = _create_uv_grid(width, height)
        coords = (u, v)

    t = cfg.type.lower()
    if node_scale is None:
        node_scale = 1.0 if t in ["gradient", "white_noise"] else cfg.noise_scale

    if t in ["fbm", "perlin", "simplex"]:
        detail = float(np.clip(cfg.detail, 0.0, 15.0))
        roughness = float(max(cfg.roughness, 0.0))
        lacunarity = float(cfg.lacunarity)
        noise_type = getattr(cfg, "noise_type", "FBM")
        coords_local = coords
        if coords_local is not None and len(coords_local) == 2:
            evolution = float(getattr(cfg, "evolution", 0.0))
            if evolution != 0.0:
                zero = xp.zeros_like(coords_local[0])
                evo = xp.full_like(coords_local[0], evolution)
                coords_local = (coords_local[0], coords_local[1], zero, evo)
        if use_gpu:
            return perlin_fractal_distorted_gpu(
                coords_local, detail=detail, roughness=roughness, lacunarity=lacunarity,
                offset=cfg.noise_offset, gain=cfg.noise_gain, distortion=cfg.distortion,
                noise_type=noise_type, normalize=cfg.normalize, seed=cfg.seed,
                cancel_check=cancel_check)
        return perlin_fractal_distorted(
            coords_local, detail=detail, roughness=roughness, lacunarity=lacunarity,
            offset=cfg.noise_offset, gain=cfg.noise_gain, distortion=cfg.distortion,
            noise_type=noise_type, normalize=cfg.normalize, seed=cfg.seed,
            cancel_check=cancel_check)

    if t == "wave":
        if use_gpu:
            return wave_texture_gpu(coords, wave_type=cfg.wave_type,
                                   bands_dir=cfg.wave_dir, rings_dir=cfg.wave_rings_dir,
                                   profile=cfg.wave_profile, phase=cfg.phase_offset, seed=cfg.seed,
                                   distortion=cfg.distortion, detail=cfg.detail,
                                   detail_scale=cfg.wave_detail_scale,
                                   detail_roughness=cfg.wave_detail_roughness)
        return wave_texture(coords, wave_type=cfg.wave_type,
                           bands_dir=cfg.wave_dir, rings_dir=cfg.wave_rings_dir,
                           profile=cfg.wave_profile, phase=cfg.phase_offset, seed=cfg.seed,
                           distortion=cfg.distortion, detail=cfg.detail,
                           detail_scale=cfg.wave_detail_scale,
                           detail_roughness=cfg.wave_detail_roughness)

    if t == "magic":
        if use_gpu:
            return magic_texture_gpu(coords, depth=cfg.depth, distortion=cfg.distortion)
        return magic_texture(coords, depth=cfg.depth, distortion=cfg.distortion)

    if t == "gabor":
        if use_gpu:
            return gabor_texture_gpu(coords, frequency=cfg.gabor_frequency,
                                     anisotropy=cfg.gabor_anisotropy,
                                     orientation_deg=cfg.gabor_orientation)
        return gabor_texture(coords, frequency=cfg.gabor_frequency,
                             anisotropy=cfg.gabor_anisotropy,
                             orientation_deg=cfg.gabor_orientation)

    if t == "white_noise":
        if use_gpu:
            return white_noise_gpu(coords, seed=cfg.seed)
        return white_noise(coords, seed=cfg.seed)

    if t == "gradient":
        if use_gpu:
            return gradient_texture_gpu(coords, subtype=cfg.subtype)
        return gradient_texture(coords, subtype=cfg.subtype)

    if t in ["voronoi", "cellular"]:
        if use_gpu:
            return voronoi_texture_gpu(
                coords, seed=cfg.seed, randomness=cfg.jitter,
                distance_metric=cfg.distance_metric, feature=cfg.return_type,
                smoothness=cfg.smoothness, detail=cfg.detail,
                roughness=cfg.roughness, lacunarity=cfg.lacunarity,
                exponent=cfg.exponent, normalize=cfg.normalize,
                output=cfg.voronoi_output, node_scale=node_scale)
        return voronoi_texture(
            coords, seed=cfg.seed, randomness=cfg.jitter,
            distance_metric=cfg.distance_metric, feature=cfg.return_type,
            smoothness=cfg.smoothness, detail=cfg.detail,
            roughness=cfg.roughness, lacunarity=cfg.lacunarity,
            exponent=cfg.exponent, normalize=cfg.normalize,
            output=cfg.voronoi_output, node_scale=node_scale)

    if t == "brick":
        if use_gpu:
            return brick_texture_gpu(
                coords, offset=cfg.row_offset,
                mortar_size=cfg.mortar_size,
                mortar_smooth=cfg.mortar_smooth, bias=0.0,
                brick_width=cfg.brick_ratio, row_height=cfg.brick_row_height,
                offset_frequency=cfg.brick_offset_frequency,
                squash_amount=cfg.brick_squash,
                squash_frequency=cfg.brick_squash_frequency)
        return brick_texture(
            coords, offset=cfg.row_offset,
            mortar_size=cfg.mortar_size,
            mortar_smooth=cfg.mortar_smooth, bias=0.0,
            brick_width=cfg.brick_ratio, row_height=cfg.brick_row_height,
            offset_frequency=cfg.brick_offset_frequency,
            squash_amount=cfg.brick_squash,
            squash_frequency=cfg.brick_squash_frequency)

    if use_gpu:
        return xp.zeros((height, width), dtype=xp.float32)
    return np.zeros((height, width), dtype=np.float32)
