"""Extend the v1.0 dialogue font with the characters the script needs, and write the table.

Every v1.0 code keeps its v1.0 bitmap and meaning (the name-entry screen uses the same
codes). Characters the script uses that v1.0 lacks get codes from NEW_FIRST on.
New characters come from tables/newglyphs.json (drawn to match the v1.0 style); a character
missing there falls back to Galmuri11 and is reported so it can be drawn.

usage: mkfont.py rom.sfc kr-v1.0.tbl script.txt out.tbl
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from font import glyph, groups, GROUPS, BANK1F
from dump import load_table
from assemble import normalize_text
from PIL import Image, ImageDraw, ImageFont

FONT = os.path.join(os.path.dirname(__file__), 'fonts', 'Galmuri11.ttf')
V10_LAST = 1613
NEW_GLYPHS = os.path.join(os.path.dirname(__file__), '..', 'tables', 'newglyphs.json')
NEW_FIRST = 1614
TABLE_END = 0x75CE          # $00:F5CE, the line-wrap exception list follows the group table
DATA_START, DATA_END = 0xF8000, 0x100000   # bank $1F; the decoder cannot cross into $20
HANGUL_W, HANGUL_H = 11, 11
NAME_TABLES = (0x12990, 0x13040)   # $02:A990-B03F, name-entry pages and menu strings
KINSOKU = (0x1297C, 0x12990)       # $02:A97C, marks that trigger waits / quote state
WIDTHS = 0xF7000            # $1E:F000, one width byte per code for asm/wordwrap.asm
WIDTHS_COUNT = 0x800

_font = ImageFont.truetype(FONT, 12)


def render(ch):
    im = Image.new('L', (24, 24), 0)
    ImageDraw.Draw(im).text((0, 0), ch, font=_font, fill=255)
    px = im.load()
    return [[1 if px[x, y] > 127 else 0 for x in range(24)] for y in range(24)]


def hangul_box():
    """Row window that holds the ink of every Hangul syllable, so all share one baseline."""
    top, bot = 99, -1
    for ch in '가각깨똠뷁쀍힣흫낢를'.strip():
        g = render(ch)
        rows = [y for y, r in enumerate(g) if any(r)]
        top, bot = min(top, rows[0]), max(bot, rows[-1])
    assert bot - top + 1 <= HANGUL_H, (top, bot)
    return bot - HANGUL_H + 1


def hangul_glyph(ch, top):
    g = render(ch)
    rows = g[top:top + HANGUL_H]
    assert not any(any(r[HANGUL_W:]) for r in g), ch
    return [r[:HANGUL_W] for r in rows]


def is_hangul(ch):
    return len(ch) == 1 and '가' <= ch <= '힣'


def pack(gl):
    """Bit stream for one group: rows of `w` bits, leftmost pixel = highest bit of the run."""
    bits, n = 0, 0
    for g in gl:
        for row in g:
            for x, p in enumerate(row):
                bits |= p << (n + len(row) - 1 - x)
            n += len(row)
    return bits.to_bytes((n + 7) // 8, 'little')


def main(romp, tblp, scriptp, outtbl):
    rom = bytearray(open(romp, 'rb').read())
    table = load_table(tblp)
    v10 = groups(rom)
    top = hangul_box()

    used, raw = set(), set()
    text = normalize_text(open(scriptp, encoding='utf-8').read())
    for m in re.finditer(r'\{[^}]*\}|#[0-9A-F]{6}\n|<(\d{4})>|\n|(.)', text, re.S):
        if m.group(2):
            used.add(m.group(2))
        elif m.group(1):
            raw.add(int(m.group(1)))
    have = set(table.values())
    new = sorted(ch for ch in used - have)
    bad = [ch for ch in new if not is_hangul(ch)]
    if bad:
        raise SystemExit('no glyph source for %r; add it to the v1.0 table or draw it' % bad)

    inv = {}
    for code, ch in table.items():
        inv.setdefault(ch, code)
    ref = raw | {inv[ch] for ch in used if ch in inv}
    for a, b in (NAME_TABLES, KINSOKU):
        ref |= {rom[o] | rom[o + 1] << 8 for o in range(a, b, 2)}
    o = TABLE_END
    while rom[o] | rom[o + 1] << 8 != 0xFFFF:
        ref.add(rom[o] | rom[o + 1] << 8)
        o += 2

    glyphs = {}
    for code in range(1, V10_LAST + 1):
        glyphs[code] = glyph(rom, code, v10)
        # A non-Hangul code nothing refers to becomes a blank glyph of its neighbour's size,
        # so it joins the neighbour's group and frees a slot in the 58-entry group table.
        if code > 1246 and code not in ref:
            prev = glyphs[code - 1]
            glyphs[code] = [[0] * len(prev[0]) for _ in prev]
    drawn = json.load(open(NEW_GLYPHS, encoding='utf-8')) if os.path.exists(NEW_GLYPHS) else {}
    # codes are assigned in size order so glyphs of one size form a single group
    size = lambda ch: (len(drawn[ch][0]), len(drawn[ch])) if ch in drawn else (HANGUL_W, HANGUL_H)
    new.sort(key=lambda ch: (size(ch), ch))
    fallback = []
    for i, ch in enumerate(new):
        if ch in drawn:
            glyphs[NEW_FIRST + i] = [[int(p) for p in row] for row in drawn[ch]]
        else:
            glyphs[NEW_FIRST + i] = hangul_glyph(ch, top)
            fallback.append(ch)
        table[NEW_FIRST + i] = ch
    if fallback:
        print('warning: drawn with Galmuri11, add to tables/newglyphs.json: ' + ''.join(fallback))

    runs = []
    for code in sorted(glyphs):
        g = glyphs[code]
        key = (len(g[0]), len(g))
        if runs and runs[-1][0] == key and runs[-1][2] == code - 1:
            runs[-1][2] = code
            runs[-1][3].append(g)
        else:
            runs.append([key, code, code, [g]])
    assert runs[0][1] == 1
    if GROUPS + 5 * len(runs) > TABLE_END:
        raise SystemExit('%d font groups do not fit the table' % len(runs))

    rom[DATA_START:DATA_END] = bytes(DATA_END - DATA_START)
    off = DATA_START
    for i, ((w, h), first, last, gl) in enumerate(runs):
        assert 1 <= w <= 16 and 1 <= h <= 15
        data = pack(gl)
        # the decoder reads 3 bytes per row, so keep 2 spare bytes after each group
        if off + len(data) + 2 > DATA_END:
            raise SystemExit('font data overflows bank $1F')
        rom[off:off + len(data)] = data
        e = GROUPS + 5 * i
        cnt = last - first + 1
        rom[e:e + 5] = bytes([cnt & 0xFF, (cnt >> 8) | (w << 4), off & 0xFF, ((off & 0x7FFF) | 0x8000) >> 8, h << 2])
        off += len(data) + 2
    rom[GROUPS + 5 * len(runs):TABLE_END] = bytes(TABLE_END - GROUPS - 5 * len(runs))
    widths = bytearray(WIDTHS_COUNT)
    for code, g in glyphs.items():
        widths[code] = len(g[0])
    # characters the engine lets hang past the margin must not push a word to the next line
    o = TABLE_END
    while rom[o] | rom[o + 1] << 8 != 0xFFFF:
        widths[rom[o] | rom[o + 1] << 8] = 0
        o += 2
    rom[WIDTHS:WIDTHS + WIDTHS_COUNT] = widths

    open(romp, 'wb').write(rom)
    with open(outtbl, 'w', encoding='utf-8') as f:
        for code in sorted(table):
            f.write('%d\t%s\n' % (code, table[code]))
    print('font: %d groups, %d bytes, %d new chars %s' % (len(runs), off - DATA_START, len(new), ''.join(new)))


if __name__ == '__main__':
    main(*sys.argv[1:5])
