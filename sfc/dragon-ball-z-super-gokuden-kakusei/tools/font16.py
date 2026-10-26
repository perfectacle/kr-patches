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
# Centred title menus ($84:A1D8 new game / option, $84:A1FA with continue, $84:A22E start / password,
# $81:D654 the chapter to continue from).
# Leading spaces can only move a line by a whole 12 px glyph, which left the lines up to 6 px off
# centre and a 12 px gap inside 새 게임. Each line is typeset from the stock glyphs instead (a 4 px
# word space), centred on the window (x 128 on screen, the middle of its inside 66-189 and of the
# cursor box that asm/v14.asm moves to 72-183) and cut into new 12 px glyphs; a line keeps its
# number of codes.
MENUS = [(0x84A1D8, ["새 게임", "옵션"]),
         (0x84A1FA, ["이어하기", "새 게임", "옵션"]),
         (0x84A22E, ["게임 시작", "암호"]),
         (0x81D654, ["피콜로편부터", "베지터편부터", "프리더편부터"])]
MENU_CELLS, MENU_CENTRE, WORD_SPACE = 9, 56, 4
# Status screen labels where the Japanese had one kanji and v1.1 squeezed two syllables into one
# 12 px glyph (codes 0x273 전환, 0x274 취소, 0x275 험치, 0x276 다음). The code that copies them takes
# a fixed number of codes into a window of fixed width ($020E), so each field is typeset into what
# is visible: its codes x 12 px plus the 4 px a glyph may reach past its cell, cut at the window
# edge. Button icons stay stock and the labels use Galmuri11 Condensed (7 px): the stock syllables
# do not fit even one pixel apart. Headers are centred; the command item starts where the others do.
# (bank $84 address of the field, its old codes, the new text, visible width, centred?[, letter gap,
# word space]). The command item is spaced out to end where 기술설정 and 기술습득 end (x 46).
ICONS = {"✚": 0x2B7, "Ⓐ": 0x2B3, "Ⓑ": 0x2B4, "Ⓧ": 0x2B5, "Ⓨ": 0x2B6}
FIELDS = [(0x86DC, [0x2B7, 0x2B3, 0xA14, 0x837, 0x2B5, 0x273, 0x2B4, 0x274], "✚Ⓐ선택Ⓧ전환Ⓑ취소", 100, True),
          (0x87E2, [0x2B5, 0x5F1, 0x724, 0x2B3, 0x2B4, 0x274], "Ⓧ전환ⒶⒷ취소", 76, True),
          (0x886A, [0x2B5, 0x276, 0x2B6, 0x7E2, 0x932, 0x2B3, 0x2B4, 0x274], "Ⓧ다음Ⓨ뒤로Ⓑ취소", 96, True),
          (0x888C, [0x272, 0x2B3, 0x2B4, 0x274], "ⒶⒷ취소", 48, True),
          (0x8904, [0x2B7, 0x2B3, 0xA14, 0x837, 0x2B5, 0x5F1, 0x724, 0x2B4, 0x274], "✚Ⓐ선택Ⓧ전환Ⓑ취소", 112, True),
          (0x896C, [0x2B5, 0x276, 0x2B6, 0x7E2, 0x932, 0x2B3, 0x2B4, 0x826, 0xA25], "Ⓧ다음Ⓨ뒤로ⒶⒷ취소", 112, True),
          (0x878E, [0x166, 0x501, 0x135, 0x275], "기술 경험치", 48, False, 2, 5)]
CONDENSED_FONT = os.path.join(ROOT, "tools", "fonts", "Galmuri11-Condensed.ttf")
# The button icons have colours (plane 1 differs from plane 0), so the field glyphs keep both planes:
# 64 bytes each, the four tiles in sheet order, from TWO_FIRST in bank TWO_BANK.
TWO_FIRST, TWO_BANK = 0x3C00, 0xCB
# Each screen gives an icon its colour by ORing a palette into four entries of the BG3 tilemap
# buffer at $7E:5000 (two tiles, two rows): LDA $7Exxxx / ORA #$pp00 / STA $7Exxxx, 11 bytes each.
# Moving an icon moves those entries, so an icon must lie within two tiles (its left column mod 8
# at most 5). (field, screen x of its first code, bank $81 setter blocks)
# (field, screen x of its first code, window width $020E x 8, inner left edge of its panel,
# bank $81 setter blocks). Two icons never share a tile, or the tile gets both palettes.
SETTERS = {0x86DC: (136, 104, 130, [0x95F3]), 0x87E2: (160, 80, 154, [0x9DDB]),
           0x886A: (136, 96, 122, [0xC128]), 0x888C: (192, 48, 186, [0xCCCF]),
           0x8904: (128, 112, 122, [0xA894, 0xB84C]), 0x896C: (128, 112, 122, [0xC5D7, 0xC8BD])}
