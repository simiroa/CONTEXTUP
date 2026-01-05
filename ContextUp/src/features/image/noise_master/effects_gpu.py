"""
Noise Master - Effects (GPU/CuPy).
"""

from __future__ import annotations

import cupy as cp


def _to_luminance(arr: cp.ndarray) -> cp.ndarray:
    if arr.ndim == 3 and arr.shape[-1] >= 3:
        return 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
    return arr


def _get_neighbors(h: cp.ndarray, wrap: bool = False):
    up = cp.roll(h, -1, axis=0)
    down = cp.roll(h, 1, axis=0)
    left = cp.roll(h, -1, axis=1)
    right = cp.roll(h, 1, axis=1)
    if not wrap:
        up[-1, :] = h[-1, :]
        down[0, :] = h[0, :]
        left[:, -1] = h[:, -1]
        right[:, 0] = h[:, 0]
    return up, down, left, right


def apply_invert(data: cp.ndarray) -> cp.ndarray:
    return 1.0 - data


def apply_ridged(data: cp.ndarray) -> cp.ndarray:
    return 1.0 - 2.0 * cp.abs(data - 0.5)


def apply_quantize(data: cp.ndarray, steps: int = 5) -> cp.ndarray:
    steps = int(max(2, steps))
    return cp.round(data * (steps - 1)) / (steps - 1)


def apply_tone(data: cp.ndarray,
               gain: float = 1.0, bias: float = 0.0,
               gamma: float = 1.0, contrast: float = 1.0) -> cp.ndarray:
    x = data.astype(cp.float32, copy=False)
    x = x + float(bias)
    x = x * float(gain)
    gamma = max(float(gamma), 1e-6)
    x = cp.power(cp.clip(x, 0.0, 1.0), 1.0 / gamma)
    x = (x - 0.5) * float(contrast) + 0.5
    return cp.clip(x, 0.0, 1.0).astype(cp.float32)


def apply_clamp(data: cp.ndarray, vmin: float = 0.0, vmax: float = 1.0) -> cp.ndarray:
    return cp.clip(data, float(vmin), float(vmax)).astype(cp.float32)


def apply_normalize(data: cp.ndarray) -> cp.ndarray:
    vmin = float(cp.min(data))
    vmax = float(cp.max(data))
    if vmax - vmin < 1e-6:
        return cp.zeros_like(data, dtype=cp.float32)
    out = (data - vmin) / (vmax - vmin)
    return cp.clip(out, 0.0, 1.0).astype(cp.float32)


def apply_blur(data: cp.ndarray, radius: int = 1, strength: float = 1.0, wrap: bool = False) -> cp.ndarray:
    radius = int(max(0, radius))
    strength = float(max(0.0, min(1.0, strength)))
    if radius == 0 or strength == 0.0:
        return data.astype(cp.float32, copy=False)

    out = data.astype(cp.float32, copy=True)
    for _ in range(radius):
        up, down, left, right = _get_neighbors(out, wrap=wrap)
        avg = (out + up + down + left + right) * 0.2
        out = out * (1.0 - strength) + avg * strength
    return cp.clip(out, 0.0, 1.0).astype(cp.float32)


def apply_sharpen(data: cp.ndarray, radius: int = 1, strength: float = 0.5, wrap: bool = False) -> cp.ndarray:
    radius = int(max(0, radius))
    strength = float(max(0.0, strength))
    if radius == 0 or strength == 0.0:
        return data.astype(cp.float32, copy=False)
    blurred = apply_blur(data, radius=radius, strength=1.0, wrap=wrap)
    out = data.astype(cp.float32, copy=False) + (data - blurred) * strength
    return cp.clip(out, 0.0, 1.0).astype(cp.float32)


def apply_slope(data: cp.ndarray, strength: float = 1.0) -> cp.ndarray:
    h = _to_luminance(data).astype(cp.float32, copy=False)
    dx = cp.gradient(h, axis=1)
    dy = cp.gradient(h, axis=0)
    slope = cp.sqrt(dx * dx + dy * dy) * float(strength)
    return cp.clip(slope, 0.0, 1.0).astype(cp.float32)


def apply_curvature(data: cp.ndarray, mode: str = "cavity",
                    strength: float = 1.0, wrap: bool = False) -> cp.ndarray:
    h = _to_luminance(data).astype(cp.float32, copy=False)
    up, down, left, right = _get_neighbors(h, wrap=wrap)
    lap = (up + down + left + right) * 0.25 - h
    m = str(mode).lower().replace(" ", "_")
    if m in ["ridge", "convex", "peak"]:
        out = cp.maximum(0.0, lap)
    elif m in ["abs", "absolute"]:
        out = cp.abs(lap)
    else:
        out = cp.maximum(0.0, -lap)
    out = out * float(strength)
    return cp.clip(out, 0.0, 1.0).astype(cp.float32)


def apply_erosion_thermal(heightmap: cp.ndarray, iterations: int = 10,
                          talus: float = 0.01, amount: float = 0.1,
                          wrap: bool = False) -> cp.ndarray:
    h = heightmap.astype(cp.float32, copy=True)
    for _ in range(int(iterations)):
        up, down, left, right = _get_neighbors(h, wrap=wrap)
        avg = (up + down + left + right) * 0.25
        diff = h - avg
        erode_mask = diff > talus
        h = cp.where(erode_mask, h - diff * amount, h)
    return cp.clip(h, 0.0, 1.0).astype(cp.float32)


def apply_erosion_hydraulic(heightmap: cp.ndarray, iterations: int = 10,
                            rain: float = 0.1, evaporation: float = 0.5,
                            solubility: float = 0.1,
                            wrap: bool = False) -> cp.ndarray:
    h = heightmap.astype(cp.float32, copy=True)
    water = cp.zeros_like(h)
    sediment = cp.zeros_like(h)

    for _ in range(int(iterations)):
        water = water + rain
        up, down, left, right = _get_neighbors(h + water, wrap=wrap)
        center = h + water
        flow = (cp.maximum(center - up, 0) +
                cp.maximum(center - down, 0) +
                cp.maximum(center - left, 0) +
                cp.maximum(center - right, 0) + 0.001)

        sediment_cap = water * flow * solubility
        deposit = cp.maximum(sediment - sediment_cap, 0) * evaporation
        erode = cp.maximum(sediment_cap - sediment, 0) * solubility

        h = h + deposit - erode
        sediment = sediment + erode - deposit
        water = water * (1.0 - evaporation)

    return cp.clip(h, 0.0, 1.0).astype(cp.float32)
