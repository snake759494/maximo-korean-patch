"""Maximo (Japan) SLPM-62127 Korean patch builder.

  python tools/build.py            -> builds 'Maximo (Japan) (Korean).bin/.cue' in the project root
  python tools/build.py --check    -> only validates translation (glyph count, space, widths)

Inputs : Maximo (Japan).bin (original), translation/strings_ko.tsv, translation/glyphs_jp.txt
Outputs: patched ELF + FONT.PRT written into a copy of the disc image (same sizes, in place).
"""
import sys, os, struct, csv, shutil, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdimg import CD, RAW, HDR
from cdecc import fix_mode2_form1, fix_mode2_form1_batch
import hangul

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, 'Maximo (Japan).bin')
OUT = os.path.join(ROOT, 'Maximo (Japan) (Korean).bin')
ELF_NAME, FONT_NAME = 'SLPM_621.27', 'PSXDATA/GAME/FONT.PRT'

BASE = 0x100000 - 0x80          # vaddr - BASE = ELF file offset
TAB, NGLYPH = 0xD8CF0, 430      # glyph table, code = 0x80 + index
# record i (48B) = quad [x0,y0,0,1, x1,y1,0,1] at TAB-0x20+i*48, then UV [u0,v0,u1,v1] at TAB+i*48
QUAD = TAB - 0x20
REGIONS = [(0xCE650, 0xD0080), (0x1331C0, 0x1331F8)]   # string pools that get repacked
ATLAS_W = ATLAS_H = 512
BG = 159
CTRL = {';': 0x3B, '/': 0x2F, ' ': 0x20}
EXTRA_RENDER = {'.': 8, ',': 8}   # non-Hangul glyphs we draw ourselves: width

def tsv(path):
    return list(csv.DictReader(open(path, encoding='utf-8'), delimiter='\t'))

def tokens(s):
    """split a translation into glyph chars and control codes (<;>, </>)"""
    out = []; i = 0
    while i < len(s):
        if s.startswith('<;>', i): out.append(';'); i += 3
        elif s.startswith('</>', i): out.append('/'); i += 3
        else: out.append(s[i]); i += 1
    return out

def is_hangul(c):
    return '가' <= c <= '힣'

def read_file(cd, name):
    for n, lba, size, _, _ in cd.walk():
        if n == name:
            return lba, cd.read(lba, size)
    raise KeyError(name)

def atlas_from_prt(prt):
    a = np.frombuffer(prt[-ATLAS_W * ATLAS_H:], np.uint8).reshape(ATLAS_H, ATLAS_W)
    return a[::-1].copy()   # stored bottom-up

def rect(r):
    return (round(r[0] * 512), round(512 - r[1] * 512), round(r[2] * 512), round(512 - r[3] * 512))

def plan(rows, jpmap):
    """decide which glyph index holds which character"""
    used = []
    for r in rows:
        for c in tokens(r['ko']):
            if c not in CTRL and c not in used:
                used.append(c)
    keep = {}    # char -> original glyph index (symbols reused as-is)
    for c in used:
        if not is_hangul(c) and c not in EXTRA_RENDER:
            if c not in jpmap:
                raise SystemExit('glyph missing from JP font and not renderable: %r' % c)
            keep[c] = jpmap.index(c)
    new = [c for c in used if c not in keep]
    free = [i for i in range(NGLYPH) if i not in keep.values()]
    if len(new) > len(free):
        raise SystemExit('too many glyphs: need %d, free %d' % (len(new), len(free)))
    assign = dict(keep)
    for c, i in zip(new, free):
        assign[c] = i
    return assign, keep, new

def build_font(elf, prt, assign, keep, new):
    old = atlas_from_prt(prt)
    recs = [list(struct.unpack_from('<4f', elf, TAB + i * 48)) + list(struct.unpack_from('<8f', elf, QUAD + i * 48))
            for i in range(NGLYPH)]
    bitmaps = {}   # index -> (bitmap, quad)
    for c, i in keep.items():
        x0, y0, x1, y1 = rect(recs[i])
        bitmaps[i] = (old[y0:y1, x0:x1].copy(), recs[i][4:12])
    for c in new:
        if c in EXTRA_RENDER:
            w = EXTRA_RENDER[c]
            bm = hangul.render(c, w=w)
            quad = [-w / 2, 22.0, 0.0, 1.0, w / 2, -1.0, 0.0, 1.0]
        else:
            bm = hangul.render(c)
            quad = [-10.0, 22.0, 0.0, 1.0, 10.0, -1.0, 0.0, 1.0]
        bitmaps[assign[c]] = (bm, quad)
    # pack
    atlas = np.full((ATLAS_H, ATLAS_W), BG, np.uint8)
    x = y = 1; rowh = 0
    for i in sorted(bitmaps, key=lambda k: (-bitmaps[k][0].shape[0], k)):
        bm, quad = bitmaps[i]
        h, w = bm.shape
        if x + w + 1 > ATLAS_W:
            x = 1; y += rowh + 1; rowh = 0
        if y + h + 1 > ATLAS_H:
            raise SystemExit('atlas full')
        atlas[y:y + h, x:x + w] = bm
        recs[i][0:4] = [x / 512, 1 - y / 512, (x + w) / 512, 1 - (y + h) / 512]
        recs[i][4:12] = quad
        x += w + 1; rowh = max(rowh, h)
    # unused slots -> 1x1 transparent texel at the bottom-right corner, zero-size quad
    for i in range(NGLYPH):
        if i not in bitmaps:
            recs[i][0:4] = [510 / 512, 2 / 512, 511 / 512, 1 / 512]
            recs[i][4:12] = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    elf = bytearray(elf)
    for i in range(NGLYPH):
        struct.pack_into('<8f', elf, QUAD + i * 48, *recs[i][4:12])
        struct.pack_into('<4f', elf, TAB + i * 48, *recs[i][0:4])
    prt = bytearray(prt)
    prt[-ATLAS_W * ATLAS_H:] = atlas[::-1].tobytes()
    return bytes(elf), bytes(prt), atlas, y + rowh

