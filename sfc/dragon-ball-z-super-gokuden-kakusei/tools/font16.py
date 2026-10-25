"""v1.4: names can use all 11,172 Hangul syllables, typed by composing jamo.

usage: font16.py rom.smc out_dir

Names are drawn with the 16x16 dialogue font (tools/font.py). Its sheets hold 882 Hangul
syllables; the other syllables and the 51 compatibility jamo are drawn with Galmuri11 and get
new codes from FIRST on. Every syllable is there because the name entry composes jamo freely:
뷁 is typed through 뷀, and neither is in KS X 1001. The ROM grows from 2 MB to 4 MB.

The font uses one colour (plane 1 repeats plane 0), so a new glyph is stored 1 bpp: 32 bytes,
two bytes (left, right half) per row, 1024 glyphs per bank from BANK0. asm/v14.asm copies it to
a WRAM buffer in the layout of a sheet row before the renderer draws it.

Writes out_dir/font16_defs.asm (constants), out_dir/font16_data.asm (jamo tables, grid and help
strings of the name entry), out_dir/font16_syl.asm (syllable -> code) and out_dir/kr-v1.4.txt
(the code table plus the new codes).
"""
import os
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import font  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
GLYPH_FONT = os.path.join(ROOT, "tools", "fonts", "Galmuri11.ttf")
TABLE = os.path.join(ROOT, "tables", "kr-v1.3.txt")
OLD_SIZE = 0x200000
NEW_SIZE = 0x400000
FIRST = 0x1000                  # first new code
BANK0 = 0xC0                    # first bank of the new glyphs
PER_BANK = 0x400                # 0x8000 bytes / 32 bytes per glyph
SIZE_BYTE = 0x7FD7              # header ROM size: 2^n KB
CODE_BANK = 0xE0                # asm/v14.asm: the syllable table
JAMO = [chr(c) for c in range(0x3131, 0x3164)]
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
JUNG_MIX = {("ㅗ", "ㅏ"): "ㅘ", ("ㅗ", "ㅐ"): "ㅙ", ("ㅗ", "ㅣ"): "ㅚ", ("ㅜ", "ㅓ"): "ㅝ",
            ("ㅜ", "ㅔ"): "ㅞ", ("ㅜ", "ㅣ"): "ㅟ", ("ㅡ", "ㅣ"): "ㅢ"}
JONG_MIX = {("ㄱ", "ㅅ"): "ㄳ", ("ㄴ", "ㅈ"): "ㄵ", ("ㄴ", "ㅎ"): "ㄶ", ("ㄹ", "ㄱ"): "ㄺ",
            ("ㄹ", "ㅁ"): "ㄻ", ("ㄹ", "ㅂ"): "ㄼ", ("ㄹ", "ㅅ"): "ㄽ", ("ㄹ", "ㅌ"): "ㄾ",
            ("ㄹ", "ㅍ"): "ㄿ", ("ㄹ", "ㅎ"): "ㅀ", ("ㅂ", "ㅅ"): "ㅄ"}
SYL = [chr(c) for c in range(0xAC00, 0xD7A4)]
# Name entry grid: six rows of three groups of five cells, " " an empty cell. The last group
# of the last row is the game's 입력완료 (cell 0x55), copied from the original grid.
GRID = ["ㅂㅈㄷㄱㅅ", "ㅁㄴㅇㄹㅎ", "ㅋㅌㅊㅍ ",
        "ㅃㅉㄸㄲㅆ", "     ", "     ",
        "ㅛㅕㅑㅐㅔ", "ㅗㅓㅏㅣ ", "ㅠㅜㅡ  ",
        "ㅒㅖ   ", "     ", "     ",
        "     ", "     ", "     ",
        "     ", "     "]
GRID_AT = (0x84 & 0x7F) * 0x8000 + 0x23E0     # $84:A3E0, hiragana page
ROW_WORDS = 19                  # blank, 5 cells, blank, 5 cells, blank, 5 cells, newline
DONE_AT = 5 * ROW_WORDS + 13    # 입력완료 in the last row: blank + four codes, then 0
HELP_AT = GRID_AT + 0x1E0       # the name screen's help: icon, label, newline, ...
HELP = [((0x2B7, 0x2B3), "선택"), ((0x2B4,), "지우기"), ((0x2B5,), "띄어쓰기"), ((0x2B6,), "클리어")]  # button icons, label
BLANK, NEWLINE = 0x0272, 0x000A


