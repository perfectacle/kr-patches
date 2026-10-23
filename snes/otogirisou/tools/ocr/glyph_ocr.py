"""OCR the Hangul glyphs of the dialogue font with macOS Vision, in rows of N glyphs.

usage: glyph_ocr.py rom.sfc first last N scale blur offset outdir > result.tsv
Prints "code<TAB>char" for rows whose recognized length matches the glyph count.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from font import glyph, groups
from PIL import Image, ImageFilter

rom = open(sys.argv[1], 'rb').read()
first, last, N, S, blur, off = map(float, sys.argv[2:8])
first, last, N, S, off = int(first), int(last), int(N), int(S), int(off)
out = sys.argv[8]
os.makedirs(out, exist_ok=True)
gs = groups(rom)
rows = []
starts = [first] + list(range(first + off if off else first + N, last + 1, N))
starts = sorted(set(s for s in starts if s <= last))
for i, s in enumerate(starts):
    e = starts[i + 1] if i + 1 < len(starts) else last + 1
    codes = list(range(s, e))
    W = sum(len(glyph(rom, c, gs)[0]) + 3 for c in codes)
    im = Image.new('L', (W * S + 80, 16 * S + 80), 255)
    x0 = 40
    for c in codes:
        g = glyph(rom, c, gs)
        for y, row in enumerate(g):
            for x, p in enumerate(row):
                if p:
                    im.paste(0, (x0 + x * S, 40 + y * S, x0 + x * S + S, 40 + y * S + S))
        x0 += (len(g[0]) + 3) * S
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    p = f'{out}/{s:04d}.png'
    im.save(p)
    rows.append((p, codes))
res = subprocess.run([os.path.join(os.path.dirname(__file__), 'ocr')] + [p for p, _ in rows],
                     capture_output=True, text=True).stdout.splitlines()
for line, (p, codes) in zip(res, rows):
    text = line.split('\t')[1].replace(' ', '')
    if len(text) == len(codes):
        for c, ch in zip(codes, text):
            print(f'{c}\t{ch}')
    else:
        for c in codes:
            print(f'{c}\t?')
