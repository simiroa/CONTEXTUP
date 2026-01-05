"""
Noise Master - Math helpers (CPU).
"""

import numpy as np


def lerp(a, b, t):
    return a + t * (b - a)


def smoothstep01(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
