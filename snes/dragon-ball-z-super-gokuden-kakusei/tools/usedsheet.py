"""Sheets of glyphs used by real dialogue lines (no garbage lines).
usage: usedsheet.py rom prefix"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from font import glyph
from dialogue import words, line_offset
from PIL import Image, ImageDraw

N = 0xED4 + 193


def odd(c):
    lo = 0x100 if c < 0x500 else 0x500 if c < 0x900 else 0x900
    return ((c - lo) // 8) % 2 == 1


def used_codes(rom):
    s = set()
    for i in range(N):
        ws = [w & 0x7FFF for w in words(rom, line_offset(rom, i)) if w != 0x0A]
        if any(odd(c) for c in ws):
            continue
        s.update(ws)
    return sorted(s)


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    codes = used_codes(rom)
    print(len(codes))
    per, cols = 160, 10
    for p in range(0, len(codes), per):
        chunk = codes[p:p + per]
        im = Image.new("L", (cols * 52, (len(chunk) + cols - 1) // cols * 20), 255)
        d = ImageDraw.Draw(im)
        for k, c in enumerate(chunk):
            X, Y = (k % cols) * 52, (k // cols) * 20
            d.text((X, Y + 4), "%03x" % c, fill=0)
            for y, row in enumerate(glyph(rom, c)):
                for x, v in enumerate(row):
                    if v:
                        im.putpixel((X + 22 + x, Y + y), 0)
        im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(f"{sys.argv[2]}{p // per:02d}.png")
