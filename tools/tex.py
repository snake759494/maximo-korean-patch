"""Maximo texture bank (.TEX / .PRT):
  0x00 magic 01 02 03 04, 0x04 0x10000000, 0x08 u32 nPal, 0x0C u32 nTex, pad to 0x20
  nPal palettes (256 x RGBA, alpha 0x80 = opaque; 4bpp palettes are also 0x400?) -- see parse()
  nTex textures: 16B header (u16 log2w, u16 log2h, u16 psm, u16 ?, u32 byteSize, u32 palIdx?) + pixels
psm 0x13 = 8bpp, 0x14 = 4bpp, 0x00 = 32bpp."""
import struct, sys, os
import numpy as np
from PIL import Image

def parse(d):
    npal, ntex = struct.unpack_from('<II', d, 8)
    for n16 in range(npal + 1):
        start = 0x20 + 64 * n16 + 1024 * (npal - n16)
        try:
            texs, end = _chain(d, start, ntex)
            if end == len(d): break
        except (ValueError, struct.error):
            continue
    else:
        raise ValueError('no chain')
    return _pals(d, npal, n16, texs), texs, end

def _pals(d, npal, n16, texs):
    # which palettes are 16-colour: assume 4bpp textures' palette indices
    idx16 = sorted({t['pal'] for t in texs if t['bpp'] == 4})
    if len(idx16) != n16:
        idx16 = list(range(n16))  # fallback guess
    pals = []; o = 0x20
    for i in range(npal):
        n = 16 if i in idx16 else 256
        pals.append((o, np.frombuffer(d[o:o + n * 4], np.uint8).reshape(n, 4)))
        o += n * 4
    return pals

def _chain(d, o, ntex):
    texs = []
    for i in range(ntex):
        lw, lh, psm, a, size, b = struct.unpack_from('<HHHHII', d, o)
        w, h = 1 << lw, 1 << lh
        mips = psm >> 8; psm &= 0xff
        bpp = {0x13: 8, 0x14: 4, 0x00: 32, 0x01: 24, 0x02: 16}.get(psm)
        if lw == 0 and lh == 0 and psm == 0 and size == 0:
            texs.append(dict(hdr=o, off=o + 16, w=0, h=0, psm=0, bpp=0, pal=0, a=0, b=0, mips=0, size=0, step=0)); o += 16; continue
        exp = sum((w >> m) * (h >> m) for m in range(mips + 1)) * (bpp or 0) // 8
        if bpp is None or size != exp:
            raise ValueError('psm %x size %x at %x' % (psm, size, o))
        pal = b >> 16
        step = size
        if psm == 0x01:  # 24bpp stored as 32bpp words
            step = size * 4 // 3
        texs.append(dict(hdr=o, off=o + 16, w=w, h=h, psm=psm, bpp=bpp, pal=pal, a=a, b=b, mips=mips,
                         size=w * h * bpp // 8 if psm != 1 else w * h * 4, step=step))
        o += 16 + step
    return texs, o

def unswz_pal(p):
    # PS2 CSM1 palette swizzle for 256 colors
    idx = np.arange(256)
    j = (idx & 0xE7) | ((idx & 0x08) << 1) | ((idx & 0x10) >> 1)
    return p[j]

def to_image(d, pals, t, swz=True):
    raw = d[t['off']:t['off'] + t['size']]
    if t['bpp'] == 8:
        ix = np.frombuffer(raw, np.uint8)
    elif t['bpp'] == 4:
        b = np.frombuffer(raw, np.uint8)
        ix = np.empty(b.size * 2, np.uint8); ix[0::2] = b & 15; ix[1::2] = b >> 4
    elif t['bpp'] == 24:
        a = np.frombuffer(raw, np.uint8).reshape(t['h'], t['w'], 4)[..., :3]
        return Image.fromarray(np.ascontiguousarray(a), 'RGB').convert('RGBA')
    else:
        a = np.frombuffer(raw, np.uint8).reshape(t['h'], t['w'], 4).copy()
        a[..., 3] = np.minimum(255, a[..., 3].astype(int) * 2)
        return Image.fromarray(a, 'RGBA')
    pal = pals[t['pal']][1] if t['pal'] < len(pals) else pals[0][1]
    if t['bpp'] == 8 and swz: pal = unswz_pal(pal)
    rgba = pal[ix].reshape(t['h'], t['w'], 4).copy()
    rgba[..., 3] = np.minimum(255, rgba[..., 3].astype(int) * 2)
    return Image.fromarray(rgba, 'RGBA')

if __name__ == '__main__':
    f = sys.argv[1]; out = sys.argv[2]
    d = open(f, 'rb').read()
    pals, texs, end = parse(d)
    print(f, len(pals), len(texs), hex(end), hex(len(d)))
    os.makedirs(out, exist_ok=True)
    for i, t in enumerate(texs):
        if not t['size']: continue
        im = to_image(d, pals, t)
        bg = Image.new('RGBA', im.size, (255, 0, 255, 255)); bg.alpha_composite(im)
        bg.convert('RGB').save(os.path.join(out, '%s_%03d_%dx%d.png' % (os.path.basename(f), i, t['w'], t['h'])))
