"""Dialogue font: 16-bit character codes -> 16x16 glyphs.

Each range is a sheet of 2bpp 8x8 tiles, 16 tiles (8 glyphs) per row, so a
glyph's top half is at its 32-byte slot and the bottom half 0x100 bytes later.
Only codes whose (code - first) // 8 is even start a glyph.
"""

RANGES = [  # (first code, end code exclusive, file offset of the sheet)
    (0x100, 0x500, 0x1B00A0),
    (0x500, 0x900, 0x1B8000),
    (0x900, 0x1000, 0x1B3CA0),
]


def glyph_offset(code):
    for lo, hi, off in RANGES:
        if lo <= code < hi:
            return off + (code - lo) * 32
    return None


def glyph(rom, code):
    """16 rows of 16 booleans (plane 0 only; the font uses one colour)."""
    o = glyph_offset(code)
    rows = []
    for y in range(16):
        base = o + (0x100 if y >= 8 else 0) + (y % 8) * 2
        rows.append([bool((rom[base + (x // 8) * 16] >> (7 - x % 8)) & 1) for x in range(16)])
    return rows