# Every guide ends on x 230, where the lines below it end (values, separators, lists), and starts
# as far in from its panel's left edge as that end is from the panel's right edge (x 243).
GUIDE_RIGHT, PANEL_RIGHT = 230, 243
HEADER_ROWS = range(0x50C0, 0x5140)


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


def typeset(rom, label, have, cells):
    """label -> rows of the line's pixels (cells x 12 wide), ink centred on MENU_CENTRE"""
    width = cells * 12 + 32
    strip = [[False] * width for _ in range(16)]
    pen = 0
    for ch in label:
        if ch == " ":
            pen += WORD_SPACE
            continue
        g = font.glyph(rom, have[ch])
        for y in range(16):
            for x in range(16):
                if g[y][x]:
                    strip[y][pen + x] = True
        pen += 12
    ink = [x for x in range(width) if any(strip[y][x] for y in range(16))]
    shift = MENU_CENTRE - (ink[0] + ink[-1] + 1) // 2
    if ink[0] + shift < 0 or ink[-1] + shift >= cells * 12:
        raise SystemExit("%s does not fit its line" % label)
    return [[strip[y][x - shift] if 0 <= x - shift < width else False for x in range(cells * 12)] for y in range(16)]


def condensed(ch, cfont):
    """16x16 rows: a Galmuri11 Condensed syllable, 7 px wide, rows 4-14 like the stock glyphs"""
    im = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(im).text((8, 8), ch, font=cfont, fill=1)
    ref = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(ref).text((8, 8), "가", font=cfont, fill=1)
    x0, y0, _, _ = ref.getbbox()
    rows = [[bool(im.getpixel((x0 + x, y0 - 4 + y))) for x in range(16)] for y in range(16)]
    if any(rows[y][x] for y in range(16) for x in range(7, 16)):
        raise SystemExit("%s is wider than 7 px" % ch)
    return rows


