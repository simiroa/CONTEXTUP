"""
Noise Master - Perlin/Fractal Noise (GPU/CuPy).
"""

import cupy as cp

from .noise_hash_gpu import (
    hash_uint2,
    hash_uint3,
    hash_uint4,
    hash_uint5,
    hash_float2_to_float,
)
from .noise_math_gpu import lerp as _lerp


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _negate_if(val, mask):
    return cp.where(mask != 0, -val, val)


def _grad2(h, x, y):
    h = h & 7
    u = cp.where(h < 4, x, y)
    v = cp.where(h < 4, y, x) * 2.0
    return _negate_if(u, h & 1) + _negate_if(v, h & 2)


def _grad3(h, x, y, z):
    h = h & 15
    u = cp.where(h < 8, x, y)
    v = cp.where(h < 4, y, cp.where((h == 12) | (h == 14), x, z))
    return _negate_if(u, h & 1) + _negate_if(v, h & 2)


def _grad4(h, x, y, z, w):
    h = h & 31
    u = cp.where(h < 24, x, y)
    v = cp.where(h < 16, y, z)
    s = cp.where(h < 8, z, w)
    return _negate_if(u, h & 1) + _negate_if(v, h & 2) + _negate_if(s, h & 4)


def _grad5(h, x, y, z, w, v):
    h = h & 63
    u = cp.where(h < 48, x, y)
    v = cp.where(h < 32, y, z)
    s = cp.where(h < 16, z, w)
    r = cp.where(h < 8, w, v)
    return (_negate_if(u, h & 1) + _negate_if(v, h & 2) +
            _negate_if(s, h & 4) + _negate_if(r, h & 8))


def _wrap_coord(p):
    correction = 0.5 * (cp.abs(p) >= 1000000.0)
    return cp.fmod(p, 100000.0) + correction


def _perlin_2d(x, y, seed=0):
    xi = cp.floor(x).astype(cp.int32)
    yi = cp.floor(y).astype(cp.int32)
    xf = x - xi
    yf = y - yi
    u = _fade(xf)
    v = _fade(yf)

    xi_u = xi.astype(cp.uint32)
    yi_u = yi.astype(cp.uint32)
    s = cp.uint32(seed)
    n00 = _grad2(hash_uint2(xi_u, yi_u) + s, xf, yf)
    n10 = _grad2(hash_uint2(xi_u + 1, yi_u) + s, xf - 1.0, yf)
    n01 = _grad2(hash_uint2(xi_u, yi_u + 1) + s, xf, yf - 1.0)
    n11 = _grad2(hash_uint2(xi_u + 1, yi_u + 1) + s, xf - 1.0, yf - 1.0)
    return _lerp(_lerp(n00, n10, u), _lerp(n01, n11, u), v)


def _perlin_3d(x, y, z, seed=0):
    xi = cp.floor(x).astype(cp.int32)
    yi = cp.floor(y).astype(cp.int32)
    zi = cp.floor(z).astype(cp.int32)
    xf = x - xi
    yf = y - yi
    zf = z - zi
    u = _fade(xf)
    v = _fade(yf)
    w = _fade(zf)

    xi_u = xi.astype(cp.uint32)
    yi_u = yi.astype(cp.uint32)
    zi_u = zi.astype(cp.uint32)
    s = cp.uint32(seed)

    def h(ix, iy, iz):
        return hash_uint3(ix, iy, iz) + s

    c000 = _grad3(h(xi_u, yi_u, zi_u), xf, yf, zf)
    c100 = _grad3(h(xi_u + 1, yi_u, zi_u), xf - 1.0, yf, zf)
    c010 = _grad3(h(xi_u, yi_u + 1, zi_u), xf, yf - 1.0, zf)
    c110 = _grad3(h(xi_u + 1, yi_u + 1, zi_u), xf - 1.0, yf - 1.0, zf)
    c001 = _grad3(h(xi_u, yi_u, zi_u + 1), xf, yf, zf - 1.0)
    c101 = _grad3(h(xi_u + 1, yi_u, zi_u + 1), xf - 1.0, yf, zf - 1.0)
    c011 = _grad3(h(xi_u, yi_u + 1, zi_u + 1), xf, yf - 1.0, zf - 1.0)
    c111 = _grad3(h(xi_u + 1, yi_u + 1, zi_u + 1), xf - 1.0, yf - 1.0, zf - 1.0)

    return _lerp(_lerp(_lerp(c000, c100, u), _lerp(c010, c110, u), v),
                 _lerp(_lerp(c001, c101, u), _lerp(c011, c111, u), v), w)