def load_table():
    table = {}
    for line in open(TABLE, encoding="utf-8"):
        line = line.rstrip("\n")
        if "=" in line:
            k, v = line.split("=", 1)
            table[int(k, 16)] = v
    return table


def is_glyph(code):
    for lo, hi, _ in font.RANGES:
        if lo <= code < hi:
            return (code - lo) // 8 % 2 == 0
    return False


def origin(gfont):
    """One origin for every glyph, from 가: the font's own vertical position tells 으 from 우."""
    im = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(im).text((8, 8), "가", font=gfont, fill=1)
    x0, y0, _, _ = im.getbbox()
    # Stock glyphs start at row 4, column 1.
    return x0 - 1, y0 - 4


def draw(ch, gfont, org):
    im = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(im).text((8, 8), ch, font=gfont, fill=1)
    x0, y0, x1, y1 = im.getbbox()
    ox, oy = org
    if x0 < ox or y0 < oy or x1 > ox + 13 or y1 > oy + 16:
        raise SystemExit("%s leaves the 12x12 box" % ch)
    return [[bool(im.getpixel((ox + x, oy + y))) for x in range(16)] for y in range(16)]


def pack(rows):
    out = bytearray()
    for row in rows:
        for half in range(2):
            out.append(sum(0x80 >> x for x in range(8) if row[half * 8 + x]))
    return bytes(out)


