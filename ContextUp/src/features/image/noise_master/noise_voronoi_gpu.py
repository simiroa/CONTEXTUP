"""
Noise Master - Voronoi Noise (GPU/CuPy).
"""

import cupy as cp
import math

from .noise_hash_gpu import hash_int2_to_float2, hash_int2_to_float3
from .noise_math_gpu import lerp as _lerp, smoothstep01 as _smoothstep01


def _voronoi_distance(dx, dy, metric, exponent):
    metric = metric.lower()
    if metric == "manhattan":
        return cp.abs(dx) + cp.abs(dy)
    if metric == "chebyshev":
        return cp.maximum(cp.abs(dx), cp.abs(dy))
    if metric == "minkowski":
        return (cp.abs(dx) ** exponent + cp.abs(dy) ** exponent) ** (1.0 / exponent)
    return cp.sqrt(dx * dx + dy * dy)


def _voronoi_distance_bound(dx, dy, metric, exponent):
    metric = metric.lower()
    if metric == "manhattan":
        return cp.abs(dx) + cp.abs(dy)
    if metric == "chebyshev":
        return cp.maximum(cp.abs(dx), cp.abs(dy))
    if metric == "minkowski":
        return cp.abs(dx) ** exponent + cp.abs(dy) ** exponent
    return dx * dx + dy * dy


def _voronoi_f1(u, v, randomness, metric, exponent, seed):
    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    min_bound = cp.full(u.shape, cp.inf, dtype=cp.float32)
    target_x = cp.zeros_like(u, dtype=cp.float32)
    target_y = cp.zeros_like(v, dtype=cp.float32)

    for oy in range(-1, 2):
        for ox in range(-1, 2):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = ox + hx * randomness
            point_y = oy + hy * randomness
            dx = point_x - local_x
            dy = point_y - local_y
            bound = _voronoi_distance_bound(dx, dy, metric, exponent)
            mask = bound < min_bound
            min_bound = cp.where(mask, bound, min_bound)
            target_x = cp.where(mask, point_x, target_x)
            target_y = cp.where(mask, point_y, target_y)

    dx = target_x - local_x
    dy = target_y - local_y
    return _voronoi_distance(dx, dy, metric, exponent)


def _voronoi_f2(u, v, randomness, metric, exponent, seed):
    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    d1 = cp.full(u.shape, cp.inf, dtype=cp.float32)
    d2 = cp.full(u.shape, cp.inf, dtype=cp.float32)

    for oy in range(-1, 2):
        for ox in range(-1, 2):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = ox + hx * randomness
            point_y = oy + hy * randomness
            dx = point_x - local_x
            dy = point_y - local_y
            bound = _voronoi_distance_bound(dx, dy, metric, exponent)
            mask1 = bound < d1
            d2 = cp.where(mask1, d1, d2)
            d1 = cp.where(mask1, bound, d1)
            mask2 = (~mask1) & (bound < d2)
            d2 = cp.where(mask2, bound, d2)

    if metric.lower() == "minkowski":
        return d2 ** (1.0 / exponent)
    if metric.lower() == "euclidean":
        return cp.sqrt(d2)
    return d2


def _voronoi_smooth_f1(u, v, randomness, metric, exponent, smoothness, seed):
    if smoothness <= 0.0:
        return _voronoi_f1(u, v, randomness, metric, exponent, seed)

    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    smooth_dist = cp.zeros_like(u, dtype=cp.float32)
    h = cp.full(u.shape, -1.0, dtype=cp.float32)

    for oy in range(-2, 3):
        for ox in range(-2, 3):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = ox + hx * randomness
            point_y = oy + hy * randomness
            dx = point_x - local_x
            dy = point_y - local_y
            dist = _voronoi_distance(dx, dy, metric, exponent)
            h = cp.where(h < 0.0, 1.0, _smoothstep01(0.5 + 0.5 * (smooth_dist - dist) / smoothness))
            correction = smoothness * h * (1.0 - h)
            smooth_dist = _lerp(smooth_dist, dist, h) - correction

    return smooth_dist


