"""Find JP u16 glyph strings in the ELF, write translation/strings_jp.tsv and render preview sheets."""
import sys, struct, collections, os
sys.path.insert(0, os.path.dirname(__file__))
from fontinfo import *
from PIL import Image, ImageDraw

d = open(ELF, 'rb').read()
n = len(d) // 2
v = struct.unpack('<%dH' % n, d[:2 * n])
ptrs = collections.defaultdict(list)
for o in range(0, len(d) - 3, 4):
    p = struct.unpack_from('<I', d, o)[0]
    if BASE + 0x80 <= p < BASE + len(d):
        ptrs[p - BASE].append(o)
OK_SMALL = {0x20, 0x0a, 0x3b, 0x2f, 0x5b, 0x5c, 0x5d, 0x5e, 0x7c}
strs = []
i = 0
while i < n:
    if 0x80 <= v[i] < 0x80 + N:
        j = i
        while j < n and (0x80 <= v[j] <= 0x80 + N or v[j] in OK_SMALL):
            j += 1
        if j < n and v[j] == 0 and j - i >= 2 and i * 2 in ptrs:
            strs.append((i * 2, list(v[i:j]), (j + 1) * 2 - i * 2))
        i = j + 1
    else:
        i += 1

def slot_size(off):
    # bytes until next non-zero word after terminator (reusable space)
    e = off
    while struct.unpack_from('<H', d, e)[0] != 0: e += 2
    e += 2
    while e < len(d) and struct.unpack_from('<H', d, e)[0] == 0 and (e - off) < 4096: e += 2
    return e - off

if __name__ == '__main__':
    os.makedirs('translation', exist_ok=True)
    with open('translation/strings_raw.tsv', 'w', encoding='utf-8') as f:
        f.write('id\toffset\tslot\trefs\tcodes\n')
        for k, (o, s, _) in enumerate(strs):
            f.write('%d\t%x\t%d\t%s\t%s\n' % (k, o, slot_size(o), ','.join('%x' % r for r in ptrs[o]), ' '.join('%x' % c for c in s)))
    print(len(strs))
    if len(sys.argv) > 1:
        out = sys.argv[1]
        a = atlas(); t = table()
        per = 25
        for pg in range(0, len(strs), per):
            rows = strs[pg:pg + per]
            im = Image.new('L', (1500, 52 * len(rows)), 255); dr = ImageDraw.Draw(im)
            for r, (o, s, _) in enumerate(rows):
                dr.text((0, r * 52 + 18), str(pg + r), fill=0)
                x = 40
                for c in s:
                    if c < 0x80:
                        x += 16; continue
                    x0, y0, x1, y1 = rect(t[c - 0x80])
                    g = Image.fromarray(a[y0:y1, x0:x1]); g = g.resize((g.width * 2, g.height * 2), 0)
                    if x + g.width > 1500: break
                    im.paste(g, (x, r * 52 + 2)); x += g.width + 2
            im.save(os.path.join(out, 'str_%03d.png' % pg))
