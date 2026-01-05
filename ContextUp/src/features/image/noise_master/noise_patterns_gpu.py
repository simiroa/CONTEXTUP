"""
Noise Master - Texture patterns (GPU/CuPy).
"""

import cupy as cp

from .noise_hash_gpu import (
    hash_float_to_float,
    hash_float2_to_float,
    hash_float3_to_float,
    hash_float4_to_float,
)
from .noise_math_gpu import smoothstep01 as _smoothstep01
from .noise_perlin_gpu import fractal_noise, noise_2d


def white_noise(coords, seed=0):
    seed_f = cp.float32(seed)
    dims = len(coords)
    if dims == 2:
        x = coords[0] + seed_f
        y = coords[1] + seed_f * 1.23
        return hash_float2_to_float(x, y)
    if dims == 3:
        x = coords[0] + seed_f
        y = coords[1] + seed_f * 1.23
        z = coords[2] + seed_f * 2.34
        return hash_float3_to_float(x, y, z)
    if dims == 4:
        x = coords[0] + seed_f
        y = coords[1] + seed_f * 1.23
        z = coords[2] + seed_f * 2.34
        w = coords[3] + seed_f * 3.45
        return hash_float4_to_float(x, y, z, w)
    if dims == 5:
        x, y, z, w, v_dim = coords
        return hash_float4_to_float(x + v_dim + seed_f, y, z, w)
    return hash_float_to_float(coords[0] + seed_f)


def magic_texture(coords, depth=2, distortion=1.0):
    if len(coords) >= 4:
        u = coords[0] + coords[2] * 0.7071
        v = coords[1] + coords[3] * 0.7071
        z = coords[4] if len(coords) > 4 else cp.zeros_like(u)
    else:
        u, v = coords[0], coords[1]
        z = cp.zeros_like(u)

    px = cp.fmod(u, 2.0 * cp.pi)
    py = cp.fmod(v, 2.0 * cp.pi)
    pz = cp.fmod(z, 2.0 * cp.pi)

    scale = 1.0
    x = cp.sin((px + py + pz) * 5.0 * scale)
    y = cp.cos((-px + py - pz) * 5.0 * scale)
    zc = -cp.cos((-px - py + pz) * 5.0 * scale)

    n = int(max(0, depth))
    if n > 0:
        x *= distortion
        y *= distortion
        zc *= distortion
        y = -cp.cos(x - y + zc)
        y *= distortion
        if n > 1:
            x = cp.cos(x - y - zc)
            x *= distortion
            if n > 2:
                zc = cp.sin(-x - y - zc)
                zc *= distortion
                if n > 3:
                    x = -cp.cos(-x + y - zc)
                    x *= distortion
                    if n > 4:
                        y = -cp.sin(-x + y + zc)
                        y *= distortion
                        if n > 5:
                            y = -cp.cos(-x + y + zc)
                            y *= distortion
                            if n > 6:
                                x = cp.cos(x + y + zc)
                                x *= distortion
                                if n > 7:
                                    zc = cp.sin(x + y - zc)
                                    zc *= distortion
                                    if n > 8:
                                        x = -cp.cos(-x - y + zc)
                                        x *= distortion
                                        if n > 9:
                                            y = -cp.sin(x - y + zc)
                                            y *= distortion

    if distortion != 0.0:
        d2 = distortion * 2.0
        x = x / d2
        y = y / d2
        zc = zc / d2

    r = 0.5 - x
    g = 0.5 - y
    b = 0.5 - zc
    return cp.clip((r + g + b) / 3.0, 0.0, 1.0).astype(cp.float32)


