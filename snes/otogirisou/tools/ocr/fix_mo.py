"""Resolve ㅁ/ㅇ confusion in OCR votes from glyph pixels.

In this font ㅇ is a box with empty corners and ㅁ a box with filled corners, which Vision
mixes up. The initial consonant's top-left corner is checked on the first ink row; the
final consonant's bottom-left corner on the last ink row.
usage: fix_mo.py rom.sfc votes.json out.tsv
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from font import glyph, groups

def split(ch):
    n = ord(ch) - 0xAC00
    return n // 588, (n // 28) % 21, n % 28

def join(c, v, j):
    return chr(0xAC00 + c * 588 + v * 28 + j)

CHO_M, CHO_O = 6, 11
JONG_M, JONG_O = 16, 21

rom = open(sys.argv[1], 'rb').read()
gs = groups(rom)
votes = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
out = []
for code in range(1, 1247):
    g = glyph(rom, code, gs)
    v = votes.get(code) or []
    ch = v[0][0] if v else None
    if ch:
        c, vw, j = split(ch)
        ink = [y for y, r in enumerate(g) if any(r)]
        top, bot = ink[0], ink[-1]
        if c in (CHO_M, CHO_O):
            xs = [x for y in range(top, top + 3) for x, p in enumerate(g[y]) if p]
            c = CHO_M if g[top][min(xs)] else CHO_O
        if j in (JONG_M, JONG_O):
            xs = [x for y in range(bot - 2, bot + 1) for x, p in enumerate(g[y]) if p]
            j = JONG_M if g[bot][min(xs)] else JONG_O
        ch = join(c, vw, j)
    out.append(f'{code}\t{ch or "□"}')
open(sys.argv[3], 'w').write('\n'.join(out) + '\n')