def _perlin_4d(x, y, z, w, seed=0):
    xi = cp.floor(x).astype(cp.int32)
    yi = cp.floor(y).astype(cp.int32)
    zi = cp.floor(z).astype(cp.int32)
    wi = cp.floor(w).astype(cp.int32)
    xf = x - xi
    yf = y - yi
    zf = z - zi
    wf = w - wi
    u = _fade(xf)
    v = _fade(yf)
    t = _fade(zf)
    s = _fade(wf)

    xi_u = xi.astype(cp.uint32)
    yi_u = yi.astype(cp.uint32)
    zi_u = zi.astype(cp.uint32)
    wi_u = wi.astype(cp.uint32)
    sd = cp.uint32(seed)

    corners = []
    for i in range(16):
        dx, dy, dz, dw = (i >> 0) & 1, (i >> 1) & 1, (i >> 2) & 1, (i >> 3) & 1
        hv = hash_uint4(xi_u + dx, yi_u + dy, zi_u + dz, wi_u + dw) + sd
        corners.append(_grad4(hv, xf - dx, yf - dy, zf - dz, wf - dw))

    l1 = [_lerp(corners[i * 2], corners[i * 2 + 1], u) for i in range(8)]
    l2 = [_lerp(l1[i * 2], l1[i * 2 + 1], v) for i in range(4)]
    l3 = [_lerp(l2[i * 2], l2[i * 2 + 1], t) for i in range(2)]
    return _lerp(l3[0], l3[1], s)


def _perlin_5d(x, y, z, w, v_dim, seed=0):
    xi = cp.floor(x).astype(cp.int32)
    yi = cp.floor(y).astype(cp.int32)
    zi = cp.floor(z).astype(cp.int32)
    wi = cp.floor(w).astype(cp.int32)
    vi = cp.floor(v_dim).astype(cp.int32)
    xf, yf, zf, wf, vf = x - xi, y - yi, z - zi, w - wi, v_dim - vi
    u, vv, s, t, r = [_fade(f) for f in (xf, yf, zf, wf, vf)]
    sd = cp.uint32(seed)

    corners = []
    for i in range(32):
        dx, dy, dz, dw, dv = (i >> 0) & 1, (i >> 1) & 1, (i >> 2) & 1, (i >> 3) & 1, (i >> 4) & 1
        hv = hash_uint5(xi + dx, yi + dy, zi + dz, wi + dw, vi + dv) + sd
        corners.append(_grad5(hv, xf - dx, yf - dy, zf - dz, wf - dw, vf - dv))

    l1 = [_lerp(corners[i * 2], corners[i * 2 + 1], u) for i in range(16)]
    l2 = [_lerp(l1[i * 2], l1[i * 2 + 1], vv) for i in range(8)]
    l3 = [_lerp(l2[i * 2], l2[i * 2 + 1], s) for i in range(4)]
    l4 = [_lerp(l3[i * 2], l3[i * 2 + 1], t) for i in range(2)]
    return _lerp(l4[0], l4[1], r)


def snoise_2d(x, y, seed=0):
    x = _wrap_coord(x)
    y = _wrap_coord(y)
    return 0.6616 * _perlin_2d(x, y, seed=seed)


def noise_2d(x, y, seed=0):
    return 0.5 * snoise_2d(x, y, seed=seed) + 0.5


def snoise_3d(x, y, z, seed=0):
    x = _wrap_coord(x)
    y = _wrap_coord(y)
    z = _wrap_coord(z)
    return 0.9820 * _perlin_3d(x, y, z, seed=seed)


def noise_3d(x, y, z, seed=0):
    return 0.5 * snoise_3d(x, y, z, seed=seed) + 0.5


def snoise_4d(x, y, z, w, seed=0):
    x = _wrap_coord(x)
    y = _wrap_coord(y)
    z = _wrap_coord(z)
    w = _wrap_coord(w)
    return 0.8344 * _perlin_4d(x, y, z, w, seed=seed)


def noise_4d(x, y, z, w, seed=0):
    return 0.5 * snoise_4d(x, y, z, w, seed=seed) + 0.5


def snoise_5d(x, y, z, w, v_dim, seed=0):
    return 0.8 * _perlin_5d(x, y, z, w, v_dim, seed=seed)


def noise_5d(x, y, z, w, v_dim, seed=0):
    return 0.5 * snoise_5d(x, y, z, w, v_dim, seed=seed) + 0.5