def _voronoi_f1_output(u, v, randomness, metric, exponent, seed, calc_color):
    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    min_bound = cp.full(u.shape, cp.inf, dtype=cp.float32)
    target_x = cp.zeros_like(u, dtype=cp.float32)
    target_y = cp.zeros_like(v, dtype=cp.float32)
    target_cell_x = cp.zeros_like(cell_x)
    target_cell_y = cp.zeros_like(cell_y)

    for oy in range(-1, 2):
        for ox in range(-1, 2):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = ox + hx * randomness
            point_y = oy + hy * randomness
            dx = point_x - local_x
            dy = point_y - local_y
            bound = _voronoi_distance_bound(dx, dy, metric, exponent)
            mask = bound < min_bound
            min_bound = cp.where(mask, bound, min_bound)
            target_x = cp.where(mask, point_x, target_x)
            target_y = cp.where(mask, point_y, target_y)
            target_cell_x = cp.where(mask, cx, target_cell_x)
            target_cell_y = cp.where(mask, cy, target_cell_y)

    dx = target_x - local_x
    dy = target_y - local_y
    distance = _voronoi_distance(dx, dy, metric, exponent)
    if calc_color:
        cr, cg, cb = hash_int2_to_float3(target_cell_x, target_cell_y)
    else:
        cr = cp.zeros_like(u, dtype=cp.float32)
        cg = cp.zeros_like(u, dtype=cp.float32)
        cb = cp.zeros_like(u, dtype=cp.float32)
    pos_x = target_x + cell_x
    pos_y = target_y + cell_y
    return distance, (cr, cg, cb), (pos_x, pos_y)


def _voronoi_f2_output(u, v, randomness, metric, exponent, seed, calc_color):
    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    d1 = cp.full(u.shape, cp.inf, dtype=cp.float32)
    d2 = cp.full(u.shape, cp.inf, dtype=cp.float32)
    pos1_x = cp.zeros_like(u, dtype=cp.float32)
    pos1_y = cp.zeros_like(v, dtype=cp.float32)
    pos2_x = cp.zeros_like(u, dtype=cp.float32)
    pos2_y = cp.zeros_like(v, dtype=cp.float32)
    cell1_x = cp.zeros_like(cell_x)
    cell1_y = cp.zeros_like(cell_y)
    cell2_x = cp.zeros_like(cell_x)
    cell2_y = cp.zeros_like(cell_y)

    for oy in range(-1, 2):
        for ox in range(-1, 2):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = ox + hx * randomness
            point_y = oy + hy * randomness
            dx = point_x - local_x
            dy = point_y - local_y
            bound = _voronoi_distance_bound(dx, dy, metric, exponent)
            mask1 = bound < d1
            old_d1 = d1
            old_pos1_x = pos1_x
            old_pos1_y = pos1_y
            old_cell1_x = cell1_x
            old_cell1_y = cell1_y
            d1 = cp.where(mask1, bound, d1)
            pos1_x = cp.where(mask1, point_x, pos1_x)
            pos1_y = cp.where(mask1, point_y, pos1_y)
            cell1_x = cp.where(mask1, cx, cell1_x)
            cell1_y = cp.where(mask1, cy, cell1_y)
            d2 = cp.where(mask1, old_d1, d2)
            pos2_x = cp.where(mask1, old_pos1_x, pos2_x)
            pos2_y = cp.where(mask1, old_pos1_y, pos2_y)
            cell2_x = cp.where(mask1, old_cell1_x, cell2_x)
            cell2_y = cp.where(mask1, old_cell1_y, cell2_y)
            mask2 = (~mask1) & (bound < d2)
            d2 = cp.where(mask2, bound, d2)
            pos2_x = cp.where(mask2, point_x, pos2_x)
            pos2_y = cp.where(mask2, point_y, pos2_y)
            cell2_x = cp.where(mask2, cx, cell2_x)
            cell2_y = cp.where(mask2, cy, cell2_y)

    if metric.lower() == "minkowski":
        distance = d2 ** (1.0 / exponent)
    elif metric.lower() == "euclidean":
        distance = cp.sqrt(d2)
    else:
        distance = d2

    if calc_color:
        cr, cg, cb = hash_int2_to_float3(cell2_x, cell2_y)
    else:
        cr = cp.zeros_like(u, dtype=cp.float32)
        cg = cp.zeros_like(u, dtype=cp.float32)
        cb = cp.zeros_like(u, dtype=cp.float32)
    pos_x = pos2_x + cell_x
    pos_y = pos2_y + cell_y
    return distance, (cr, cg, cb), (pos_x, pos_y)


