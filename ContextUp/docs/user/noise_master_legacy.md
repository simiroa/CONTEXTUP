# Noise Master - Legacy Specification (Pre-Rewrite)

This document captures the current Noise Master behavior before the full rewrite.

## Overview

- GPU-first rendering using CuPy when available.
- CPU fallback with NumPy/Numba paths.
- Interactive preview: reduced quality while dragging sliders.

## Pipeline

```
GUI -> LayerConfig -> Renderer -> Coords -> Noise Gen -> Modifiers -> Blend -> Output
```

Key behavior:
- Seamless tiling uses 4D torus mapping (not applied to Gradient).
- Domain warp is applied in 2D path only.
- Erosion runs on GPU when available, otherwise CPU.
- Output returned to CPU for PIL/Tk display.

## Noise Types

Supported types:
- fBm/Perlin/Simplex (noise types: FBM, Multifractal, Hybrid, Ridged, Hetero)
- Voronoi (F1, F2, Smooth F1, Distance to Edge, N-Sphere Radius)
- Wave
- Magic
- Brick
- Gradient
- White Noise
- Gabor (approximation)

## Common Parameters

- Transform: scale, ratio, rotation, offset
- Modifiers: invert, ridged, step
- Seamless tiling
- Blend: normal/add/multiply/overlay/screen/subtract/difference

## Domain Warp

- Uses two noise renders to warp U/V.
- Only applied in 2D (non-seamless) path.

## Erosion

- Thermal and hydraulic types.
- GPU path for CuPy, CPU fallback for NumPy/Numba.

## Interactive Preview

While dragging sliders:
- Render size clamps to 256 (if higher).
- GPU preview is downsampled to 128 before transfer.
- Detail clamped (fBm <= 3, Voronoi <= 2).
- Warp and erosion disabled.
- Only selected layer renders.
- "RENDERING..." overlay appears after 150ms.

## Environment

- `NOISE_MASTER_PROFILE=1` prints render stage timing.
- `NOISE_MASTER_NUMBA=0/1` toggles CPU Numba paths.

## Dependencies

- `cupy-cuda12x` for GPU
- `numba` optional for CPU acceleration
