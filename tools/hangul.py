"""Render Hangul/extra glyphs in the Maximo font style (white core + dark outline, binary alpha)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = 'NanumSquareNeo-dEb.ttf'
SS = 4            # supersampling
GW, GH = 20, 23   # glyph bitmap size (== quad size, 1:1 texels)
BODY = 18         # target ink height of a full syllable (px)
# palette indices (FONT.PRT atlas palette, after CSM1 unswizzle)
BG, CORE, EDGE1, EDGE2, OUT = 159, 236, 127, 34, 0

_font = {}
def font(px):
    if px not in _font:
        _font[px] = ImageFont.truetype(FONT, px)
    return _font[px]

def _mask(ch, size_px, box_w, box_h, dy=0):
    f = font(size_px * SS)
    W, H = box_w * SS, box_h * SS
    im = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(im)
    # centre using the reference syllable box so all syllables share a baseline
    ref = f.getbbox('한')
    bb = f.getbbox(ch)
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    y = (H - (ref[3] - ref[1])) // 2 - ref[1] + dy * SS
    dr.text((x, y), ch, fill=255, font=f)
    return im

def render(ch, w=GW, h=GH, size=None, dy=0):
    """returns uint8 index array (h, w)"""
    size = size or 19
    m = _mask(ch, size, w, h, dy)
    core = np.asarray(m.resize((w, h), Image.BOX), np.float32) / 255
    # outline: dilate the hi-res mask by 1 output pixel
    dil = m.filter(ImageFilter.MaxFilter(2 * SS + 1))
    out = np.asarray(dil.resize((w, h), Image.BOX), np.float32) / 255
    idx = np.full((h, w), BG, np.uint8)
    idx[out > 0.30] = OUT
    idx[core > 0.20] = EDGE2
    idx[core > 0.40] = EDGE1
    idx[core > 0.60] = CORE
    return idx

if __name__ == '__main__':
    import sys
    s = sys.argv[1]; out = sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    pal = {BG: (60, 90, 160), CORE: (255, 255, 255), EDGE1: (200, 200, 200), EDGE2: (165, 165, 165), OUT: (38, 38, 38)}
    tiles = [render(c, size=size) for c in s]
    img = np.zeros((GH, GW * len(s), 3), np.uint8)
    for i, t in enumerate(tiles):
        for k, v in pal.items():
            img[:, i * GW:(i + 1) * GW][t == k] = v
    Image.fromarray(img).resize((GW * len(s) * 3, GH * 3), Image.NEAREST).save(out)
