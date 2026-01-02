"""
Noise Master - Unified Pattern Generators

Single entry point for all pattern generation.
All functions return np.ndarray (float32) in range [0.0, 1.0].
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

# Safe import for noise library
try:
    import noise
    HAS_NOISE = True
except ImportError:
    HAS_NOISE = False
    noise = None


@dataclass
class LayerData:
    """Immutable layer configuration."""
    name: str = "Layer"
    type: str = "perlin"
    visible: bool = True
    blend_mode: str = "normal"
    opacity: float = 1.0
    
    # Transform
    scale: float = 10.0
    rotation: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    
    # Noise params
    seed: int = 0
    octaves: int = 4
    persistence: float = 0.5
    lacunarity: float = 2.0
    
    # Modifiers
    invert: bool = False
    ridged: bool = False
    
    # Type-specific
    subtype: str = "linear"


def generate(layer: LayerData, width: int, height: int) -> np.ndarray:
    """
    Single entry point for all pattern generation.
    
    Args:
        layer: Layer configuration
        width: Output width in pixels
        height: Output height in pixels
        
    Returns:
        np.ndarray: float32 array [0.0, 1.0] of shape (height, width)
    """
    # Create coordinate grid
    coords = _create_coords(width, height, layer)
    
    # Dispatch to generator
    generators = {
        'perlin': _gen_perlin,
        'simplex': _gen_simplex,
        'cellular': _gen_cellular,
        'voronoi': _gen_cellular,
        'gradient': _gen_gradient,
        'checker': _gen_checker,
        'grid': _gen_grid,
        'brick': _gen_brick,
    }
    
    gen_func = generators.get(layer.type, _gen_perlin)
    result = gen_func(coords, layer)
    
    # Apply modifiers
    if layer.ridged:
        result = 1.0 - 2.0 * np.abs(result - 0.5)
    if layer.invert:
        result = 1.0 - result
        
    return np.clip(result, 0.0, 1.0).astype(np.float32)


def _create_coords(width: int, height: int, layer: LayerData) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create normalized coordinate grids with transform applied.
    
    Returns:
        (nx, ny): Coordinate arrays of shape (height, width)
    """
    # Base grid [0, 1]
    x = np.linspace(0, 1, width, dtype=np.float32)
    y = np.linspace(0, 1, height, dtype=np.float32)
    nx, ny = np.meshgrid(x, y)
    
    # Center for rotation
    nx -= 0.5
    ny -= 0.5
    
    # Rotation
    if layer.rotation != 0:
        rad = np.radians(layer.rotation)
        cos_r, sin_r = np.cos(rad), np.sin(rad)
        rx = nx * cos_r - ny * sin_r
        ry = nx * sin_r + ny * cos_r
        nx, ny = rx, ry
    
    # Offset
    nx += layer.offset_x
    ny += layer.offset_y
    
    # Scale (higher = more detail/repetitions)
    scale = max(0.1, layer.scale)
    nx *= scale
    ny *= scale
    
    return nx, ny


# ============ NOISE GENERATORS ============

