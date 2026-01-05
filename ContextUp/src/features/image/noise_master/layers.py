"""
Noise Master - Layer configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class LayerConfig:
    uid: str = ""
    # General
    name: str = "Layer"
    layer_kind: str = "generator"
    type: str = "fbm"
    visible: bool = True
    blend_mode: str = "normal"
    opacity: float = 1.0
    seamless: bool = False
    evolution: float = 0.0
    noise_scale: float = 5.0
    normalize: bool = True
    bypass: bool = False

    # Effect Layer
    effect_type: str = "warp"
    input_source: str = "stack_below"
    input_layer_uid: str = ""
    masks: list = field(default_factory=list)

    # Transform
    scale: float = 1.0
    ratio: float = 0.0
    rotation: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    # fBm / Perlin / Simplex
    noise_type: str = "FBM"
    detail: float = 2.0
    roughness: float = 0.5
    lacunarity: float = 2.0
    distortion: float = 0.0
    noise_offset: float = 0.0
    noise_gain: float = 1.0
    seed: int = 0

    # Voronoi
    jitter: float = 1.0
    distance_metric: str = "Euclidean"
    return_type: str = "F1"
    smoothness: float = 1.0
    exponent: float = 0.5
    voronoi_output: str = "Distance"

    # Gradient
    subtype: str = "Linear"

    # Brick
    row_offset: float = 0.5
    brick_ratio: float = 0.5
    brick_row_height: float = 0.25
    brick_offset_frequency: int = 2
    brick_squash: float = 1.0
    brick_squash_frequency: int = 2
    mortar_size: float = 0.02
    mortar_smooth: float = 0.1

    # Magic
    depth: int = 2

    # Wave
    wave_type: str = "Bands"
    wave_dir: str = "X"
    wave_rings_dir: str = "X"
    wave_profile: str = "Sine"
    phase_offset: float = 0.0
    wave_detail_scale: float = 1.0
    wave_detail_roughness: float = 0.5

    # Gabor
    gabor_frequency: float = 2.0
    gabor_anisotropy: float = 1.0
    gabor_orientation: float = 45.0

    # Tone / Clamp / Blur / Sharpen / Curvature
    tone_gain: float = 1.0
    tone_bias: float = 0.0
    tone_gamma: float = 1.0
    tone_contrast: float = 1.0
    clamp_min: float = 0.0
    clamp_max: float = 1.0
    blur_radius: int = 1
    blur_strength: float = 1.0
    sharpen_radius: int = 1
    sharpen_strength: float = 1.0
    slope_strength: float = 1.0
    curvature_mode: str = "Cavity"
    curvature_strength: float = 1.0

    quantize_steps: int = 5

    warp_type: str = "perlin"
    warp_strength: float = 0.0
    warp_scale: float = 4.0
    warp_seed: int = 0

    # Erosion
    erosion_type: str = "thermal"
    erosion_iterations: int = 10
    erosion_rain: float = 0.5
    erosion_evap: float = 0.5
    erosion_solu: float = 0.1

    # Output
    normal_strength: float = 1.0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LayerConfig":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        for k, v in filtered.items():
            field_type = cls.__dataclass_fields__[k].type
            try:
                if field_type == float or field_type == Optional[float]:
                    filtered[k] = float(v)
                elif field_type == int or field_type == Optional[int]:
                    filtered[k] = int(float(v))
                elif field_type == bool:
                    filtered[k] = bool(v)
            except (ValueError, TypeError):
                pass
        return cls(**filtered)