def _voronoi_smooth_f1_output(u, v, randomness, metric, exponent, smoothness, seed, calc_color):
    if smoothness <= 0.0:
        return _voronoi_f1_output(u, v, randomness, metric, exponent, seed, calc_color)

    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    smooth_dist = cp.zeros_like(u, dtype=cp.float32)
    smooth_pos_x = cp.zeros_like(u, dtype=cp.float32)
    smooth_pos_y = cp.zeros_like(v, dtype=cp.float32)
    smooth_r = cp.zeros_like(u, dtype=cp.float32)
    smooth_g = cp.zeros_like(u, dtype=cp.float32)
    smooth_b = cp.zeros_like(u, dtype=cp.float32)
    h = cp.full(u.shape, -1.0, dtype=cp.float32)

    for oy in range(-2, 3):
        for ox in range(-2, 3):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = ox + hx * randomness
            point_y = oy + hy * randomness
            dx = point_x - local_x
            dy = point_y - local_y
            dist = _voronoi_distance(dx, dy, metric, exponent)
            h = cp.where(h < 0.0, 1.0, _smoothstep01(0.5 + 0.5 * (smooth_dist - dist) / smoothness))
            correction = smoothness * h * (1.0 - h)
            smooth_dist = _lerp(smooth_dist, dist, h) - correction
            correction /= 1.0 + 3.0 * smoothness
            if calc_color:
                cr, cg, cb = hash_int2_to_float3(cx, cy)
                smooth_r = _lerp(smooth_r, cr, h) - correction
                smooth_g = _lerp(smooth_g, cg, h) - correction
                smooth_b = _lerp(smooth_b, cb, h) - correction
            smooth_pos_x = _lerp(smooth_pos_x, point_x, h) - correction
            smooth_pos_y = _lerp(smooth_pos_y, point_y, h) - correction

    pos_x = cell_x + smooth_pos_x
    pos_y = cell_y + smooth_pos_y
    return smooth_dist, (smooth_r, smooth_g, smooth_b), (pos_x, pos_y)


def _voronoi_distance_to_edge(u, v, randomness, seed):
    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    min_dist = cp.full(u.shape, cp.inf, dtype=cp.float32)
    vec_closest_x = cp.zeros_like(u, dtype=cp.float32)
    vec_closest_y = cp.zeros_like(v, dtype=cp.float32)

    for oy in range(-1, 2):
        for ox in range(-1, 2):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            vec_x = ox + hx * randomness - local_x
            vec_y = oy + hy * randomness - local_y
            dist = vec_x * vec_x + vec_y * vec_y
            mask = dist < min_dist
            min_dist = cp.where(mask, dist, min_dist)
            vec_closest_x = cp.where(mask, vec_x, vec_closest_x)
            vec_closest_y = cp.where(mask, vec_y, vec_closest_y)

    min_edge = cp.full(u.shape, cp.inf, dtype=cp.float32)
    for oy in range(-1, 2):
        for ox in range(-1, 2):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            vec_x = ox + hx * randomness - local_x
            vec_y = oy + hy * randomness - local_y
            perp_x = vec_x - vec_closest_x
            perp_y = vec_y - vec_closest_y
            perp_len = perp_x * perp_x + perp_y * perp_y
            valid = perp_len > 0.0001
            inv_len = cp.where(valid, 1.0 / cp.sqrt(perp_len), 0.0)
            n_x = perp_x * inv_len
            n_y = perp_y * inv_len
            mid_x = (vec_closest_x + vec_x) * 0.5
            mid_y = (vec_closest_y + vec_y) * 0.5
            dist_edge = mid_x * n_x + mid_y * n_y
            dist_edge = cp.where(valid, dist_edge, min_edge)
            min_edge = cp.minimum(min_edge, dist_edge)

    return min_edge