def new_offset(code):
    i = code - FIRST
    return ((BANK0 & 0x7F) + i // PER_BANK) * 0x8000 + (i % PER_BANK) * 32


def main(romp, out):
    rom = bytearray(open(romp, "rb").read())
    if len(rom) != OLD_SIZE or rom[SIZE_BYTE] != 0x0B:
        raise SystemExit("expected the 2 MB v1.3 build")
    gfont = ImageFont.truetype(GLYPH_FONT, 12)
    org = origin(gfont)
    table = load_table()
    have = {}
    for c, ch in sorted(table.items()):
        if is_glyph(c) and len(ch) == 1 and "가" <= ch <= "힣":
            have.setdefault(ch, c)

    rom += b"\xFF" * (NEW_SIZE - OLD_SIZE)
    rom[SIZE_BYTE] = 0x0C
    new = [ch for ch in JAMO + SYL + ["띄"] if ch not in have]
    new = list(dict.fromkeys(new))
    codes, seen = {}, {}
    for i, ch in enumerate(new):
        code = FIRST + i
        data = pack(draw(ch, gfont, org))
        if data in seen:
            # Galmuri11 itself draws a few pairs alike; only a difference lost to the box is an error.
            a = Image.new("1", (32, 32), 0)
            b = Image.new("1", (32, 32), 0)
            ImageDraw.Draw(a).text((8, 8), seen[data], font=gfont, fill=1)
            ImageDraw.Draw(b).text((8, 8), ch, font=gfont, fill=1)
            if a.tobytes() != b.tobytes():
                raise SystemExit("%s and %s look the same" % (seen[data], ch))
        seen.setdefault(data, ch)
        o = new_offset(code)
        rom[o:o + 32] = data
        codes[ch] = code
    if any(codes.get(j) != FIRST + i for i, j in enumerate(JAMO)):
        raise SystemExit("the jamo must be the first new codes: the name entry computes their index from the code")
    every = {**have, **codes}
    last = max(codes.values())
    if new_offset(last) // 0x8000 + 0x80 >= CODE_BANK:
        raise SystemExit("the glyphs run into the code bank")

    def words(at, n):
        return [struct.unpack_from("<H", rom, at + 2 * i)[0] for i in range(n)]

    old = words(GRID_AT, 6 * ROW_WORDS)
    if old[DONE_AT - 1] != BLANK or old[6 * ROW_WORDS - 1] != 0 or old[ROW_WORDS - 1] != NEWLINE:
        raise SystemExit("name entry grid not found")
    grid, cells = [], []
    for row in range(6):
        for g in range(3):
            grid.append(BLANK)
            if row == 5 and g == 2:
                grid += old[DONE_AT:DONE_AT + 4]
                break
            for ch in GRID[row * 3 + g]:
                grid.append(BLANK if ch == " " else every[ch])
                cells.append(0xFF if ch == " " else JAMO.index(ch))
        grid.append(NEWLINE if row < 5 else 0)
    if len(cells) != 0x55:
        raise SystemExit("the grid must have 85 cells before 입력완료")

    help_old = words(HELP_AT, 20)
    if help_old[0] != 0x2B7 or help_old[-1] != 0:
        raise SystemExit("name entry help not found")
    help_words = []
    for icons, label in HELP:
        help_words += list(icons) + [every[ch] if ch in every else
                                                  next(k for k, v in table.items() if v == ch) for ch in label]
        help_words.append(NEWLINE)
    help_words[-1] = 0
    open(romp, "wb").write(rom)

    def dw(label, values):
        values = list(values)
        return [label + ":"] + ["    dw " + ",".join("$%04X" % v for v in values[i:i + 16]) for i in range(0, len(values), 16)]

    def db(label, values):
        values = list(values)
        return [label + ":"] + ["    db " + ",".join("$%02X" % v for v in values[i:i + 16]) for i in range(0, len(values), 16)]

    rest, move = [0], [0xFF]
    for j in JONG[1:]:
        pair = next((k for k, v in JONG_MIX.items() if v == j), None)
        rest.append(JONG.index(pair[0]) if pair else 0)
        move.append(CHO.index(pair[1] if pair else j))
    defs = ["; generated by tools/font16.py",
            "!k16_first = $%04X" % FIRST,
            "!k16_bank0 = $%02X" % BANK0,
            "!k16_jamo_first = $%04X" % every[JAMO[0]]]
    asm = ["; generated by tools/font16.py"]
    asm += dw("NeJamoCode", (every[j] for j in JAMO))
    asm += db("NeJCho", (CHO.index(j) if j in CHO else 0xFF for j in JAMO))
    asm += db("NeJJung", (JUNG.index(j) if j in JUNG else 0xFF for j in JAMO))
    asm += db("NeJJong", (JONG.index(j) if j in JONG[1:] else 0 for j in JAMO))
    asm += db("NeChoJ", (JAMO.index(j) for j in CHO))
    asm += db("NeJungJ", (JAMO.index(j) for j in JUNG))
    asm += db("NeJongRest", rest) + db("NeJongMove", move)
    asm += db("NeJungMix", [x for (a, b), r in JUNG_MIX.items() for x in (JUNG.index(a), JAMO.index(b), JUNG.index(r))] + [0xFF])
    asm += db("NeJongMix", [x for (a, b), r in JONG_MIX.items() for x in (JONG.index(a), JAMO.index(b), JONG.index(r))] + [0xFF])
    asm += db("NeCell", cells)
    asm += dw("NeGrid", grid)
    asm += dw("NeHelp", help_words)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "font16_defs.asm"), "w").write("\n".join(defs) + "\n")
    open(os.path.join(out, "font16_data.asm"), "w").write("\n".join(asm) + "\n")
    syl = ["; generated by tools/font16.py"] + dw("NeSylCode", (every[ch] for ch in SYL))
    open(os.path.join(out, "font16_syl.asm"), "w").write("\n".join(syl) + "\n")
    with open(os.path.join(out, "kr-v1.4.txt"), "w", encoding="utf-8") as f:
        for c, ch in sorted({**table, **{c: ch for ch, c in codes.items()}}.items()):
            f.write("%X=%s\n" % (c, ch))
    print("16px glyphs: %d syllables already in the font, %d new (codes %X-%X, banks $%02X-$%02X)"
          % (len(have), len(codes), FIRST, last, BANK0, new_offset(last) // 0x8000 + 0x80))


if __name__ == "__main__":
    main(*sys.argv[1:])
