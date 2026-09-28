"""CD-ROM Mode 2 Form 1 sector EDC/ECC (ECMA-130), for rewriting user data in a raw 2352-byte image."""

def _tables():
    ecc_f = [0] * 256
    ecc_b = [0] * 256
    edc = [0] * 256
    for i in range(256):
        j = (i << 1) ^ (0x11D if i & 0x80 else 0)
        ecc_f[i] = j & 0xFF
        ecc_b[i ^ j & 0xFF] = i
        e = i
        for _ in range(8):
            e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
        edc[i] = e
    return ecc_f, ecc_b, edc

ECC_F, ECC_B, EDC = _tables()

def edc_calc(data):
    e = 0
    for b in data:
        e = (e >> 8) ^ EDC[(e ^ b) & 0xFF]
    return e

def _ecc_compute(sec, major_count, minor_count, major_mult, minor_inc, dest):
    # sec: bytearray of whole 2352 sector; operates on bytes from offset 0xC
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        ecc_a = 0
        ecc_b = 0
        for minor in range(minor_count):
            temp = sec[0xC + index]
            index += minor_inc
            if index >= size:
                index -= size
            ecc_a ^= temp
            ecc_b ^= temp
            ecc_a = ECC_F[ecc_a]
        ecc_a = ECC_B[ECC_F[ecc_a] ^ ecc_b]
        sec[dest + major] = ecc_a
        sec[dest + major + major_count] = ecc_a ^ ecc_b

def fix_mode2_form1(sec):
    """sec: bytearray(2352) with sync/header/subheader and 2048 user data at 24. Rewrites EDC and ECC."""
    e = edc_calc(sec[16:16 + 8 + 2048])
    sec[2072:2076] = e.to_bytes(4, 'little')
    # ECC is computed with the header (bytes 12..15) zeroed for Mode 2
    hdr = bytes(sec[12:16])
    sec[12:16] = b'\0\0\0\0'
    _ecc_compute(sec, 86, 24, 2, 86, 2076)       # P parity
    _ecc_compute(sec, 52, 43, 86, 88, 2076 + 172)  # Q parity
    sec[12:16] = hdr
    return sec


# ---- vectorised version for many sectors at once ----
import numpy as _np

_EDC = _np.array(EDC, _np.uint32)
_ECC_F = _np.array(ECC_F, _np.uint8)
_ECC_B = _np.array(ECC_B, _np.uint8)

def _ecc_batch(s, major_count, minor_count, major_mult, minor_inc, dest):
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = _np.zeros(len(s), _np.uint8); b = _np.zeros(len(s), _np.uint8)
        for minor in range(minor_count):
            t = s[:, 0xC + index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= t; b ^= t
            a = _ECC_F[a]
        a = _ECC_B[_ECC_F[a] ^ b]
        s[:, dest + major] = a
        s[:, dest + major + major_count] = a ^ b

def fix_mode2_form1_batch(s):
    """s: uint8 array (N, 2352), modified in place."""
    e = _np.zeros(len(s), _np.uint32)
    for k in range(16, 16 + 8 + 2048):
        e = (e >> 8) ^ _EDC[(e ^ s[:, k]) & 0xFF]
    s[:, 2072:2076] = e.view(_np.uint8).reshape(-1, 4) if e.dtype.byteorder in '<=' else e.byteswap().view(_np.uint8).reshape(-1, 4)
    hdr = s[:, 12:16].copy()
    s[:, 12:16] = 0
    _ecc_batch(s, 86, 24, 2, 86, 2076)
    _ecc_batch(s, 52, 43, 86, 88, 2076 + 172)
    s[:, 12:16] = hdr
    return s