def _voronoi_n_sphere_radius(u, v, randomness, seed):
    cell_x = cp.floor(u).astype(cp.int32)
    cell_y = cp.floor(v).astype(cp.int32)
    local_x = u - cell_x
    local_y = v - cell_y

    min_dist = cp.full(u.shape, cp.inf, dtype=cp.float32)
    closest_x = cp.zeros_like(u, dtype=cp.float32)
    closest_y = cp.zeros_like(v, dtype=cp.float32)
    closest_offset_x = cp.zeros_like(cell_x)
    closest_offset_y = cp.zeros_like(cell_y)

    for oy in range(-1, 2):
        for ox in range(-1, 2):
            cx = cell_x + ox + seed
            cy = cell_y + oy + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = ox + hx * randomness
            point_y = oy + hy * randomness
            dx = point_x - local_x
            dy = point_y - local_y
            dist = dx * dx + dy * dy
            mask = dist < min_dist
            min_dist = cp.where(mask, dist, min_dist)
            closest_x = cp.where(mask, point_x, closest_x)
            closest_y = cp.where(mask, point_y, closest_y)
            closest_offset_x = cp.where(mask, ox, closest_offset_x)
            closest_offset_y = cp.where(mask, oy, closest_offset_y)

    min_dist = cp.full(u.shape, cp.inf, dtype=cp.float32)
    closest2_x = cp.zeros_like(u, dtype=cp.float32)
    closest2_y = cp.zeros_like(v, dtype=cp.float32)
    for oy in range(-1, 2):
        for ox in range(-1, 2):
            skip = (ox == 0) & (oy == 0)
            cell_off_x = ox + closest_offset_x
            cell_off_y = oy + closest_offset_y
            cx = cell_x + cell_off_x + seed
            cy = cell_y + cell_off_y + seed
            hx, hy = hash_int2_to_float2(cx, cy)
            point_x = cell_off_x + hx * randomness
            point_y = cell_off_y + hy * randomness
            dx = closest_x - point_x
            dy = closest_y - point_y
            dist = dx * dx + dy * dy
            dist = cp.where(skip, min_dist, dist)
            mask = dist < min_dist
            min_dist = cp.where(mask, dist, min_dist)
            closest2_x = cp.where(mask, point_x, closest2_x)
            closest2_y = cp.where(mask, point_y, closest2_y)

    return 0.5 * cp.sqrt((closest2_x - closest_x) ** 2 + (closest2_y - closest_y) ** 2)


def _voronoi_octave(u, v, feat, randomness, metric, exponent, smoothness, seed):
    if feat == "f2":
        return _voronoi_f2(u, v, randomness, metric, exponent, seed)
    if feat in ["smooth_f1", "smooth"] and smoothness != 0.0:
        return _voronoi_smooth_f1(u, v, randomness, metric, exponent, smoothness, seed)
    return _voronoi_f1(u, v, randomness, metric, exponent, seed)