def encode(s, assign):
    out = []
    for c in tokens(s):
        out.append(CTRL[c] if c in CTRL else 0x80 + assign[c])
    return out

def find_refs(elf, targets):
    refs = {t: [] for t in targets}
    for o in range(0, len(elf) - 3, 4):
        p = struct.unpack_from('<I', elf, o)[0] - BASE
        if p in refs:
            refs[p].append(o)
    return refs

def inject_strings(elf, rows, assign, raw):
    elf = bytearray(elf)
    offs = [int(r['offset'], 16) for r in rows]
    known = {int(r['offset'], 16): r for r in raw}
    for o in offs:
        assert o in known, hex(o)
    refs = {int(r['offset'], 16): [int(x, 16) for x in r['refs'].split(',')] for r in raw}
    report = []
    for lo, hi in REGIONS:
        items = [r for r in rows if lo <= int(r['offset'], 16) < hi]
        elf[lo:hi] = bytes(hi - lo)
        pos = lo; placed = {}
        for r in items:
            data = struct.pack('<%dH' % (len(encode(r['ko'], assign)) + 1), *encode(r['ko'], assign), 0)
            key = data
            if key in placed:          # identical strings share storage
                newoff = placed[key]
            else:
                if pos + len(data) > hi:
                    raise SystemExit('string pool %x overflow' % lo)
                elf[pos:pos + len(data)] = data
                newoff = pos; placed[key] = pos
                pos += len(data)
                pos += (-pos) % 4 if False else 0
            for ref in refs[int(r['offset'], 16)]:
                struct.pack_into('<I', elf, ref, newoff + BASE)
        report.append((lo, hi, pos))
    return bytes(elf), report

def write_image(files):
    """files: list of (lba, data). data length == original size. Copies ORIG -> OUT then patches the
    sectors whose user data changed (EDC/ECC recomputed, vectorised in batches)."""
    shutil.copyfile(ORIG, OUT)
    BATCH = 4096
    with open(OUT, 'r+b') as f:
        for lba, data in files:
            nsec = (len(data) + 2047) // 2048
            data = data + bytes(nsec * 2048 - len(data))
            for b0 in range(0, nsec, BATCH):
                n = min(BATCH, nsec - b0)
                f.seek((lba + b0) * RAW)
                s = np.frombuffer(f.read(n * RAW), np.uint8).reshape(n, RAW).copy()
                new = np.frombuffer(data[b0 * 2048:(b0 + n) * 2048], np.uint8).reshape(n, 2048)
                changed = (s[:, HDR:HDR + 2048] != new).any(1)
                if not changed.any():
                    continue
                s[:, HDR:HDR + 2048] = new
                idx = np.nonzero(changed)[0]
                sub = s[idx]
                fix_mode2_form1_batch(sub)
                s[idx] = sub
                f.seek((lba + b0) * RAW)
                f.write(s.tobytes())
    cue = os.path.splitext(OUT)[0] + '.cue'
    with open(cue, 'w', newline='\r\n') as f:
        f.write('FILE "%s" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n' % os.path.basename(OUT))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--atlas-png')
    ap.add_argument('--no-movie', action='store_true')
    a = ap.parse_args()
    os.chdir(ROOT)
    rows = tsv('translation/strings_ko.tsv')
    raw = tsv('translation/strings_raw.tsv')
    jpmap = open('translation/glyphs_jp.txt', encoding='utf-8').read()
    assign, keep, new = plan(rows, jpmap)
    print('glyphs: %d kept symbols, %d new (%d Hangul), %d free slots left'
          % (len(keep), len(new), sum(map(is_hangul, new)), NGLYPH - len(assign)))
    cd = CD(ORIG)
    elf_lba, elf = read_file(cd, ELF_NAME)
    prt_lba, prt = read_file(cd, FONT_NAME)
    elf2, prt2, atlas, used_h = build_font(elf, prt, assign, keep, new)
    print('atlas rows used: %d/%d px' % (used_h, ATLAS_H))
    elf2, rep = inject_strings(elf2, rows, assign, raw)
    for lo, hi, pos in rep:
        print('pool %06x-%06x used %d/%d bytes' % (lo, hi, pos - lo, hi - lo))
    if a.atlas_png:
        from PIL import Image
        Image.fromarray(np.where(atlas == BG, 60, atlas).astype(np.uint8)).save(a.atlas_png)
    if a.check:
        return
    assert len(elf2) == len(elf) and len(prt2) == len(prt)
    files = [(elf_lba, elf2), (prt_lba, prt2)]
    if not a.no_movie:
        for n, lba, size, _, _ in cd.walk():
            if n.endswith('.PSS'):
                pth = os.path.join(ROOT, 'work', 'patched', os.path.basename(n))
                if os.path.exists(pth):
                    d = open(pth, 'rb').read()
                    if len(d) != size:
                        raise SystemExit('size mismatch ' + pth)
                    files.append((lba, d)); print('movie', os.path.basename(n))
    write_image(files)
    print('wrote', OUT)

if __name__ == '__main__':
    main()
