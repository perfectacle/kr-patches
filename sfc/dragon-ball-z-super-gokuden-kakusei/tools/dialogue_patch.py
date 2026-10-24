"""Replace dialogue lines in the ROM.

usage: dialogue_patch.py jp.smc in.smc fixes.tsv out.smc [out-table.txt]

fixes.tsv: `id<TAB>text`, '/' = line break. Text is encoded with tables/kr.txt.
A line that fits in its old slot is rewritten in place; otherwise it goes to
free space in the same bank (its 0xFF tail or slots vacated by
other moved lines) and its pointer is updated (pointers are
16-bit, bank-relative, so a line can never leave its bank).

Characters missing from the font are drawn with Galmuri11 into glyph slots
that no dialogue line and no other translated text uses.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from dialogue import BANKS, LAST_BANK, off, words  # noqa: E402
from extract import load  # noqa: E402
from font import glyph_offset  # noqa: E402
from usedsheet import N, odd  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
GLYPH_FONT = os.path.join(os.path.dirname(__file__), "fonts", "Galmuri11.ttf")
DIALOGUE = range(0xC0000, 0x100000)
FONT_AREA = range(0x1B0000, 0x1C0000)


def canon(c):
    """0x900+ codes alias the 0x2E0+ part of the first sheet."""
    return c - 0x620 if c >= 0x900 else c


def table_slot(i):
    for lo, hi, bank, table in BANKS:
        if lo <= i < hi:
            return bank, off(bank, table) + (i - lo) * 2
    lo, bank, table = LAST_BANK
    return bank, off(bank, table) + (i - lo) * 2


def pointer(rom, i):
    bank, t = table_slot(i)
    return bank, t, rom[t] | rom[t + 1] << 8


def title_graphics(rom):
    """Compressed title-screen assets; their bytes are pixels, not glyph codes."""
    from title import CHR, MAP
    spans = []
    for a in (CHR, MAP):
        a.load(rom)
        spans.append(range(a.off, a.off + a.clen))
    return spans


def other_text_codes(jp, rom):
    """Every 16-bit value inside translated bytes outside dialogue, font and title graphics."""
    skip = title_graphics(rom)
    seen = set()
    i = 0
    while i < len(rom):
        if jp[i] != rom[i] and i not in DIALOGUE and i not in FONT_AREA and not any(i in r for r in skip):
            for k in range(max(0, i - 2), min(len(rom) - 1, i + 3)):
                seen.add(canon((rom[k] | rom[k + 1] << 8) & 0x7FFF))
        i += 1
    return seen


def tokenize(text, enc):
    """Prefer two-character glyphs such as '!!' and '!?'."""
    out, k = [], 0
    while k < len(text):
        if text[k:k + 2] in enc:
            out.append(text[k:k + 2])
            k += 2
        else:
            out.append(text[k])
            k += 1
    return out


def draw_glyph(ch):
    """16x16 1bpp rows for a Hangul syllable, roughly matching the game font."""
    font = ImageFont.truetype(GLYPH_FONT, 12)
    im = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(im).text((8, 8), ch, font=font, fill=1)
    x0, y0, _, _ = im.getbbox()
    # Stock glyphs start at row 4, column 1.
    return [[bool(im.getpixel((x0 + x - 1, y0 + y - 4))) if x >= 1 and y >= 4 else False
             for x in range(16)] for y in range(16)]


def write_glyph(rom, code, rows):
    o = glyph_offset(code)
    for y in range(16):
        base = o + (0x100 if y >= 8 else 0) + (y % 8) * 2
        for half in range(2):
            v = 0
            for x in range(8):
                if rows[y][half * 8 + x]:
                    v |= 0x80 >> x
            rom[base + half * 16] = v       # plane 0
            rom[base + half * 16 + 1] = v   # plane 1 mirrors it, like the stock font


def main():
    jp = open(sys.argv[1], "rb").read()
    rom = bytearray(open(sys.argv[2], "rb").read())
    fixes = []
    for line in open(sys.argv[3], encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        i, text = line.split("\t", 1)
        fixes.append((int(i, 16), text))

    table = load(os.path.join(ROOT, "tables", "kr.txt"))
    enc = {}
    for c in sorted(table):
        enc.setdefault(table[c], c)

    # Glyph slots still referenced after the patch.
    fixed_ids = {i for i, _ in fixes}
    keep = set()
    for i in range(N):
        if i in fixed_ids:
            continue
        bank, t, p = pointer(rom, i)
        if p >= 0x8000:
            keep.update(canon(w & 0x7FFF) for w in words(rom, off(bank, p)) if w != 0x0A)
    keep |= other_text_codes(jp, rom)
    needed = set()
    for _, text in fixes:
        for tok in tokenize(text, enc):
            if tok == "/":
                continue
            if tok in enc:
                keep.add(canon(enc[tok]))
            else:
                needed.add(tok)
    free = [c for c in sorted(table) if 0x100 <= c < 0x900 and canon(c) not in keep and table[c] != " "]
    if len(needed) > len(free):
        sys.exit(f"need {len(needed)} new glyphs, only {len(free)} free slots: {''.join(sorted(needed))}")
    for ch, c in zip(sorted(needed), free):
        write_glyph(rom, c, draw_glyph(ch))
        print(f"new glyph {ch} -> {c:03x} (was {table[c]})")
        for k in [k for k, v in enc.items() if v == c]:
            del enc[k]
        enc[ch] = c
        table[c] = ch
    if len(sys.argv) > 5:
        with open(sys.argv[5], "w", encoding="utf-8") as f:
            f.writelines(f"{c:03x}={table[c]}\n" for c in sorted(table))

    # Pass 1: rewrite lines that fit in place; vacate the slots of the rest.
    pending = []
    for i, text in fixes:
        data = bytearray()
        for tok in tokenize(text, enc):
            w = 0x0A if tok == "/" else enc[tok]
            data += bytes([w & 0xFF, w >> 8])
        data += b"\0\0"
        bank, t, p = pointer(rom, i)
        o = off(bank, p)
        old = 2 * len(words(rom, o)) + 2
        shared = any(j != i and pointer(rom, j)[::2] == (bank, p) for j in range(N))
        if len(data) <= old and not shared:
            rom[o:o + len(data)] = data
            rom[o + len(data):o + old] = b"\xff" * (old - len(data))
        else:
            if not shared:
                rom[o:o + old] = b"\xff" * old
            pending.append((bank, t, data))

    # Pass 2: place the rest, largest first, into merged 0xFF runs. Runs inside
    # the text area are only ever slots this script vacated or trimmed, since
    # live strings end in 0x0000 and never contain 0xFFFF.
    text_start = {}
    for j in range(N):
        bank, _, p = pointer(rom, j)
        if p >= 0x8000:
            text_start[bank] = min(text_start.get(bank, 1 << 30), off(bank, p))
    spans = {}
    for bank in {b for b, _, _ in pending}:
        # Only the string area: tables and other data sit below the first string.
        lo, hi = text_start[bank], off(bank, 0xFFFF) + 1
        runs, k = [], lo
        while k < hi:
            if rom[k] != 0xFF:
                k += 1
                continue
            e = k
            while e < hi and rom[e] == 0xFF:
                e += 1
            # keep one byte of margin next to live data
            s0, s1 = k + 1, (e - 1 if e < hi else e)
            if s1 - s0 >= 2:
                runs.append([s0, s1])
            k = e
        spans[bank] = runs
    moved = 0
    for bank, t, data in sorted(pending, key=lambda x: -len(x[2])):
        for sp in spans[bank]:
            if sp[0] & 1:
                sp[0] += 1
            if sp[1] - sp[0] >= len(data):
                start = sp[0]
                sp[0] += len(data)
                break
        else:
            sys.exit(f"bank {bank:02x} is out of space for {len(data)} bytes")
        rom[start:start + len(data)] = data
        newp = 0x8000 | (start & 0x7FFF)
        rom[t], rom[t + 1] = newp & 0xFF, newp >> 8
        moved += 1
    open(sys.argv[4], "wb").write(rom)
    print(f"{len(fixes)} lines, {moved} relocated")
    for b, sp in sorted(spans.items()):
        print(f"  bank {b:02x}: {sum(max(0, e - s) for s, e in sp)} bytes free")


if __name__ == "__main__":
    main()