def _fractal_voronoi_distance(u, v, feat, randomness, metric, exponent, smoothness,
                              detail, roughness, lacunarity, max_distance, normalize, seed):
    amplitude = 1.0
    max_amplitude = 0.0
    scale = 1.0
    output = cp.zeros_like(u, dtype=cp.float32)
    zero_input = detail == 0.0 or roughness == 0.0
    remainder = detail - math.floor(detail)
    max_oct = int(math.ceil(detail))

    for i in range(max_oct + 1):
        octave = _voronoi_octave(u * scale, v * scale, feat, randomness,
                                 metric, exponent, smoothness, seed)
        if zero_input:
            max_amplitude = 1.0
            output = octave
            break
        if i <= detail:
            max_amplitude += amplitude
            output += octave * amplitude
            scale *= lacunarity
            amplitude *= roughness
        else:
            if remainder != 0.0:
                max_amplitude = _lerp(max_amplitude, max_amplitude + amplitude, remainder)
                output = _lerp(output, output + octave * amplitude, remainder)

    if normalize and max_distance > 0.0:
        output = output / (max_amplitude * max_distance)
    return output


def _fractal_voronoi_distance_to_edge(u, v, randomness, detail, roughness, lacunarity,
                                      max_distance, normalize, seed):
    amplitude = 1.0
    max_amplitude = max_distance
    scale = 1.0
    distance = cp.full(u.shape, 8.0, dtype=cp.float32)
    zero_input = detail == 0.0 or roughness == 0.0
    remainder = detail - math.floor(detail)
    max_oct = int(math.ceil(detail))

    for i in range(max_oct + 1):
        octave = _voronoi_distance_to_edge(u * scale, v * scale, randomness, seed)
        if zero_input:
            distance = octave
            break
        if i <= detail:
            max_amplitude = _lerp(max_amplitude, max_distance / scale, amplitude)
            distance = _lerp(distance, cp.minimum(distance, octave / scale), amplitude)
            scale *= lacunarity
            amplitude *= roughness
        else:
            if remainder != 0.0:
                lerp_amp = _lerp(max_amplitude, max_distance / scale, amplitude)
                distance = _lerp(distance, cp.minimum(distance, octave / scale), remainder)
                max_amplitude = _lerp(max_amplitude, lerp_amp, remainder)

    if normalize and max_amplitude > 0.0:
        distance = distance / max_amplitude
    return distance


def _voronoi_octave_output(u, v, feat, randomness, metric, exponent, smoothness, seed, calc_color):
    if feat == "f2":
        return _voronoi_f2_output(u, v, randomness, metric, exponent, seed, calc_color)
    if feat in ["smooth_f1", "smooth"] and smoothness != 0.0:
        return _voronoi_smooth_f1_output(u, v, randomness, metric, exponent, smoothness, seed, calc_color)
    return _voronoi_f1_output(u, v, randomness, metric, exponent, seed, calc_color)