def wave_texture(coords, wave_type="bands", bands_dir="x",
                 rings_dir="x", profile="sine", phase=0.0,
                 seed=0, distortion=0.0, detail=2.0,
                 detail_scale=1.0, detail_roughness=0.5):
    if len(coords) >= 4:
        u = coords[0] + coords[2] * 0.7071
        v = coords[1] + coords[3] * 0.7071
    else:
        u, v = coords[0], coords[1]

    z = cp.zeros_like(u)
    px = (u + 0.000001) * 0.999999
    py = (v + 0.000001) * 0.999999
    pz = (z + 0.000001) * 0.999999

    t = wave_type.lower()
    d = bands_dir.lower()
    if t == "rings":
        rd = rings_dir.lower()
        rx, ry, rz = px, py, pz
        if rd == "x":
            rx = 0.0 * rx
        elif rd == "y":
            ry = 0.0 * ry
        elif rd == "z":
            rz = 0.0 * rz
        n = cp.sqrt(rx * rx + ry * ry + rz * rz) * 20.0
    else:
        if d == "x":
            n = px * 20.0
        elif d == "y":
            n = py * 20.0
        elif d == "z":
            n = pz * 20.0
        else:
            n = (px + py + pz) * 10.0

    n = n + phase

    if distortion != 0.0:
        p = (px * detail_scale, py * detail_scale, pz * detail_scale)
        noise = fractal_noise(p, seed=seed, detail=detail,
                              roughness=detail_roughness, lacunarity=2.0, normalize=True)
        n += distortion * (noise * 2.0 - 1.0)

    prof = profile.lower()
    if prof == "saw":
        n = n / (2.0 * cp.pi)
        res = n - cp.floor(n)
    elif prof == "tri":
        n = n / (2.0 * cp.pi)
        res = cp.abs(n - cp.floor(n + 0.5)) * 2.0
    else:
        res = 0.5 + 0.5 * cp.sin(n - (cp.pi / 2.0))

    return res.astype(cp.float32)


def gabor_texture(coords, frequency=2.0, anisotropy=1.0, orientation_deg=45.0):
    u, v = coords
    rad = cp.deg2rad(orientation_deg)

    cos_a, sin_a = cp.cos(rad), cp.sin(rad)

    dist = (u * cos_a + v * sin_a) * frequency
    perp = (-u * sin_a + v * cos_a) * frequency * (1.0 - anisotropy * 0.9)

    wave = (cp.sin(dist * 20.123) + 1.0) * 0.5
    noise = noise_2d(u * 10.0, v * 0.1) if anisotropy > 0.5 else 0.5

    res = wave * (1.0 - anisotropy) + noise * anisotropy
    return cp.clip((res + 0.5), 0.0, 1.0).astype(cp.float32)


def gradient_texture(coords, subtype="linear"):
    x, y = coords
    z = cp.zeros_like(x)
    s = subtype.lower().replace(" ", "_").replace("-", "_")
    if s == "linear":
        res = x
    elif s == "quadratic":
        r = cp.maximum(x, 0.0)
        res = r * r
    elif s == "easing":
        r = cp.clip(x, 0.0, 1.0)
        t = r * r
        res = 3.0 * t - 2.0 * t * r
    elif s == "diagonal":
        res = (x + y) * 0.5
    elif s == "radial":
        res = (cp.arctan2(y, x) / (2.0 * cp.pi)) + 0.5
    else:
        r = cp.maximum(0.999999 - cp.sqrt(x * x + y * y + z * z), 0.0)
        if s == "quadratic_sphere":
            res = r * r
        else:
            res = r
    return cp.clip(res, 0.0, 1.0).astype(cp.float32)


def brick_texture(coords, offset=0.5, mortar_size=0.02,
                  mortar_smooth=0.1, bias=0.0,
                  brick_width=0.5, row_height=0.25,
                  offset_frequency=2,
                  squash_amount=1.0,
                  squash_frequency=2):
    if len(coords) >= 4:
        u = coords[0] + coords[2] * 0.7071
        v = coords[1] + coords[3] * 0.7071
    else:
        u, v = coords[0], coords[1]

    x = u
    y = v

    rownum = cp.floor(y / row_height).astype(cp.int32)
    apply_offset = (rownum % max(int(offset_frequency), 1)) == 0
    brick_w = brick_width * cp.where((rownum % max(int(squash_frequency), 1)) == 0, squash_amount, 1.0)
    offset_val = cp.where(apply_offset, brick_w * offset, 0.0)

    bricknum = cp.floor((x + offset_val) / brick_w).astype(cp.int32)
    x_local = (x + offset_val) - brick_w * bricknum
    y_local = y - row_height * rownum

    dx = cp.minimum(x_local, brick_w - x_local)
    dy = cp.minimum(y_local, row_height - y_local)
    min_dist = cp.minimum(dx, dy)

    mortar = cp.zeros_like(min_dist, dtype=cp.float32)
    mask = min_dist < mortar_size
    if mortar_smooth == 0.0:
        mortar = cp.where(mask, 1.0, mortar)
    else:
        md = 1.0 - min_dist / max(mortar_size, 1e-6)
        mortar = cp.where(mask, _smoothstep01(md / mortar_smooth), mortar)

    return cp.clip(mortar, 0.0, 1.0).astype(cp.float32)
