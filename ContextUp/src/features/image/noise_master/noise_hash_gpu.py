"""
Noise Master - Hash utilities (GPU/CuPy).
"""

import cupy as cp

_U32_MAX = cp.uint32(0xFFFFFFFF)
_INT_MASK = cp.int32(0x7FFFFFFF)


def _u32(x):
    return cp.asarray(x, dtype=cp.uint32)


def _i32(x):
    return cp.asarray(x, dtype=cp.int32)


def _rot_u32(x, k):
    return ((x << cp.uint32(k)) | (x >> cp.uint32(32 - k))) & _U32_MAX


def _jenkins_final(a, b, c):
    c ^= b
    c -= _rot_u32(b, 14)
    a ^= c
    a -= _rot_u32(c, 11)
    b ^= a
    b -= _rot_u32(a, 25)
    c ^= b
    c -= _rot_u32(b, 16)
    a ^= c
    a -= _rot_u32(c, 4)
    b ^= a
    b -= _rot_u32(a, 14)
    c ^= b
    c -= _rot_u32(b, 24)
    return c


def _jenkins_mix(a, b, c):
    a -= c
    a ^= _rot_u32(c, 4)
    c += b
    b -= a
    b ^= _rot_u32(a, 6)
    a += c
    c -= b
    c ^= _rot_u32(b, 8)
    b += a
    a -= c
    a ^= _rot_u32(c, 16)
    c += b
    b -= a
    b ^= _rot_u32(a, 19)
    a += c
    c -= b
    c ^= _rot_u32(b, 4)
    b += a
    return a, b, c


def hash_uint(kx):
    kx = _u32(kx)
    c = cp.uint32(0xdeadbeef + (1 << 2) + 13)
    a = c + kx
    b = c
    c = _jenkins_final(a, b, c)
    return c


def hash_uint2(kx, ky):
    kx = _u32(kx)
    ky = _u32(ky)
    c = cp.uint32(0xdeadbeef + (2 << 2) + 13)
    a = c + kx
    b = c + ky
    c = _jenkins_final(a, b, c)
    return c


def hash_uint3(kx, ky, kz):
    kx = _u32(kx)
    ky = _u32(ky)
    kz = _u32(kz)
    c = cp.uint32(0xdeadbeef + (3 << 2) + 13)
    a = c + kx
    b = c + ky
    c = c + kz
    c = _jenkins_final(a, b, c)
    return c


def hash_uint4(kx, ky, kz, kw):
    kx = _u32(kx)
    ky = _u32(ky)
    kz = _u32(kz)
    kw = _u32(kw)
    c = cp.uint32(0xdeadbeef + (4 << 2) + 13)
    a = c + kx
    b = c + ky
    c = c + kz
    a, b, c = _jenkins_mix(a, b, c)
    a = a + kw
    c = _jenkins_final(a, b, c)
    return c


def hash_uint5(kx, ky, kz, kw, kv):
    return hash_uint(hash_uint4(kx, ky, kz, kw) + _u32(kv))


def uint_to_float_incl(n):
    return _u32(n).astype(cp.float32) * (1.0 / float(0xFFFFFFFF))


def _float_as_uint(x):
    return cp.asarray(x, dtype=cp.float32).view(cp.uint32)


def hash_uint_to_float(kx):
    return uint_to_float_incl(hash_uint(kx))


def hash_uint2_to_float(kx, ky):
    return uint_to_float_incl(hash_uint2(kx, ky))


def hash_uint3_to_float(kx, ky, kz):
    return uint_to_float_incl(hash_uint3(kx, ky, kz))


def hash_uint4_to_float(kx, ky, kz, kw):
    return uint_to_float_incl(hash_uint4(kx, ky, kz, kw))


def hash_float_to_float(k):
    return hash_uint_to_float(_float_as_uint(k))


def hash_float2_to_float(kx, ky):
    return hash_uint2_to_float(_float_as_uint(kx), _float_as_uint(ky))


def hash_float3_to_float(kx, ky, kz):
    return hash_uint3_to_float(_float_as_uint(kx), _float_as_uint(ky), _float_as_uint(kz))


def hash_float4_to_float(kx, ky, kz, kw):
    return hash_uint4_to_float(_float_as_uint(kx), _float_as_uint(ky), _float_as_uint(kz), _float_as_uint(kw))


def _hash_pcg2d_i(ix, iy):
    v_x = _i32(ix) * cp.int32(1664525) + cp.int32(1013904223)
    v_y = _i32(iy) * cp.int32(1664525) + cp.int32(1013904223)
    v_x = v_x + v_y * cp.int32(1664525)
    v_y = v_y + v_x * cp.int32(1664525)
    v_x = v_x ^ (v_x >> cp.int32(16))
    v_y = v_y ^ (v_y >> cp.int32(16))
    v_x = v_x + v_y * cp.int32(1664525)
    v_y = v_y + v_x * cp.int32(1664525)
    return (v_x & _INT_MASK), (v_y & _INT_MASK)


def _hash_pcg3d_i(ix, iy, iz):
    v_x = _i32(ix) * cp.int32(1664525) + cp.int32(1013904223)
    v_y = _i32(iy) * cp.int32(1664525) + cp.int32(1013904223)
    v_z = _i32(iz) * cp.int32(1664525) + cp.int32(1013904223)
    v_x = v_x + v_y * v_z
    v_y = v_y + v_z * v_x
    v_z = v_z + v_x * v_y
    v_x = v_x ^ (v_x >> cp.int32(16))
    v_y = v_y ^ (v_y >> cp.int32(16))
    v_z = v_z ^ (v_z >> cp.int32(16))
    v_x = v_x + v_y * v_z
    v_y = v_y + v_z * v_x
    v_z = v_z + v_x * v_y
    return (v_x & _INT_MASK), (v_y & _INT_MASK), (v_z & _INT_MASK)


def hash_int2_to_float2(ix, iy):
    hx, hy = _hash_pcg2d_i(ix, iy)
    scale = 1.0 / float(0x7FFFFFFF)
    return hx.astype(cp.float32) * scale, hy.astype(cp.float32) * scale


def hash_int2_to_float3(ix, iy):
    hx, hy, hz = _hash_pcg3d_i(ix, iy, cp.int32(0))
    scale = 1.0 / float(0x7FFFFFFF)
    return hx.astype(cp.float32) * scale, hy.astype(cp.float32) * scale, hz.astype(cp.float32) * scale
