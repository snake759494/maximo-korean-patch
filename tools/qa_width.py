"""Compare rendered line widths (glyph quad widths) of Korean vs Japanese."""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontinfo import table
from build import tokens, is_hangul
SP = 8
t = table(); m = open('translation/glyphs_jp.txt', encoding='utf-8').read()
W = {}
for i, c in enumerate(m):
    W.setdefault(c, t[i][8] - t[i][4])
def wid(s, hw=20):
    w = 0
    for c in tokens(s):
        if c in ';/': continue
        w += SP if c == ' ' else hw if is_hangul(c) else {'.': 8, ',': 8}.get(c, W.get(c, 22))
    return w
rows = list(csv.DictReader(open('translation/strings_ko.tsv', encoding='utf-8'), delimiter='\t'))
lim = float(sys.argv[1]) if len(sys.argv) > 1 else 1.15
mx = max(wid(r['jp']) for r in rows)
bad = 0
for r in rows:
    a, b = wid(r['jp']), wid(r['ko'])
    if b > 440 or (b > a * lim and b > a + 60):
        bad += 1; print('%s jp=%d ko=%d  %s' % (r['offset'], a, b, r['ko']))
print('max jp width', mx, 'flagged', bad)
