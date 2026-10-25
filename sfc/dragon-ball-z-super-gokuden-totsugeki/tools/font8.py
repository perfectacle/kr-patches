"""v1.3: the 8 px Hangul of names is redrawn and extended to all 11,172 syllables.

usage: font8.py rom.smc out_dir

Names, the name entry grid and the ending password use the 8x16 glyphs of the kana slots
(codes 0x100-0x4FF, sheet $83:DE00). v1.0 drew 160 Hangul syllables there with 1 px strokes
that run together; they are redrawn with Galmuri11 Condensed (7 px wide, 11 px high) and the
usual shadow (right, down, down-right), so every code keeps its meaning.

The sheet has room for 512 glyphs, so the other syllables and the 51 compatibility jamo get
new codes from FIRST on. Every syllable is there because the name entry composes jamo freely:
뷁 is typed through 뷀, and neither is in KS X 1001. The ROM grows from 2 MB to 4 MB and their
glyphs fill banks $C0- in the layout of the kana sheet (16 codes per sheet row, glyph rows on even sheet rows,
bottom half +0x100). asm/v13.asm makes the renderer treat these codes like kana-slot codes.

Writes out_dir/font8_defs.asm (constants), out_dir/font8_data.asm (the jamo tables of the
name entry), out_dir/font8_syl.asm (syllable -> code) and out_dir/kr-v1.3.txt (the code table plus the new codes).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import font1  # noqa: E402
import kr1  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
FONT = os.path.join(ROOT, "tools", "fonts", "Galmuri11-Condensed.ttf")
OLD_SIZE = 0x200000
NEW_SIZE = 0x400000
FIRST = 0x1000                  # first new code
BANK0 = 0xC0                    # first bank of the new sheet
CODES_PER_BANK = 0x800          # 0x8000 bytes / 16 bytes per code
SIZE_BYTE = 0x7FD7              # header ROM size: 2^n KB
JAMO = [chr(c) for c in range(0x3131, 0x3164)]
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
JUNG_MIX = {("ㅗ", "ㅏ"): "ㅘ", ("ㅗ", "ㅐ"): "ㅙ", ("ㅗ", "ㅣ"): "ㅚ", ("ㅜ", "ㅓ"): "ㅝ",
            ("ㅜ", "ㅔ"): "ㅞ", ("ㅜ", "ㅣ"): "ㅟ", ("ㅡ", "ㅣ"): "ㅢ"}
JONG_MIX = {("ㄱ", "ㅅ"): "ㄳ", ("ㄴ", "ㅈ"): "ㄵ", ("ㄴ", "ㅎ"): "ㄶ", ("ㄹ", "ㄱ"): "ㄺ",
            ("ㄹ", "ㅁ"): "ㄻ", ("ㄹ", "ㅂ"): "ㄼ", ("ㄹ", "ㅅ"): "ㄽ", ("ㄹ", "ㅌ"): "ㄾ",
            ("ㄹ", "ㅍ"): "ㄿ", ("ㄹ", "ㅎ"): "ㅀ", ("ㅂ", "ㅅ"): "ㅄ"}
# Name entry grid: two rows of four groups of five cells. ⋮ is the game's space key, " " an empty cell.
GRID = ["ㅂㅈㄷㄱㅅ", "ㅁㄴㅇㄹㅎ", "ㅋㅌㅊㅍ ", "ㅃㅉㄸㄲㅆ",
        "ㅛㅕㅑㅐㅔ", "ㅗㅓㅏㅣ ", "ㅠㅜㅡ  ", "ㅒㅖ  ⋮"]
GRID_AT = 0x7005                # $80:F005, rows of 23 cells and a newline
GRID_ROWS = 10
BLANK, SPACE_KEY, NEWLINE = 0x02C5, 0x02C8, 0x000A
SYL = [chr(c) for c in range(0xAC00, 0xD7A4)]
CODE_BANK = 0xE0                # asm/v13.asm: code, then the syllable table in the next bank


def is_hangul(ch):
    return len(ch) == 1 and ("가" <= ch <= "힣" or ch in JAMO)


def new_code(i):
    """i-th new glyph -> its code (only even sheet rows start a glyph)"""
    return FIRST + (i // 16) * 32 + i % 16


def new_offset(code):
    i = code - FIRST
    return (BANK0 & 0x7F) * 0x8000 + (i // CODES_PER_BANK) * 0x8000 + (i % CODES_PER_BANK) * 16


def draw(ch, font):
    """plane rows (p0, p1), 16 high and 8 wide: glyph in columns 0-6, rows 3-13, plus shadow"""
    # One origin for every glyph: the font's own vertical position tells 돈 from 든.
    im = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(im).text((8, 8), ch, font=font, fill=1)
    x0, y0, x1, y1 = im.getbbox()
    if x0 < 8 or x1 > 15 or y0 < 9 or y1 > 20:
        raise SystemExit("%s leaves the 7x11 box" % ch)
    sk = [[False] * 8 for _ in range(16)]
    for y in range(11):
        for x in range(7):
            sk[3 + y][x] = bool(im.getpixel((8 + x, 9 + y)))
    p0 = [[False] * 8 for _ in range(16)]
    p1 = [[False] * 8 for _ in range(16)]
    for y in range(16):
        for x in range(8):
            if sk[y][x]:
                p0[y][x] = True
            elif (x and sk[y][x - 1]) or (y and sk[y - 1][x]) or (x and y and sk[y - 1][x - 1]):
                p0[y][x] = p1[y][x] = True
    return p0, p1


def picture(ch, font):
    im = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(im).text((8, 8), ch, font=font, fill=1)
    return im.tobytes()


def put(rom, off, planes):
    for y in range(16):
        base = off + (0x100 if y >= 8 else 0) + (y % 8) * 2
        for p, rows in enumerate(planes):
            rom[base + p] = sum(0x80 >> x for x in range(8) if rows[y][x])


def main(romp, out):
    rom = bytearray(open(romp, "rb").read())
    if len(rom) != OLD_SIZE or rom[SIZE_BYTE] != 0x0B:
        raise SystemExit("expected the 2 MB v1.2 build")
    font = ImageFont.truetype(FONT, 12)
    table = kr1.table()
    have = {ch: c for c, ch in sorted(table.items()) if 0x100 <= c < 0x500 and font1.valid(c) and is_hangul(ch)}

    shapes = {}
    for ch, c in have.items():
        planes = draw(ch, font)
        put(rom, font1.info(c)[1], planes)
        shapes[ch] = planes

    rom += b"\xFF" * (NEW_SIZE - OLD_SIZE)
    rom[SIZE_BYTE] = 0x0C
    new = [ch for ch in JAMO + SYL if ch not in have]
    codes = {}
    for i, ch in enumerate(new):
        code = new_code(i)
        planes = draw(ch, font)
        put(rom, new_offset(code), planes)
        codes[ch] = code
        shapes[ch] = planes
    if any(codes.get(j) != new_code(i) for i, j in enumerate(JAMO)):
        raise SystemExit("the jamo must be the first new codes: the name entry computes their index from the code")
    seen = {}
    for ch, planes in shapes.items():
        key = str([[a and not b for a, b in zip(r0, r1)] for r0, r1 in zip(*planes)])  # glyph pixels, shadow left out
        if key in seen:
            # Galmuri11 Condensed itself draws some pairs alike (쌔 썌, 째 쨰); only a
            # difference lost to the 7x11 box is an error.
            if picture(seen[key], font) != picture(ch, font):
                raise SystemExit("%s and %s look the same" % (seen[key], ch))
            continue
        seen[key] = ch
    grid = []
    for row in range(GRID_ROWS):
        cells = []
        for g in range(4):
            group = GRID[row * 4 + g] if row < 2 else "     "
            for ch in group:
                cells.append(0x8000 | (BLANK if ch == " " else SPACE_KEY if ch == "⋮" else codes[ch]))
            if g < 3:
                cells.append(0x8000 | BLANK)
        grid += cells + [NEWLINE]
    old = rom[GRID_AT + 23 * 2:GRID_AT + 24 * 2]
    if old != NEWLINE.to_bytes(2, "little"):
        raise SystemExit("name entry grid not found")
    rom[GRID_AT:GRID_AT + len(grid) * 2] = b"".join(w.to_bytes(2, "little") for w in grid)
    open(romp, "wb").write(rom)

    every = {**have, **codes}
    last = max(codes.values())
    if new_offset(last) // 0x8000 + 0x80 >= CODE_BANK:
        raise SystemExit("the glyphs run into the code bank")
    defs = ["; generated by tools/font8.py",
            "!f8_first = $%04X" % FIRST,
            "!f8_end = $%04X" % (last + 1),
            "!f8_bank0 = $%02X" % BANK0,
            "!f8_jamo_first = $%04X" % every[JAMO[0]]]

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
    asm = ["; generated by tools/font8.py"]
    asm += dw("NeJamoCode", (every[j] for j in JAMO))
    asm += db("NeJCho", (CHO.index(j) if j in CHO else 0xFF for j in JAMO))
    asm += db("NeJJung", (JUNG.index(j) if j in JUNG else 0xFF for j in JAMO))
    asm += db("NeJJong", (JONG.index(j) if j in JONG[1:] else 0 for j in JAMO))
    asm += db("NeChoJ", (JAMO.index(j) for j in CHO))
    asm += db("NeJungJ", (JAMO.index(j) for j in JUNG))
    asm += db("NeJongRest", rest) + db("NeJongMove", move)
    asm += db("NeJungMix", [x for (a, b), r in JUNG_MIX.items() for x in (JUNG.index(a), JAMO.index(b), JUNG.index(r))] + [0xFF])
    asm += db("NeJongMix", [x for (a, b), r in JONG_MIX.items() for x in (JONG.index(a), JAMO.index(b), JONG.index(r))] + [0xFF])
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "font8_defs.asm"), "w").write("\n".join(defs) + "\n")
    open(os.path.join(out, "font8_data.asm"), "w").write("\n".join(asm) + "\n")
    syl = ["; generated by tools/font8.py"] + dw("NeSylCode", (every[ch] for ch in SYL))
    open(os.path.join(out, "font8_syl.asm"), "w").write("\n".join(syl) + "\n")
    with open(os.path.join(out, "kr-v1.3.txt"), "w", encoding="utf-8") as f:
        for c, ch in sorted({**table, **{c: ch for ch, c in codes.items()}}.items()):
            f.write("%X=%s\n" % (c, ch))
    print("8px glyphs: %d redrawn, %d new (codes %X-%X, banks $%02X-$%02X)"
          % (len(have), len(codes), FIRST, last, BANK0, new_offset(last) // 0x8000 + 0x80))


if __name__ == "__main__":
    main(*sys.argv[1:])
