"""Read the patched image back, decode every translated string via its pointer refs and render preview sheets."""
import sys, os, csv, struct
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdimg import CD
import build
os.chdir(build.ROOT)
cd = CD(build.OUT)
_, elf = build.read_file(cd, build.ELF_NAME)
_, prt = build.read_file(cd, build.FONT_NAME)
atlas = build.atlas_from_prt(prt)
recs = [struct.unpack_from('<4f', elf, build.TAB + i * 48) + struct.unpack_from('<8f', elf, build.QUAD + i * 48) for i in range(build.NGLYPH)]
raw = build.tsv('translation/strings_raw.tsv')
rows = {r['offset']: r for r in build.tsv('translation/strings_ko.tsv')}
pal = {159: (40, 60, 110), 236: (255, 255, 255), 127: (200, 200, 200), 96: (185, 185, 185), 34: (165, 165, 165), 0: (30, 30, 30)}
def glyph(i):
    x0, y0, x1, y1 = build.rect(recs[i])
    g = atlas[y0:y1, x0:x1]
    rgb = np.zeros(g.shape + (3,), np.uint8)
    for v in np.unique(g):
        c = pal.get(int(v), (int(v) // 2 + 60,) * 3); rgb[g == v] = c
    return Image.fromarray(rgb), recs[i][8] - recs[i][4]
lines = []; errors = 0
for r in raw:
    for ref in r['refs'].split(','):
        p = struct.unpack_from('<I', elf, int(ref, 16))[0] - build.BASE
        codes = []
        while True:
            c = struct.unpack_from('<H', elf, p)[0]
            if c == 0: break
            codes.append(c); p += 2
        exp = build.encode(rows[r['offset']]['ko'], build.plan(list(rows.values()), open('translation/glyphs_jp.txt', encoding='utf-8').read())[0])
        if codes != exp:
            errors += 1; print('MISMATCH', r['offset'], ref)
    lines.append((r['offset'], codes))
print('strings', len(lines), 'pointer mismatches', errors)
if len(sys.argv) > 1:
    out = sys.argv[1]; per = 40
    for pg in range(0, len(lines), per):
        im = Image.new('RGB', (560, 26 * len(lines[pg:pg + per])), (40, 60, 110)); dr = ImageDraw.Draw(im)
        for k, (off, codes) in enumerate(lines[pg:pg + per]):
            x = 60; dr.text((0, k * 26 + 6), off, fill=(255, 255, 0))
            for c in codes:
                if c < 0x80:
                    x += 8 if c == 0x20 else 0; continue
                g, w = glyph(c - 0x80)
                im.paste(g, (x, k * 26 + 1)); x += int(w) + 1
        im.save(os.path.join(out, 'ko_%03d.png' % pg))
