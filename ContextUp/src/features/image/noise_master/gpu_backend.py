"""
Noise Master - GPU backend helpers.
"""

from __future__ import annotations

import numpy as np

try:
    import cupy as cp
    GPU_AVAILABLE = True
except Exception:
    cp = None
    GPU_AVAILABLE = False


def get_xp(use_gpu: bool):
    if GPU_AVAILABLE and use_gpu:
        return cp
    return np


def is_gpu_array(arr) -> bool:
    return GPU_AVAILABLE and isinstance(arr, cp.ndarray)


def to_numpy(arr):
    if is_gpu_array(arr):
        return cp.asnumpy(arr)
    return arr