def _fractal_voronoi_output(u, v, feat, randomness, metric, exponent, smoothness,
                            detail, roughness, lacunarity, max_distance, normalize, seed,
                            node_scale, calc_color):
    amplitude = 1.0
    max_amplitude = 0.0
    scale = 1.0
    out_distance = cp.zeros_like(u, dtype=cp.float32)
    out_r = cp.zeros_like(u, dtype=cp.float32)
    out_g = cp.zeros_like(u, dtype=cp.float32)
    out_b = cp.zeros_like(u, dtype=cp.float32)
    out_pos_x = cp.zeros_like(u, dtype=cp.float32)
    out_pos_y = cp.zeros_like(v, dtype=cp.float32)
    zero_input = detail == 0.0 or roughness == 0.0
    remainder = detail - math.floor(detail)
    max_oct = int(math.ceil(detail))

    for i in range(max_oct + 1):
        octave_dist, (oct_r, oct_g, oct_b), (oct_px, oct_py) = _voronoi_octave_output(
            u * scale, v * scale, feat, randomness, metric, exponent, smoothness, seed, calc_color)
        if zero_input:
            max_amplitude = 1.0
            out_distance = octave_dist
            out_r, out_g, out_b = oct_r, oct_g, oct_b
            out_pos_x, out_pos_y = oct_px, oct_py
            break
        if i <= detail:
            max_amplitude += amplitude
            out_distance += octave_dist * amplitude
            out_r += oct_r * amplitude
            out_g += oct_g * amplitude
            out_b += oct_b * amplitude
            out_pos_x = _lerp(out_pos_x, oct_px / scale, amplitude)
            out_pos_y = _lerp(out_pos_y, oct_py / scale, amplitude)
            scale *= lacunarity
            amplitude *= roughness
        else:
            if remainder != 0.0:
                max_amplitude = _lerp(max_amplitude, max_amplitude + amplitude, remainder)
                out_distance = _lerp(out_distance, out_distance + octave_dist * amplitude, remainder)
                out_r = _lerp(out_r, out_r + oct_r * amplitude, remainder)
                out_g = _lerp(out_g, out_g + oct_g * amplitude, remainder)
                out_b = _lerp(out_b, out_b + oct_b * amplitude, remainder)
                out_pos_x = _lerp(out_pos_x, _lerp(out_pos_x, oct_px / scale, amplitude), remainder)
                out_pos_y = _lerp(out_pos_y, _lerp(out_pos_y, oct_py / scale, amplitude), remainder)

    if normalize and max_distance > 0.0:
        out_distance = out_distance / (max_amplitude * max_distance)
        if max_amplitude > 0.0:
            out_r = out_r / max_amplitude
            out_g = out_g / max_amplitude
            out_b = out_b / max_amplitude

    if node_scale != 0.0:
        out_pos_x = out_pos_x / node_scale
        out_pos_y = out_pos_y / node_scale
    else:
        out_pos_x = cp.zeros_like(out_pos_x)
        out_pos_y = cp.zeros_like(out_pos_y)

    return out_distance, (out_r, out_g, out_b), (out_pos_x, out_pos_y)


def voronoi_texture_gpu(coords, seed=0, randomness=1.0,
                        distance_metric="euclidean", feature="f1",
                        smoothness=1.0, detail=0.0, roughness=0.5,
                        lacunarity=2.0, exponent=0.5, normalize=True,
                        output="distance", node_scale=1.0):
    if len(coords) >= 4:
        u = coords[0] + coords[2] * 0.7071
        v = coords[1] + coords[3] * 0.7071
    else:
        u, v = coords[0], coords[1]

    randomness = float(cp.clip(randomness, 0.0, 1.0))
    smooth = float(cp.clip(smoothness / 2.0, 0.0, 0.5))
    detail = float(cp.clip(detail, 0.0, 15.0))
    roughness = float(cp.clip(roughness, 0.0, 1.0))
    lacunarity = float(max(lacunarity, 0.0))
    exponent = float(max(exponent, 0.0001))
    metric = distance_metric.lower()

    feat = feature.lower().replace("-", "_").replace(" ", "_")
    out = output.lower().replace("-", "_").replace(" ", "_")
    if feat in ["n_sphere_radius", "n_sphere"]:
        return _voronoi_n_sphere_radius(u, v, randomness, seed)
    if feat in ["distance_to_edge", "edge"]:
        max_distance = 0.5 + 0.5 * randomness
        return _fractal_voronoi_distance_to_edge(
            u, v, randomness, detail, roughness, lacunarity, max_distance, normalize, seed)

    max_distance = _voronoi_distance(0.5 + 0.5 * randomness,
                                     0.5 + 0.5 * randomness,
                                     metric, exponent)
    if feat == "f2":
        max_distance *= 2.0
    calc_color = out == "color"

    dist, (cr, cg, cb), (px, py) = _fractal_voronoi_output(
        u, v, feat, randomness, metric, exponent, smooth, detail, roughness, lacunarity,
        max_distance, normalize, seed, node_scale, calc_color)

    if out == "color":
        return cp.stack([cr, cg, cb], axis=-1).astype(cp.float32)
    if out in ["position", "pos"]:
        return cp.stack([px, py, cp.zeros_like(px)], axis=-1).astype(cp.float32)
    if out == "radius":
        return _voronoi_n_sphere_radius(u, v, randomness, seed)
    return dist.astype(cp.float32)
