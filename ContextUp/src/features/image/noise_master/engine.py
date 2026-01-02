"""
Noise Master - Engine

Handles layer compositing, blend modes, and image conversion.
All generation logic is delegated to generators.py.
"""

import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from .generators import LayerData, generate


class NoiseEngine:
    """
    Core engine for Noise Master.
    Handles compositing, blend modes, and export.
    """
    
    def __init__(self, width: int = 256, height: int = 256):
        self.width = width
        self.height = height
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    def render(self, layers: List[Dict[str, Any]]) -> np.ndarray:
        """
        Render all layers into a single heightmap.
        
        Args:
            layers: List of layer dictionaries
            
        Returns:
            np.ndarray: Composited heightmap [0.0, 1.0]
        """
        if not layers:
            return np.zeros((self.height, self.width), dtype=np.float32)
        
        # Start with black canvas
        canvas = np.zeros((self.height, self.width), dtype=np.float32)
        
        # Process layers bottom to top (reverse order since layers[0] is on top)
        for layer_dict in reversed(layers):
            if not layer_dict.get('visible', True):
                continue
            
            # Convert dict to LayerData
            layer = self._dict_to_layer(layer_dict)
            
            # Generate pattern
            pattern = generate(layer, self.width, self.height)
            
            # Apply opacity
            opacity = layer.opacity
            
            # Blend
            canvas = self._blend(canvas, pattern, layer.blend_mode, opacity)
        
        return np.clip(canvas, 0.0, 1.0)
    
    def _dict_to_layer(self, d: Dict[str, Any]) -> LayerData:
        """Convert dictionary to LayerData with safe defaults."""
        return LayerData(
            name=d.get('name', 'Layer'),
            type=d.get('type', 'perlin'),
            visible=d.get('visible', True),
            blend_mode=d.get('blend_mode', 'normal'),
            opacity=d.get('opacity', 1.0),
            scale=d.get('scale', 10.0),
            rotation=d.get('rotation', d.get('angle', 0.0)),
            offset_x=d.get('offset_x', 0.0),
            offset_y=d.get('offset_y', 0.0),
            seed=int(d.get('seed', 0)),
            octaves=int(d.get('octaves', 4)),
            persistence=d.get('persistence', 0.5),
            lacunarity=d.get('lacunarity', 2.0),
            invert=d.get('invert', False),
            ridged=d.get('ridged', False),
            subtype=d.get('subtype', 'linear'),
        )
    
    def _blend(self, base: np.ndarray, layer: np.ndarray, 
               mode: str, opacity: float) -> np.ndarray:
        """Apply blend mode between base and layer."""
        
        if mode == 'normal':
            result = layer
        elif mode == 'add':
            result = base + layer
        elif mode == 'multiply':
            result = base * layer
        elif mode == 'subtract':
            result = base - layer
        elif mode == 'overlay':
            # Overlay: multiply dark, screen light
            mask = base < 0.5
            result = np.where(
                mask,
                2.0 * base * layer,
                1.0 - 2.0 * (1.0 - base) * (1.0 - layer)
            )
        else:
            result = layer
        
        # Apply opacity
        return base * (1.0 - opacity) + result * opacity
    
    def to_image(self, heightmap: np.ndarray) -> Image.Image:
        """Convert heightmap to grayscale PIL Image."""
        data = (np.clip(heightmap, 0.0, 1.0) * 255).astype(np.uint8)
        return Image.fromarray(data, mode='L')
    
    def generate_normal_map(self, heightmap: np.ndarray, 
                           strength: float = 1.0,
                           flip_y: bool = False) -> np.ndarray:
        """
        Generate normal map from heightmap using Sobel.
        
        Returns:
            np.ndarray: RGB normal map (height, width, 3) in [0, 1]
        """
        # Sobel kernels
        dx = np.gradient(heightmap, axis=1) * strength
        dy = np.gradient(heightmap, axis=0) * strength
        
        if flip_y:
            dy = -dy
        
        # Build normal vectors
        nx = -dx
        ny = -dy
        nz = np.ones_like(heightmap)
        
        # Normalize
        length = np.sqrt(nx**2 + ny**2 + nz**2)
        nx /= length
        ny /= length
        nz /= length
        
        # Convert [-1, 1] to [0, 1]
        normal_map = np.stack([
            (nx + 1.0) * 0.5,
            (ny + 1.0) * 0.5,
            (nz + 1.0) * 0.5
        ], axis=-1)
        
        return normal_map.astype(np.float32)