def _perlin_signed(coords, seed=0):
    dims = len(coords)
    if dims == 2:
        return snoise_2d(coords[0], coords[1], seed=seed)
    if dims == 3:
        return snoise_3d(coords[0], coords[1], coords[2], seed=seed)
    if dims == 4:
        return snoise_4d(coords[0], coords[1], coords[2], coords[3], seed=seed)
    if dims == 5:
        return snoise_5d(coords[0], coords[1], coords[2], coords[3], coords[4], seed=seed)
    return snoise_2d(coords[0], coords[1], seed=seed)


def _random_float2_offset(seed):
    sx = hash_float2_to_float(cp.float32(seed), cp.float32(0.0))
    sy = hash_float2_to_float(cp.float32(seed), cp.float32(1.0))
    return (100.0 + float(sx) * 100.0, 100.0 + float(sy) * 100.0)


def _random_float3_offset(seed):
    s0 = hash_float2_to_float(cp.float32(seed), cp.float32(0.0))
    s1 = hash_float2_to_float(cp.float32(seed), cp.float32(1.0))
    s2 = hash_float2_to_float(cp.float32(seed), cp.float32(2.0))
    return (100.0 + float(s0) * 100.0,
            100.0 + float(s1) * 100.0,
            100.0 + float(s2) * 100.0)


def _random_float4_offset(seed):
    s0 = hash_float2_to_float(cp.float32(seed), cp.float32(0.0))
    s1 = hash_float2_to_float(cp.float32(seed), cp.float32(1.0))
    s2 = hash_float2_to_float(cp.float32(seed), cp.float32(2.0))
    s3 = hash_float2_to_float(cp.float32(seed), cp.float32(3.0))
    return (100.0 + float(s0) * 100.0,
            100.0 + float(s1) * 100.0,
            100.0 + float(s2) * 100.0,
            100.0 + float(s3) * 100.0)


def _random_float5_offset(seed):
    s0 = hash_float2_to_float(cp.float32(seed), cp.float32(0.0))
    s1 = hash_float2_to_float(cp.float32(seed), cp.float32(1.0))
    s2 = hash_float2_to_float(cp.float32(seed), cp.float32(2.0))
    s3 = hash_float2_to_float(cp.float32(seed), cp.float32(3.0))
    s4 = hash_float2_to_float(cp.float32(seed), cp.float32(4.0))
    return (100.0 + float(s0) * 100.0,
            100.0 + float(s1) * 100.0,
            100.0 + float(s2) * 100.0,
            100.0 + float(s3) * 100.0,
            100.0 + float(s4) * 100.0)


def _perlin_distortion(coords, strength, seed=0):
    if strength == 0.0:
        return tuple(cp.zeros_like(coords[0], dtype=cp.float32) for _ in coords)
    dims = len(coords)
    if dims == 2:
        off0 = _random_float2_offset(0.0)
        off1 = _random_float2_offset(1.0)
        x = _perlin_signed((coords[0] + off0[0], coords[1] + off0[1]), seed=seed) * strength
        y = _perlin_signed((coords[0] + off1[0], coords[1] + off1[1]), seed=seed) * strength
        return (x, y)
    if dims == 3:
        off0 = _random_float3_offset(0.0)
        off1 = _random_float3_offset(1.0)
        off2 = _random_float3_offset(2.0)
        x = _perlin_signed((coords[0] + off0[0], coords[1] + off0[1], coords[2] + off0[2]), seed=seed) * strength
        y = _perlin_signed((coords[0] + off1[0], coords[1] + off1[1], coords[2] + off1[2]), seed=seed) * strength
        z = _perlin_signed((coords[0] + off2[0], coords[1] + off2[1], coords[2] + off2[2]), seed=seed) * strength
        return (x, y, z)
    if dims == 4:
        off0 = _random_float4_offset(0.0)
        off1 = _random_float4_offset(1.0)
        off2 = _random_float4_offset(2.0)
        off3 = _random_float4_offset(3.0)
        x = _perlin_signed((coords[0] + off0[0], coords[1] + off0[1], coords[2] + off0[2], coords[3] + off0[3]), seed=seed) * strength
        y = _perlin_signed((coords[0] + off1[0], coords[1] + off1[1], coords[2] + off1[2], coords[3] + off1[3]), seed=seed) * strength
        z = _perlin_signed((coords[0] + off2[0], coords[1] + off2[1], coords[2] + off2[2], coords[3] + off2[3]), seed=seed) * strength
        w = _perlin_signed((coords[0] + off3[0], coords[1] + off3[1], coords[2] + off3[2], coords[3] + off3[3]), seed=seed) * strength
        return (x, y, z, w)
    if dims == 5:
        off0 = _random_float5_offset(0.0)
        off1 = _random_float5_offset(1.0)
        off2 = _random_float5_offset(2.0)
        off3 = _random_float5_offset(3.0)
        off4 = _random_float5_offset(4.0)
        x = _perlin_signed((coords[0] + off0[0], coords[1] + off0[1], coords[2] + off0[2], coords[3] + off0[3], coords[4] + off0[4]), seed=seed) * strength
        y = _perlin_signed((coords[0] + off1[0], coords[1] + off1[1], coords[2] + off1[2], coords[3] + off1[3], coords[4] + off1[4]), seed=seed) * strength
        z = _perlin_signed((coords[0] + off2[0], coords[1] + off2[1], coords[2] + off2[2], coords[3] + off2[3], coords[4] + off2[4]), seed=seed) * strength
        w = _perlin_signed((coords[0] + off3[0], coords[1] + off3[1], coords[2] + off3[2], coords[3] + off3[3], coords[4] + off3[4]), seed=seed) * strength
        v = _perlin_signed((coords[0] + off4[0], coords[1] + off4[1], coords[2] + off4[2], coords[3] + off4[3], coords[4] + off4[4]), seed=seed) * strength
        return (x, y, z, w, v)
    return tuple(cp.zeros_like(coords[0], dtype=cp.float32) for _ in coords)


