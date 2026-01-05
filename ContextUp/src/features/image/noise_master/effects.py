"""
Noise Master - Effects (CPU).
"""

from __future__ import annotations

import numpy as np


def _to_luminance(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 3 and arr.shape[-1] >= 3:
        return 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
    return arr


def _get_neighbors(h: np.ndarray, wrap: bool = False):
    up = np.roll(h, -1, axis=0)
    down = np.roll(h, 1, axis=0)
    left = np.roll(h, -1, axis=1)
    right = np.roll(h, 1, axis=1)
    if not wrap:
        up[-1, :] = h[-1, :]
        down[0, :] = h[0, :]
        left[:, -1] = h[:, -1]
        right[:, 0] = h[:, 0]
    return up, down, left, right


def apply_invert(data: np.ndarray) -> np.ndarray:
    return 1.0 - data


def apply_ridged(data: np.ndarray) -> np.ndarray:
    return 1.0 - 2.0 * np.abs(data - 0.5)


def apply_quantize(data: np.ndarray, steps: int = 5) -> np.ndarray:
    steps = int(max(2, steps))
    return np.round(data * (steps - 1)) / (steps - 1)


def apply_tone(data: np.ndarray,
               gain: float = 1.0, bias: float = 0.0,
               gamma: float = 1.0, contrast: float = 1.0) -> np.ndarray:
    x = data.astype(np.float32, copy=False)
    x = x + float(bias)
    x = x * float(gain)
    gamma = max(float(gamma), 1e-6)
    x = np.power(np.clip(x, 0.0, 1.0), 1.0 / gamma)
    x = (x - 0.5) * float(contrast) + 0.5
    return np.clip(x, 0.0, 1.0).astype(np.float32)


def apply_clamp(data: np.ndarray, vmin: float = 0.0, vmax: float = 1.0) -> np.ndarray:
    return np.clip(data, float(vmin), float(vmax)).astype(np.float32)


def apply_normalize(data: np.ndarray) -> np.ndarray:
    vmin = float(np.min(data))
    vmax = float(np.max(data))
    if vmax - vmin < 1e-6:
        return np.zeros_like(data, dtype=np.float32)
    out = (data - vmin) / (vmax - vmin)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def apply_blur(data: np.ndarray, radius: int = 1, strength: float = 1.0, wrap: bool = False) -> np.ndarray:
    radius = int(max(0, radius))
    strength = float(max(0.0, min(1.0, strength)))
    if radius == 0 or strength == 0.0:
        return data.astype(np.float32, copy=False)

    out = data.astype(np.float32, copy=True)
    for _ in range(radius):
        up, down, left, right = _get_neighbors(out, wrap=wrap)
        avg = (out + up + down + left + right) * 0.2
        out = out * (1.0 - strength) + avg * strength
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def apply_sharpen(data: np.ndarray, radius: int = 1, strength: float = 0.5, wrap: bool = False) -> np.ndarray:
    radius = int(max(0, radius))
    strength = float(max(0.0, strength))
    if radius == 0 or strength == 0.0:
        return data.astype(np.float32, copy=False)
    blurred = apply_blur(data, radius=radius, strength=1.0, wrap=wrap)
    out = data.astype(np.float32, copy=False) + (data - blurred) * strength
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def apply_slope(data: np.ndarray, strength: float = 1.0) -> np.ndarray:
    h = _to_luminance(data).astype(np.float32, copy=False)
    dx = np.gradient(h, axis=1)
    dy = np.gradient(h, axis=0)
    slope = np.sqrt(dx * dx + dy * dy) * float(strength)
    return np.clip(slope, 0.0, 1.0).astype(np.float32)


def apply_curvature(data: np.ndarray, mode: str = "cavity",
                    strength: float = 1.0, wrap: bool = False) -> np.ndarray:
    h = _to_luminance(data).astype(np.float32, copy=False)
    up, down, left, right = _get_neighbors(h, wrap=wrap)
    lap = (up + down + left + right) * 0.25 - h
    m = str(mode).lower().replace(" ", "_")
    if m in ["ridge", "convex", "peak"]:
        out = np.maximum(0.0, lap)
    elif m in ["abs", "absolute"]:
        out = np.abs(lap)
    else:
        out = np.maximum(0.0, -lap)
    out = out * float(strength)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def apply_erosion_thermal(heightmap: np.ndarray, iterations: int = 10,
                          talus: float = 0.01, amount: float = 0.1,
                          wrap: bool = False) -> np.ndarray:
    h = heightmap.copy().astype(np.float32)
    for _ in range(int(iterations)):
        up, down, left, right = _get_neighbors(h, wrap=wrap)
        avg = (up + down + left + right) * 0.25
        diff = h - avg
        erode_mask = diff > talus
        h = np.where(erode_mask, h - diff * amount, h)
    return np.clip(h, 0.0, 1.0).astype(np.float32)


def apply_erosion_hydraulic(heightmap: np.ndarray, iterations: int = 10,
                            rain: float = 0.1, evaporation: float = 0.5,
                            solubility: float = 0.1,
                            wrap: bool = False) -> np.ndarray:
    h = heightmap.copy().astype(np.float32)
    water = np.zeros_like(h)
    sediment = np.zeros_like(h)

    for _ in range(int(iterations)):
        water += rain
        up, down, left, right = _get_neighbors(h + water, wrap=wrap)
        center = h + water
        flow = (np.maximum(center - up, 0) +
                np.maximum(center - down, 0) +
                np.maximum(center - left, 0) +
                np.maximum(center - right, 0) + 0.001)

        sediment_cap = water * flow * solubility
        deposit = np.maximum(sediment - sediment_cap, 0) * evaporation
        erode = np.maximum(sediment_cap - sediment, 0) * solubility

        h += deposit - erode
        sediment += erode - deposit
        water *= (1.0 - evaporation)

    return np.clip(h, 0.0, 1.0).astype(np.float32)