def _gen_perlin(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Generate Perlin noise."""
    if not HAS_NOISE:
        return _gen_fallback(coords, layer)
    
    nx, ny = coords
    height, width = nx.shape
    result = np.zeros((height, width), dtype=np.float32)
    
    for y in range(height):
        for x in range(width):
            result[y, x] = noise.pnoise2(
                nx[y, x], ny[y, x],
                octaves=layer.octaves,
                persistence=layer.persistence,
                lacunarity=layer.lacunarity,
                base=layer.seed
            )
    
    # Normalize [-1, 1] -> [0, 1]
    return (result + 1.0) * 0.5


def _gen_simplex(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Generate Simplex noise."""
    if not HAS_NOISE:
        return _gen_fallback(coords, layer)
    
    nx, ny = coords
    height, width = nx.shape
    result = np.zeros((height, width), dtype=np.float32)
    
    for y in range(height):
        for x in range(width):
            result[y, x] = noise.snoise2(
                nx[y, x], ny[y, x],
                octaves=layer.octaves,
                persistence=layer.persistence,
                lacunarity=layer.lacunarity,
                base=layer.seed
            )
    
    return (result + 1.0) * 0.5


def _gen_cellular(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Generate Cellular/Voronoi noise using grid-based approach."""
    nx, ny = coords
    
    # Integer cell coordinates
    ix = np.floor(nx).astype(np.int32)
    iy = np.floor(ny).astype(np.int32)
    
    # Fractional position within cell
    fx = nx - ix
    fy = ny - iy
    
    min_dist = np.full_like(nx, 10.0)
    seed = layer.seed
    
    # Check 3x3 neighborhood
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            # Neighbor cell
            cx = ix + dx
            cy = iy + dy
            
            # Hash to get random point in cell
            px = dx + _hash2d(cx, cy, seed) 
            py = dy + _hash2d(cx, cy, seed + 1)
            
            # Distance to point
            dist = np.sqrt((fx - px)**2 + (fy - py)**2)
            min_dist = np.minimum(min_dist, dist)
    
    # Normalize (typical F1 range is ~0-1.5)
    return np.clip(min_dist, 0.0, 1.0)


def _hash2d(x: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """Simple hash function for pseudo-random values in [0, 1]."""
    return np.mod(np.sin(x * 12.9898 + y * 78.233 + seed) * 43758.5453, 1.0)


def _gen_fallback(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Fallback noise when library not available - simple value noise."""
    nx, ny = coords
    seed = layer.seed
    
    # Grid-based value noise
    ix = np.floor(nx).astype(np.int32)
    iy = np.floor(ny).astype(np.int32)
    fx = nx - ix
    fy = ny - iy
    
    # Corner values
    v00 = _hash2d(ix, iy, seed)
    v10 = _hash2d(ix + 1, iy, seed)
    v01 = _hash2d(ix, iy + 1, seed)
    v11 = _hash2d(ix + 1, iy + 1, seed)
    
    # Bilinear interpolation
    sx = fx * fx * (3 - 2 * fx)  # Smoothstep
    sy = fy * fy * (3 - 2 * fy)
    
    return (v00 * (1 - sx) + v10 * sx) * (1 - sy) + (v01 * (1 - sx) + v11 * sx) * sy


# ============ PATTERN GENERATORS ============

def _gen_gradient(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Generate linear or radial gradient."""
    nx, ny = coords
    
    if layer.subtype == 'radial':
        # Distance from center
        dist = np.sqrt(nx**2 + ny**2)
        # Normalize so edge of unit circle = 1
        return np.clip(1.0 - dist * 2.0 / layer.scale, 0.0, 1.0)
    else:
        # Linear gradient along X axis (rotation handled in coords)
        return np.mod(nx / layer.scale + 0.5, 1.0)


def _gen_checker(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Generate checkerboard pattern."""
    nx, ny = coords
    
    ix = np.floor(nx).astype(np.int32)
    iy = np.floor(ny).astype(np.int32)
    
    return ((ix + iy) % 2).astype(np.float32)


def _gen_grid(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Generate grid lines pattern."""
    nx, ny = coords
    
    # Distance to nearest grid line
    fx = np.abs(nx - np.round(nx))
    fy = np.abs(ny - np.round(ny))
    dist = np.minimum(fx, fy)
    
    # Line thickness based on persistence (0=thin, 1=thick)
    thickness = layer.persistence * 0.3
    
    return np.clip((thickness - dist) / 0.05, 0.0, 1.0)


def _gen_brick(coords: Tuple[np.ndarray, np.ndarray], layer: LayerData) -> np.ndarray:
    """Generate brick pattern."""
    nx, ny = coords
    
    # Stagger every other row
    row = np.floor(ny)
    staggered_x = nx.copy()
    staggered_x[row.astype(np.int32) % 2 == 1] += 0.5
    
    # Distance to cell edge
    fx = np.abs(staggered_x - np.round(staggered_x))
    fy = np.abs(ny - np.round(ny))
    dist = np.minimum(fx, fy)
    
    # Mortar thickness
    mortar = layer.persistence * 0.2
    
    return np.clip((dist - mortar) / 0.05, 0.0, 1.0)
