"""Dialogue/menu font of Totsugeki-hen (VWF renderer at $B7:9763).

  0x100-0x4FF  8x16  $83:DE00 + (c-0x100)*16   16 glyphs per 0x200 bytes, bottom half +0x100
  0x500-0x7EF 16x16  $83:8000 + (c-0x500)*32    8 glyphs per 0x200 bytes, bottom half +0x100
  0x7F0-0xBEF 16x16  $BF:8000 + (c-0x7F0)*32    same layout
  0xC00-       16x16  extra 4 KB blocks added by fontext1 (renderer hook)
Only codes on even sheet rows start a glyph. Plane 0 = glyph, plane 1 = shadow.
"""
import fontext1

RANGES = [  # (first, end, file offset, width in tiles)
    (0x100, 0x500, 0x1DE00, 1),
    (0x500, 0x7F0, 0x18000, 2),
    (0x7F0, 0xBF0, 0x1F8000, 2),
]


def info(code):
    for lo, hi, off, w in RANGES:
        if lo <= code < hi:
            return lo, off + (code - lo) * 16 * w, w
    ext = fontext1.FIRST + len(fontext1.BLOCKS) * fontext1.PER_BLOCK
    if fontext1.FIRST <= code < ext:
        return fontext1.FIRST, fontext1.glyph_offset(code), 2
    return None


def valid(code):
    i = info(code)
    if not i:
        return False
    lo, _, w = i
    if lo == fontext1.FIRST:
        return ((code - lo) % fontext1.PER_BLOCK // 8) % 2 == 0
    return ((code - lo) // (16 // w)) % 2 == 0


def glyph(rom, code, plane=0):
    """rows of booleans (16 high, 8*w wide)."""
    lo, o, w = info(code)
    rows = []
    for y in range(16):
        base = o + (0x100 if y >= 8 else 0) + (y % 8) * 2 + plane
        rows.append([bool((rom[base + (x // 8) * 16] >> (7 - x % 8)) & 1) for x in range(8 * w)])
    return rows


def codes(ext=False):
    for lo, hi, _, _ in RANGES:
        for c in range(lo, hi):
            if valid(c):
                yield c
    if ext:
        yield from fontext1.codes()
