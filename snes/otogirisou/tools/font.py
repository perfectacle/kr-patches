"""Dialogue font: variable-size 1bpp glyphs in bank $1F, indexed by the group table $00:F4AC.

Group entry (5 bytes): word0 = count | width << 12, word1 = base address in bank $1F,
byte4 = height << 2. Glyph n of a group starts at bit n * width * height from the base.
Each row is `width` bits; the decoder ($00:A57F) takes stream bits [p, p + width) and puts
bit p + width - 1 in the leftmost pixel.

usage: font.py rom.sfc out.png [first last]   (sheet of codes, 32 per row)
"""
import sys

GROUPS = 0x74AC
BANK1F = 0xF8000


def groups(rom):
    out, o, code = [], GROUPS, 1
    while True:
        w0 = rom[o] | rom[o + 1] << 8
        cnt, w = w0 & 0xFFF, w0 >> 12
        if cnt == 0 or w == 0:
            break
        base = rom[o + 2] | rom[o + 3] << 8
        h = (rom[o + 4] >> 2) & 0xF
        out.append((code, cnt, w, h, base))
        code += cnt
        o += 5
    return out


def glyph(rom, code, gs=None):
    """Return rows of 0/1 lists, or None if the code has no glyph."""
    for first, cnt, w, h, base in gs or groups(rom):
        if first <= code < first + cnt:
            bit = (code - first) * w * h
            start = BANK1F + (base & 0x7FFF)
            rows = []
            for _ in range(h):
                v = int.from_bytes(rom[start + (bit >> 3):start + (bit >> 3) + 4], 'little') >> (bit & 7)
                rows.append([(v >> (w - 1 - x)) & 1 for x in range(w)])
                bit += w
            return rows
    return None


def sheet(rom, first, last, scale=2, per_row=32):
    from PIL import Image, ImageDraw
    gs = groups(rom)
    cell = 16
    n = last - first + 1
    rows = (n + per_row - 1) // per_row
    im = Image.new('L', (per_row * cell * scale, rows * (cell + 8) * scale), 255)
    d = ImageDraw.Draw(im)
    for i in range(n):
        g = glyph(rom, first + i, gs)
        cx, cy = (i % per_row) * cell * scale, (i // per_row) * (cell + 8) * scale
        if i % per_row == 0:
            d.text((0, cy), '', fill=128)
        if g:
            for y, row in enumerate(g):
                for x, p in enumerate(row):
                    if p:
                        d.rectangle([cx + x * scale, cy + y * scale, cx + x * scale + scale - 1, cy + y * scale + scale - 1], fill=0)
    return im


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    a = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    b = int(sys.argv[4]) if len(sys.argv) > 4 else a + 255
    sheet(rom, a, b).save(sys.argv[2])
