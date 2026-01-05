"""
Noise Master - Output utilities.
"""

import numpy as np
from PIL import Image


def _to_luminance(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 3 and arr.shape[-1] >= 3:
        return 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
    return arr


def to_8bit_image(arr: np.ndarray) -> Image.Image:
    if arr.ndim == 3:
        data = np.clip(arr, 0.0, 1.0)
        data = (data * 255.0 + 0.5).astype(np.uint8)
        return Image.fromarray(data, mode="RGB")
    data = np.clip(arr, 0.0, 1.0)
    data = (data * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(data, mode="L")


def to_16bit_image(arr: np.ndarray) -> Image.Image:
    if arr.ndim == 3:
        data = np.clip(arr, 0.0, 1.0)
        data = (data * 65535.0 + 0.5).astype(np.uint16)
        return Image.fromarray(data, mode="RGB")
    data = np.clip(arr, 0.0, 1.0)
    data = (data * 65535.0 + 0.5).astype(np.uint16)
    return Image.fromarray(data, mode="I;16")


def generate_normal_map(heightmap: np.ndarray, strength: float = 1.0, format: str = "opengl") -> Image.Image:
    h = _to_luminance(heightmap).astype(np.float32)
    strength = max(0.001, float(strength))

    dx = np.gradient(h, axis=1)
    dy = np.gradient(h, axis=0)

    nx = -dx * strength
    ny = -dy * strength
    nz = np.ones_like(nx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length

    if format.lower() == "directx":
        ny = -ny

    r = (nx * 0.5 + 0.5)
    g = (ny * 0.5 + 0.5)
    b = (nz * 0.5 + 0.5)
    rgb = np.stack([r, g, b], axis=-1)
    return to_8bit_image(rgb)
