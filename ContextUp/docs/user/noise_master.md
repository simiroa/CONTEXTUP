# Noise Master - Technical Specification (GPU-first)

## Overview

Noise Master is a GPU-first procedural texture generator aligned with Blender 5.0 noise behavior.
CuPy is used when available, with a CPU fallback via NumPy if the GPU is missing.

Key goals:
- Interactive preview with low-latency updates
- Seamless tiling for all types except Gradient
- Blender 5.0 parity for core noise types and parameters
- Effect layers for stack-level processing

## Requirements

- NVIDIA GPU + CUDA 12.x recommended
- Dependency: `cupy-cuda12x`
- CPU fallback uses NumPy

## Architecture

Core modules (`src/features/image/noise_master/`):
- `renderer.py` - GPU-first render pipeline
- `generators.py` - Type dispatch and GPU/CPU routing
- `gpu_backend.py` - Backend selection and array conversion
- `noise_perlin(_gpu).py` - Fractal/Perlin/Simplex kernels
- `noise_voronoi(_gpu).py` - Voronoi kernels
- `noise_patterns(_gpu).py` - Wave/Magic/Brick/Gradient/White/Gabor
- `effects(_gpu).py` - Effect layer kernels (tone/blur/erosion/etc)
- `layers.py` - Layer config and defaults
- `utils.py` - Normal map and output conversion

Pipeline:
```
GUI -> LayerConfig -> Renderer -> Coords -> Noise Gen -> Effects -> Blend -> Output
```

## Layer Types

### Generator Layer
- Produces noise output
- Can be blended into the stack
- Supports transform and noise parameters

### Effect Layer
- Modifies the current stack (`stack_below`) by default
- Supports input selection and multiple masks
- Uses opacity as effect intensity

## Effect Layer Input

Default input:
- `stack_below` (all layers below in the stack)

Optional:
- Specific layer below (by ID) from the UI list

## Masking

- Multiple masks supported
- Each mask has source, mode, strength, invert
- Modes: multiply/add/subtract/max/min
- Mask is combined and applied to effect intensity

## Output Seamless

- Global toggle: when ON, all generator layers are forced seamless (Gradient excluded)
- Effect layers preserve seamless output via wrap-aware sampling
- If seamless is OFF, per-layer seamless works as before

## Interactive Preview

While dragging sliders:
- Render size clamps to 256
- GPU preview is downsampled to 128 before transfer
- fBm detail <= 3, Voronoi detail <= 2
- Effect warp and erosion are skipped
- Only the selected layer is rendered
- "RENDERING..." overlay appears after 150ms

Full-quality render runs after interaction ends.

## Noise Types (Generator)

Common parameters:
- Transform: scale, ratio, rotation, offset
- Seamless tiling (except Gradient)

### fBm / Perlin / Simplex
- Noise types: FBM, Multifractal, Hybrid, Ridged, Hetero
- Detail, roughness, lacunarity, distortion
- Evolution adds W dimension for animation

### Voronoi (Cellular)
- F1, F2, Smooth F1, Distance to Edge, N-Sphere Radius
- Metrics: Euclidean, Manhattan, Chebyshev, Minkowski
- Outputs: distance, color, position, radius

### Wave
- Bands or Rings
- Direction, profile (sine/saw/tri), phase
- Optional distortion via fractal noise

### Magic
- Iterative sine/cosine feedback

### Gradient
- Linear, Quadratic, Easing, Diagonal, Radial, Sphere, Quadratic Sphere
- Seamless is disabled for Gradient

### Brick
- Row offset, mortar size/smooth, squash, row height

### White Noise
- Hash-based values

### Gabor (approximation)
- Directional pattern blending wave and noise

## Effect Types

- Warp (image warp by noise)
- Erosion (thermal/hydraulic)
- Tone (gain/bias/gamma/contrast)
- Clamp
- Normalize
- Quantize
- Blur / Sharpen
- Invert / Ridged
- Slope / Curvature

## Seamless Tiling

Seamless uses 4D torus mapping:
```
x = cos(u * 2pi)
y = sin(u * 2pi)
z = cos(v * 2pi)
w = sin(v * 2pi)
```

Gradient is excluded from seamless.

## Output

- Heightmap or Normal map
- 8-bit or 16-bit export
- Session state is not persisted unless exported

## Environment

- `NOISE_MASTER_PROFILE=1` prints render stage timing
