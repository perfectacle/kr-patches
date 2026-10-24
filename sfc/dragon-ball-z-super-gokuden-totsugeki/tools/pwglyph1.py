"""Redraw the password kana whose 8 px glyphs looked alike, then check glyphs against the table.

usage: pwglyph1.py rom.smc table.txt

The ending password (WRAM $7E:0A00) prints kana codes 0x100-0x2C8 with the 8x16 font.
v1.0 drew Hangul over those slots, and five of them drew the same syllable as another
slot, so a password could not be read off the screen. tables/kr-v1.2-glyphs.txt names the
five slots with the syllables drawn here. The new glyphs follow the strokes of
neighbouring slots (1 px lines, columns 0-6, rows 3-12, no shadow plane), with Galmuri11
as the reference for the syllable shapes.

tables/password.tsv: code, kana, glyph v1.1 showed, glyph to show (Kakusei-hen v1.3 uses
the same list for its password grid and name transfer). Checks, exiting non-zero on failure:
  - the five redrawn slots match the bitmaps below; every other code is unchanged
  - no two password codes draw the same pixels
  - table.txt names every password code with its glyph, so text encoded through the
    table shows what it means
  - no two codes with different names in table.txt draw the same glyph (plane 0 without
    the shadow of plane 1), the check that would have caught 0x12C and 0x142
  - the name entry grid (file 0x7005, written by v1.0) has no two letters that look the same
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402
import font1  # noqa: E402

GLYPHS = {
    0x12C: "다",
    0x142: "동",
    0x14C: "레",
    0x14D: "렉",
    0x1C8: "저",
}
BITMAPS = {  # rows 3-12; '#' = plane 0
    "다": ["#####.#.", "#.....#.", "#.....#.", "#.....##", "#.....#.", "#####.#.",
           "......#.", "......#.", "......#.", "......#."],
    "동": [".######.", ".#......", ".######.", "...#....", "#######.", "........",
           "..###...", ".#...#..", ".#...#..", "..###..."],
    "레": ["###.#.#.", "..#.#.#.", "###.#.#.", "#.###.#.", "#...#.#.", "###.#.#.",
           "....#.#.", "....#.#.", "....#.#.", "....#.#."],
    "렉": ["###.#.#.", "..#.#.#.", "###.#.#.", "#.###.#.", "###.#.#.", "#######.",
           "......#.", "......#.", "......#.", "......#."],
    "저": ["#####.#.", ".##...#.", ".###.##.", ".#.#..#.", "#..#..#.", "#...#.#.",
           "......#.", "......#.", "......#.", "......#."],
}
ROOT = os.path.join(os.path.dirname(__file__), "..")
SAME_SHAPE = [{"0", "O"}]  # 0x280 and 0x2A8 share one glyph in the original font
NAME_GRID = 0x7005  # 16-bit codes up to 0x0000; 0x000A ends a row, 0x82C5/0x82C8 are gaps


def bitmap(ch):
    rows = [[False] * 8 for _ in range(16)]
    for y, r in enumerate(BITMAPS[ch]):
        rows[3 + y] = [p == "#" for p in r]
    return rows


def write(rom, code, rows):
    _, o, _ = font1.info(code)
    for y in range(16):
        base = o + (0x100 if y >= 8 else 0) + (y % 8) * 2
        v = 0
        for x in range(8):
            if rows[y][x]:
                v |= 0x80 >> x
        rom[base] = v
        rom[base + 1] = 0


def load_tsv():
    rows = []
    for line in open(os.path.join(ROOT, "tables", "password.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        c = line.rstrip("\n").split("\t")
        rows.append((int(c[0], 16), c[1], c[2], c[3]))
    return rows


def main():
    path = sys.argv[1]
    rom = bytearray(open(path, "rb").read())
    before = bytes(rom)
    table = D.load_table(sys.argv[2])
    for code, ch in GLYPHS.items():
        write(rom, code, bitmap(ch))
    errs = []
    rows = load_tsv()
    seen = {}
    for code, kana, old, new in rows:
        g = tuple(tuple(r) for r in font1.glyph(rom, code, 0))
        if code in GLYPHS:
            if GLYPHS[code] != new or [list(r) for r in g] != bitmap(new):
                errs.append(f"{code:03X}: redraw does not show {new}")
        else:
            if old != new:
                errs.append(f"{code:03X}: {old} -> {new} but no redraw listed")
            if g != tuple(tuple(r) for r in font1.glyph(before, code, 0)):
                errs.append(f"{code:03X}: pixels changed")
        if g in seen:
            errs.append(f"{code:03X} draws the same pixels as {seen[g]:03X}")
        seen[g] = code
        if table.get(code) not in (new, kana):
            errs.append(f"{code:03X}: table says {table.get(code)!r}, screen shows {new}")
    shapes = {}
    for code, name in sorted(table.items()):
        if not font1.valid(code):
            continue
        p0, p1 = font1.glyph(rom, code, 0), font1.glyph(rom, code, 1)
        shape = tuple(tuple(a and not b for a, b in zip(r0, r1)) for r0, r1 in zip(p0, p1))
        if not any(any(r) for r in shape):
            continue
        other = shapes.setdefault(shape, (code, name))
        if other[1] != name and {other[1], name} not in SAME_SHAPE:
            errs.append(f"{code:03X} {name} draws the same glyph as {other[0]:03X} {other[1]}")
    grid, o = {}, NAME_GRID
    while (w := rom[o] | rom[o + 1] << 8) != 0:
        c = w & 0x7FFF
        if 0x100 <= c < 0x2C5:
            g = tuple(tuple(r) for r in font1.glyph(rom, c, 0))
            if grid.get(g, c) != c:
                errs.append(f"name grid: {c:03X} looks the same as {grid[g]:03X}")
            grid[g] = c
        o += 2
    if errs:
        sys.exit("password glyph check failed:\n  " + "\n  ".join(errs))
    open(path, "wb").write(rom)
    print(f"password glyphs: {len(GLYPHS)} redrawn, {len(rows)} codes checked")


if __name__ == "__main__":
    main()