def _perlin_multi_fractal(coords, detail, roughness, lacunarity, seed=0, cancel_check=None):
    value = cp.ones_like(coords[0], dtype=cp.float32)
    pwr = 1.0
    coords_local = coords
    for _ in range(int(detail) + 1):
        if cancel_check and cancel_check():
            break
        value *= (pwr * _perlin_signed(coords_local, seed=seed) + 1.0)
        pwr *= roughness
        coords_local = tuple(c * lacunarity for c in coords_local)

    rmd = detail - int(detail)
    if rmd != 0.0:
        value *= (rmd * pwr * _perlin_signed(coords_local, seed=seed) + 1.0)
    return value


def _perlin_hetero_terrain(coords, detail, roughness, lacunarity, offset, seed=0, cancel_check=None):
    pwr = roughness
    value = offset + _perlin_signed(coords, seed=seed)
    coords_local = tuple(c * lacunarity for c in coords)

    for _ in range(1, int(detail) + 1):
        if cancel_check and cancel_check():
            break
        increment = (_perlin_signed(coords_local, seed=seed) + offset) * pwr * value
        value += increment
        pwr *= roughness
        coords_local = tuple(c * lacunarity for c in coords_local)

    rmd = detail - int(detail)
    if rmd != 0.0:
        increment = (_perlin_signed(coords_local, seed=seed) + offset) * pwr * value
        value += rmd * increment
    return value


def _perlin_hybrid_multi_fractal(coords, detail, roughness, lacunarity, offset, gain, seed=0, cancel_check=None):
    pwr = 1.0
    value = cp.zeros_like(coords[0], dtype=cp.float32)
    weight = cp.ones_like(coords[0], dtype=cp.float32)
    coords_local = coords

    for _ in range(int(detail) + 1):
        if cancel_check and cancel_check():
            break
        active = weight > 0.001
        if not bool(cp.any(active)):
            break
        weight = cp.minimum(weight, 1.0)
        signal = (_perlin_signed(coords_local, seed=seed) + offset) * pwr
        value = cp.where(active, value + weight * signal, value)
        weight = cp.where(active, weight * gain * signal, weight)
        pwr *= roughness
        coords_local = tuple(c * lacunarity for c in coords_local)

    rmd = detail - int(detail)
    if rmd != 0.0:
        active = weight > 0.001
        if bool(cp.any(active)):
            weight = cp.minimum(weight, 1.0)
            signal = (_perlin_signed(coords_local, seed=seed) + offset) * pwr
            value = cp.where(active, value + rmd * weight * signal, value)
    return value


def _perlin_ridged_multi_fractal(coords, detail, roughness, lacunarity, offset, gain, seed=0, cancel_check=None):
    pwr = roughness
    signal = offset - cp.abs(_perlin_signed(coords, seed=seed))
    signal = signal * signal
    value = signal
    coords_local = coords

    for _ in range(1, int(detail) + 1):
        if cancel_check and cancel_check():
            break
        coords_local = tuple(c * lacunarity for c in coords_local)
        weight = cp.clip(signal * gain, 0.0, 1.0)
        signal = offset - cp.abs(_perlin_signed(coords_local, seed=seed))
        signal = signal * signal
        signal = signal * weight
        value += signal * pwr
        pwr *= roughness
    return value