def glyph2(rom, code):
    """16 rows of 16 colour indexes (plane 0 + 2 x plane 1) of a stock glyph"""
    o = font.glyph_offset(code)
    rows = []
    for y in range(16):
        base = o + (0x100 if y >= 8 else 0) + (y % 8) * 2
        rows.append([(rom[base + (x // 8) * 16] >> (7 - x % 8) & 1) | (rom[base + (x // 8) * 16 + 1] >> (7 - x % 8) & 1) << 1
                     for x in range(16)])
    return rows


def pack2(rows):
    """16 rows of colour indexes -> 64 bytes: top left, top right, bottom left, bottom right tiles"""
    out = bytearray()
    for top in (0, 8):
        for half in (0, 8):
            for y in range(top, top + 8):
                for plane in (0, 1):
                    out.append(sum(0x80 >> x for x in range(8) if rows[y][half + x] >> plane & 1))
    return bytes(out)


def place_guide(text, end, gap, icon_gap):
    """left x of each item, laid from the right so it ends on `end` (field x from a tile boundary):
    icons 11 px with their left column mod 8 at most 5 and no tile shared with another icon,
    labels 7 px. Room the tiles force goes in front of an icon, not between two icons."""
    xs, pen, nxt, next_tile = [], end + 1, None, 1 << 16
    for ch in reversed(text):
        icon = ch in ICONS
        if nxt is not None:
            pen -= icon_gap if icon != (nxt == "icon") else gap if not icon else 1
        x = pen - (11 if icon else 7)
        if icon:
            while x % 8 > 5 or x // 8 + 1 >= next_tile:
                x -= 1
            next_tile = x // 8
        xs.append(x)
        pen = x
        nxt = "icon" if icon else "text"
    return xs[::-1], xs[-1]


def lay_guide(rom, text, cfont, origin, window, panel_left, limit):
    """button guide -> (rows of colour indexes `limit` px wide, left x of each icon), from the
    spacing and start nearest the targets (see GUIDE_RIGHT), even spacing breaking ties"""
    right = GUIDE_RIGHT - origin
    left = panel_left + (PANEL_RIGHT - GUIDE_RIGHT) - origin
    best = None
    for gap in (1, 2, 3):
        for icon_gap in range(gap, gap + 4):
            for end in range(min(limit, window) - 1, 0, -1):
                xs, start = place_guide(text, end, gap, icon_gap)
                if start < 0:
                    break
                uneven = 0
                for (a, xa), (b, xb) in zip(zip(text, xs), zip(text[1:], xs[1:])):
                    want = 1 if a in ICONS and b in ICONS else icon_gap if (a in ICONS) != (b in ICONS) else gap
                    uneven += abs(xb - xa - (11 if a in ICONS else 7) - want)
                score = (abs(start - left) + abs(end - right) + 2 * uneven, icon_gap - gap, -gap)
                if best is None or score < best[0]:
                    best = (score, xs)
    if best is None:
        raise SystemExit("%s does not fit %d px" % (text, window))
    xs = best[1]
    strip = [[0] * limit for _ in range(16)]
    for ch, x in zip(text, xs):
        g = glyph2(rom, ICONS[ch]) if ch in ICONS else [[3 if p else 0 for p in row] for row in condensed(ch, cfont)]
        for y in range(16):
            for gx in range(16):
                if g[y][gx] and x + gx < limit:
                    strip[y][x + gx] |= g[y][gx]
    return strip, [x for ch, x in zip(text, xs) if ch in ICONS]


def move_icon_palettes(rom, at, old, text, icons):
    """moves each icon's palette entries with the icon (see SETTERS); an icon the new text leaves out
    loses them (the instructions become NOPs)"""
    origin, _, _, blocks = SETTERS[at]
    names = {v: k for k, v in ICONS.items()}
    old_icons = [(names[c], (origin + i * 12) // 8) for i, c in enumerate(old) if c in names]
    new_icons = [ch for ch in text if ch in ICONS]
    old_cols = [c for _, c in old_icons]
    new_cols = []
    for k, (ch, _) in enumerate(old_icons):
        nth = sum(1 for c, _ in old_icons[:k] if c == ch)
        hits = [x for c, x in zip(new_icons, icons) if c == ch]
        new_cols.append((origin + hits[nth]) // 8 if nth < len(hits) else None)
    for block in blocks:
        o = (0x81 & 0x7F) * 0x8000 + (block & 0x7FFF)
        while rom[o] == 0xAF and rom[o + 3] == 0x7E and rom[o + 4] == 0x09 and rom[o + 7] == 0x8F:
            addr = rom[o + 1] | rom[o + 2] << 8
            if addr in HEADER_ROWS:
                col = (addr - 0x5000) % 0x40 // 2
                k = next((k for k, c in enumerate(old_cols) if c == col), None)
                if k is None:
                    k = next((k for k, c in enumerate(old_cols) if c == col - 1), None)
                if k is None:
                    raise SystemExit("palette entry $7E:%04X of field $84:%04X has no icon" % (addr, at))
                if new_cols[k] is None:
                    rom[o:o + 11] = b"\xEA" * 11
                    o += 11
                    continue
                new = addr + 2 * (new_cols[k] - old_cols[k])
                for off in (1, 8):
                    rom[o + off], rom[o + off + 1] = new & 0xFF, new >> 8
            o += 11


def lay_field(rom, text, cfont, width, centred, gap=1, space=3):
    """text -> rows of colour indexes `width` px wide: icons advance 12, syllables 7 + gap, a space
    `space`; the syllables take colour 3 like the stock font"""
    strip = [[0] * (width + 32) for _ in range(16)]
    pen, prev = 0, None
    for ch in text:
        if ch == " ":
            pen += space - gap
            continue
        if ch in ICONS:
            g, w = glyph2(rom, ICONS[ch]), 12
        else:
            g, w = [[3 if p else 0 for p in row] for row in condensed(ch, cfont)], 7 + gap
        for y in range(16):
            for x in range(16):
                strip[y][pen + x] |= g[y][x]
        pen += w
        prev = "icon" if ch in ICONS else "text"
    ink = [x for x in range(width + 32) if any(strip[y][x] for y in range(16))]
    shift = (width - (ink[-1] + 1 - ink[0])) // 2 - ink[0] if centred else 1 - ink[0]
    if ink[0] + shift < 0 or ink[-1] + shift >= width:
        raise SystemExit("%s does not fit its %d px" % (text, width))
    return [[strip[y][x - shift] if 0 <= x - shift < width + 32 else 0 for x in range(width)] for y in range(16)]


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

    next_code = FIRST + len(new)
    menu_glyphs = {}
    for at, labels in MENUS:
        o = (at >> 16 & 0x7F) * 0x8000 + (at & 0x7FFF)
        lines, line, k = [], [], o
        while True:
            w = struct.unpack_from("<H", rom, k)[0]
            if w in (0, NEWLINE):
                lines.append((k - 2 * len(line), line))
                line = []
                if w == 0:
                    break
            else:
                line.append(w)
            k += 2
        if len(lines) != len(labels):
            raise SystemExit("menu at $%06X not found" % at)
        for (start, old), label in zip(lines, labels):
            if "".join(table.get(c, "") for c in old if c != BLANK) != label.replace(" ", ""):
                raise SystemExit("menu at $%06X does not say %s" % (at, label))
            pixels = typeset(rom, label, have, MENU_CELLS)
            words = []
            for c in range(len(old)):
                rows = [[pixels[y][c * 12 + x] if c * 12 + x < MENU_CELLS * 12 and x < 12 else False
                         for x in range(16)] for y in range(16)]
                if not any(any(r) for r in rows):
                    words.append(BLANK)
                    continue
                data = pack(rows)
                if data not in menu_glyphs:
                    menu_glyphs[data] = next_code
                    o2 = new_offset(next_code)
                    rom[o2:o2 + 32] = data
                    next_code += 1
                words.append(menu_glyphs[data])
            if any(pixels[y][x] for y in range(16) for x in range(len(old) * 12, MENU_CELLS * 12)):
                raise SystemExit("%s runs past the %d codes of its line" % (label, len(old)))
            rom[start:start + 2 * len(old)] = b"".join(w.to_bytes(2, "little") for w in words)
    cfont = ImageFont.truetype(CONDENSED_FONT, 12)
    two_glyphs = {}
    for at, old, text, width, centred, *spacing in FIELDS:
        start = (0x84 & 0x7F) * 0x8000 + (at & 0x7FFF)
        if [struct.unpack_from("<H", rom, start + 2 * i)[0] for i in range(len(old))] != old:
            raise SystemExit("field at $84:%04X not found" % at)
        if width > len(old) * 12 + 4:
            raise SystemExit("field at $84:%04X: %d px is past its last glyph" % (at, width))
        if at in SETTERS:
            field_x, window, panel_left, _ = SETTERS[at]
            pixels, icons = lay_guide(rom, text, cfont, field_x, window, panel_left, width)
            move_icon_palettes(rom, at, old, text, icons)
        else:
            pixels = lay_field(rom, text, cfont, width, centred, *spacing)
        words = []
        for c in range(len(old)):
            rows = [[pixels[y][c * 12 + x] if c * 12 + x < width and (x < 12 or c == len(old) - 1) else 0
                     for x in range(16)] for y in range(16)]
            if not any(any(r) for r in rows):
                words.append(BLANK)
                continue
            data = pack2(rows)
            if data not in two_glyphs:
                code = TWO_FIRST + len(two_glyphs)
                o2 = (TWO_BANK & 0x7F) * 0x8000 + (code - TWO_FIRST) * 64
                rom[o2:o2 + 64] = data
                two_glyphs[data] = code
            words.append(two_glyphs[data])
        rom[start:start + 2 * len(old)] = b"".join(w.to_bytes(2, "little") for w in words)
    last = next_code - 1
    if new_offset(last) // 0x8000 + 0x80 >= TWO_BANK or last >= TWO_FIRST:
        raise SystemExit("the glyphs run into the two-plane glyphs")

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
            "!k16_jamo_first = $%04X" % every[JAMO[0]],
            "!k16_two_first = $%04X" % TWO_FIRST,
            "!k16_two_bank = $%02X" % TWO_BANK]
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