def _perlin_fbm(coords, detail, roughness, lacunarity, normalize, seed=0, cancel_check=None):
    fscale = 1.0
    amp = 1.0
    maxamp = 0.0
    total = cp.zeros_like(coords[0], dtype=cp.float32)

    for _ in range(int(detail) + 1):
        if cancel_check and cancel_check():
            break
        scaled_coords = [c * fscale for c in coords]
        total += _perlin_signed(tuple(scaled_coords), seed=seed) * amp
        maxamp += amp
        amp *= roughness
        fscale *= lacunarity

    rmd = detail - int(detail)
    if rmd != 0.0:
        scaled_coords = [c * fscale for c in coords]
        t = _perlin_signed(tuple(scaled_coords), seed=seed)
        sum2 = total + t * amp
        if normalize:
            return _lerp(0.5 * total / maxamp + 0.5,
                         0.5 * sum2 / (maxamp + amp) + 0.5,
                         rmd).astype(cp.float32)
        return _lerp(total, sum2, rmd).astype(cp.float32)
    return (0.5 * total / maxamp + 0.5).astype(cp.float32) if normalize else total.astype(cp.float32)


def _perlin_select(coords, detail, roughness, lacunarity, offset, gain, noise_type, normalize, seed=0, cancel_check=None):
    t = "fbm" if noise_type is None else str(noise_type).lower().replace("-", "_").replace(" ", "_")
    if t in ["multifractal", "multi_fractal"]:
        return _perlin_multi_fractal(coords, detail, roughness, lacunarity, seed=seed, cancel_check=cancel_check)
    if t == "fbm":
        return _perlin_fbm(coords, detail, roughness, lacunarity, normalize, seed=seed, cancel_check=cancel_check)
    if t in ["hybrid_multifractal", "hybrid_multi_fractal"]:
        return _perlin_hybrid_multi_fractal(coords, detail, roughness, lacunarity, offset, gain, seed=seed, cancel_check=cancel_check)
    if t in ["ridged_multifractal", "ridged_multi_fractal"]:
        return _perlin_ridged_multi_fractal(coords, detail, roughness, lacunarity, offset, gain, seed=seed, cancel_check=cancel_check)
    if t in ["hetero_terrain", "hetero"]:
        return _perlin_hetero_terrain(coords, detail, roughness, lacunarity, offset, seed=seed, cancel_check=cancel_check)
    return _perlin_fbm(coords, detail, roughness, lacunarity, normalize, seed=seed, cancel_check=cancel_check)


def perlin_fractal_distorted_gpu(coords, detail, roughness, lacunarity,
                                 offset, gain, distortion, noise_type,
                                 normalize, seed=0, cancel_check=None):
    coords_local = coords
    if distortion != 0.0:
        disp = _perlin_distortion(coords_local, distortion, seed=seed)
        coords_local = tuple(c + d for c, d in zip(coords_local, disp))
    return _perlin_select(coords_local, detail, roughness, lacunarity, offset, gain, noise_type,
                          normalize, seed=seed, cancel_check=cancel_check)


def fractal_noise(coords, seed=0, detail=2.0,
                  roughness=0.5, lacunarity=2.0,
                  distortion=0.0, normalize=True,
                  cancel_check=None):
    dims = len(coords)
    snoise_func = {2: snoise_2d, 3: snoise_3d, 4: snoise_4d, 5: snoise_5d}[dims]

    if distortion != 0.0:
        new_coords = list(coords)
        for d in range(dims):
            d_offset = 13.5 + d * 100.0
            d_coords = [c + d_offset for c in coords]
            disp = snoise_func(*d_coords, seed=seed + 1337 + d) * distortion
            new_coords[d] = new_coords[d] + disp
        coords = tuple(new_coords)

    detail = max(0.0, float(detail))
    full_octaves = int(detail)

    fscale = 1.0
    amp = 1.0
    maxamp = 0.0
    total = cp.zeros_like(coords[0], dtype=cp.float32)

    for _ in range(full_octaves + 1):
        if cancel_check and cancel_check():
            break
        scaled_coords = [c * fscale for c in coords]
        total += snoise_func(*scaled_coords, seed=seed) * amp
        maxamp += amp
        amp *= roughness
        fscale *= lacunarity

    rmd = detail - full_octaves
    if rmd != 0.0:
        scaled_coords = [c * fscale for c in coords]
        t = snoise_func(*scaled_coords, seed=seed)
        sum2 = total + t * amp
        if normalize:
            res = _lerp(0.5 * total / maxamp + 0.5,
                        0.5 * sum2 / (maxamp + amp) + 0.5,
                        rmd)
        else:
            res = _lerp(total, sum2, rmd)
    else:
        res = 0.5 * total / maxamp + 0.5 if normalize else total

    return res.astype(cp.float32)
