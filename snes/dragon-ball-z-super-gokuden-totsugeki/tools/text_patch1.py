"""Rewrite every dialogue line and repack each bank's string area.

usage: text_patch1.py jp.smc in.smc out.smc out-table.txt text.tsv [text.tsv ...]

ui-*.tsv files hold in-place menu fixes (offset, current text, new text[, max codes]);
without a maximum the new text may not be longer than the current one.
text.tsv: id<TAB>...; the "text" column (else the last) holds the line, '/' = newline.
Dialogue ids are hex; other pointer-table sets use "name:index" (see textsets.py).
Rows may be missing; those entries keep the text already in in.smc.

Each bank's strings are rewritten back to back from where the Japanese strings
started up to where they ended, identical strings shared. Pointers are 16-bit
and bank-relative, so text never leaves its bank.

Characters missing from the font are drawn (Galmuri11 + the font's drop shadow)
into 16x16 glyph slots that no text uses after the patch, then into the extra
blocks from fontext1.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402
import font1  # noqa: E402
import fontext1  # noqa: E402
import kr1  # noqa: E402
import textsets  # noqa: E402

GLYPH_FONT = os.path.join(os.path.dirname(__file__), "fonts", "Galmuri11.ttf")
FONT_AREAS = [range(0x18000, 0x20000), range(0x1F8000, 0x200000)]

# Drawn last, in this order, so earlier glyph codes stay put. 0x248 draws 떠, so 펴
# needs a 16 px glyph of its own; 플, 딩 and 렉 see kr1.WIDE_ONLY.
LATE_GLYPHS = "펴플딩렉"

# Battle shouts in bank 8E outside the dialogue table; their pointers are
# immediate operands (LDA #addr) in bank 81. Order matches Japanese $8E:C8F0-.
SHOUT_OPERANDS = [0xE300, 0xE380, 0xE43F, 0xE573, 0xE69B, 0xEB14, 0xEB80]


def bank_spans(jp):
    """bank -> (first byte, end) of the Japanese string area, shouts included."""
    spans = {}
    for i in range(D.count(jp)):
        t, bank = D.table_slot(jp, i)
        o = D.line_offset(jp, i)
        e = o + 2 * len(D.words(jp, o)) + 2
        s0, e0 = spans.get(bank, (o, e))
        spans[bank] = (min(s0, o), max(e0, e))
    s0, e0 = spans[0x8E]
    for op in SHOUT_OPERANDS:
        a = jp[op] | jp[op + 1] << 8
        o = D.off(0x8E, a)
        e0 = max(e0, o + 2 * len(D.words(jp, o)) + 2)
    spans[0x8E] = (s0, e0)
    return spans


def draw_glyph(ch):
    """plane rows (p0, p1) for a 16x16 glyph: 1 px strokes, shadow right and down."""
    font = ImageFont.truetype(GLYPH_FONT, 12)
    im = Image.new("1", (32, 32), 0)
    ImageDraw.Draw(im).text((8, 8), ch, font=font, fill=1)
    x0, y0, x1, y1 = im.getbbox()
    w, h = x1 - x0, y1 - y0
    # Stock Hangul strokes sit in columns 2-11, rows 3-13.
    ox, oy = 2 + max(0, (10 - w) // 2), 3 + max(0, (11 - h) // 2)
    sk = [[False] * 16 for _ in range(16)]
    for y in range(h):
        for x in range(w):
            if im.getpixel((x0 + x, y0 + y)) and 0 <= oy + y < 16 and 0 <= ox + x < 16:
                sk[oy + y][ox + x] = True
    p0 = [[False] * 16 for _ in range(16)]
    p1 = [[False] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if sk[y][x]:
                p0[y][x] = True
            elif (x > 0 and sk[y][x - 1]) or (y > 0 and sk[y - 1][x]) or (x > 0 and y > 0 and sk[y - 1][x - 1]):
                p0[y][x] = p1[y][x] = True
    return p0, p1


def write_glyph(rom, code, planes):
    lo, o, w = font1.info(code)
    for y in range(16):
        base = o + (0x100 if y >= 8 else 0) + (y % 8) * 2
        for half in range(w):
            for p, rows in enumerate(planes):
                v = 0
                for x in range(8):
                    if rows[y][half * 8 + x]:
                        v |= 0x80 >> x
                rom[base + half * 16 + p] = v


def other_text_codes(jp, rom, spans):
    """16-bit values in bytes v1.0 changed outside dialogue, fonts and title graphics."""
    from title import CHR, MAP
    skip = [range(s, e) for s, e in spans.values()] + FONT_AREAS
    for a in (CHR, MAP):
        a.load(rom)
        skip.append(range(a.off, a.off + a.clen))
    seen = set()
    for i in range(len(rom) - 1):
        if jp[i] != rom[i] and not any(i in r for r in skip):
            for k in range(max(0, i - 2), min(len(rom) - 1, i + 3)):
                seen.add((rom[k] | rom[k + 1] << 8) & 0x7FFF)
    return seen


def set_span(jp, name):
    ss = textsets.strings(jp, name)
    return min(o for _, _, o, _ in ss), max(o + 2 * len(w) + 2 for _, _, o, w in ss)


def repack(rom, items, regions, label):
    """items: (pointer slot, codes). Writes strings back to back into the
    regions [(start, end), ...] in order; returns what is left of each region."""
    regions = [list(r) for r in regions]
    first = regions[0][0]
    total = sum(e - s for s, e in regions)
    placed = {}
    for slot, ws in items:
        key = tuple(ws)
        if key not in placed:
            data = b"".join(w.to_bytes(2, "little") for w in ws) + b"\0\0"
            for r in regions:
                if r[1] - r[0] >= len(data):
                    break
            else:
                sys.exit(f"{label} out of space for {len(data)} bytes")
            rom[r[0]:r[0] + len(data)] = data
            placed[key] = 0x8000 | (r[0] & 0x7FFF)
            r[0] += len(data)
        p = placed[key]
        rom[slot], rom[slot + 1] = p & 0xFF, p >> 8
    for s, e in regions:
        rom[s:e] = b"\xff" * (e - s)
    free = sum(e - s for s, e in regions)
    print(f"{label}: {total - free} / {total} bytes, {free} free")
    return [(s, e) for s, e in regions if e > s]


def subtract(areas, reserved, minimum=0x40):
    """areas minus reserved ranges (with a 0x10 gap), dropping pieces under minimum bytes"""
    out = list(areas)
    for r in reserved:
        lo, hi = r.start - 0x10, r.stop + 0x10
        nxt = []
        for s, e in out:
            if e <= lo or s >= hi:
                nxt.append((s, e))
                continue
            if lo - s >= minimum:
                nxt.append((s, lo))
            if e - hi >= minimum:
                nxt.append(((hi + 1) & ~1, e))
        out = nxt
    return out


def ff_areas(jp, rom, bank, minimum=0x40, margin=0x10):
    """0xFF runs in a bank that are 0xFF in both the Japanese ROM and in.smc (left margins kept)."""
    out, base = [], (bank & 0x7F) * 0x8000
    k, end = base, base + 0x8000
    while k < end:
        if jp[k] == 0xFF and rom[k] == 0xFF:
            e = k
            while e < end and jp[e] == 0xFF and rom[e] == 0xFF:
                e += 1
            s = (k + margin + 1) & ~1
            if e - s >= minimum:
                out.append((s, e))
            k = e
        else:
            k += 1
    return out


def main():
    jp = open(sys.argv[1], "rb").read()
    rom = bytearray(open(sys.argv[2], "rb").read())
    table = kr1.table()
    enc = kr1.Encoder(table)
    n = D.count(jp)

    texts, set_texts, ui_fixes = {}, {}, []
    for path in sys.argv[5:]:
        if os.path.basename(path).startswith("ui-"):
            for row in open(path, encoding="utf-8"):
                row = row.rstrip("\n")
                if row and not row.startswith("#"):
                    off, old, new, *cap = row.split("\t")
                    ui_fixes.append((int(off, 16), old, new, int(cap[0]) if cap else None))
            continue
        col = -1
        for row in open(path, encoding="utf-8"):
            cols = row.rstrip("\n").split("\t")
            if cols[0] == "id":
                col = cols.index("text") if "text" in cols else -1
                continue
            if len(cols) < 2:
                continue
            if ":" in cols[0]:
                name, idx = cols[0].split(":")
                set_texts.setdefault(name, {})[int(idx, 16)] = cols[col]
            else:
                texts[int(cols[0], 16)] = cols[col]

    # Slots that share a Japanese string share its translation; review files
    # list each string once, under its first slot.
    for name, d in set_texts.items():
        jp_ptr = [p for _, p in textsets.pointers(jp, name)]
        first = {}
        for i, p in enumerate(jp_ptr):
            first.setdefault(p, i)
        for i, p in enumerate(jp_ptr):
            if i not in d and first[p] in d:
                d[i] = d[first[p]]

    # Current strings for every id and shout, as code lists.
    cur = {i: D.words(rom, D.line_offset(rom, i)) for i in range(n)}
    shouts = [D.words(rom, D.off(0x8E, rom[op] | rom[op + 1] << 8)) for op in SHOUT_OPERANDS]
    set_cur = {name: [w for _, _, _, w in textsets.strings(rom, name)] for name in set_texts}

    spans = bank_spans(jp)
    keep = other_text_codes(jp, rom, spans)
    for ws in shouts:
        keep.update(w & 0x7FFF for w in ws)
    for i in range(n):
        if i not in texts:
            keep.update(w & 0x7FFF for w in cur[i])
    all_texts = [(f"{i:04X}", t) for i, t in sorted(texts.items())]
    all_texts += [(f"{name}:{i:03X}", t) for name, d in sorted(set_texts.items()) for i, t in sorted(d.items())]
    all_texts += [(f"ui:{o:06X}", new) for o, _, new, _ in ui_fixes]
    for o, old, _, _ in ui_fixes:  # glyphs the old UI text used stay reserved only through other texts
        if D.decode(D.words(rom, o, 200), table) != old:
            sys.exit(f"ui {o:06X}: current text differs: {D.decode(D.words(rom, o, 200), table)!r}")
    needed = []
    for i, t in all_texts:
        for tok in enc.tokens(t):
            if tok == "/":
                continue
            if not enc.missing(tok):
                keep.add(enc.code(tok) & 0x7FFF)
            elif tok not in needed:
                if len(tok) != 1 or not ("가" <= tok <= "힣"):
                    sys.exit(f"{i}: no glyph for {tok!r}")
                needed.append(tok)
    free = [c for c in font1.codes() if c >= 0x500 and c not in keep and not table.get(c, "").startswith("{")]
    free += list(fontext1.codes())
    fontext1.install(rom)
    if len(needed) > len(free):
        sys.exit(f"need {len(needed)} new glyphs, only {len(free)} free slots")
    # Glyphs first needed after a release are placed after the others, so the codes
    # of every glyph a released ROM already has stay the same.
    late = lambda ch: LATE_GLYPHS.index(ch) if ch in LATE_GLYPHS else -1  # noqa: E731
    for ch, c in zip(sorted(needed, key=lambda ch: (late(ch), ch)), free):
        write_glyph(rom, c, draw_glyph(ch))
        print(f"new glyph {ch} -> {c:03X} (was {table.get(c)})")
        old = table.get(c)
        if old in enc.enc and enc.enc[old] == c:
            del enc.enc[old]
        enc.enc[ch] = c
        table[c] = ch

    for i, t in texts.items():
        cur[i] = enc.encode(t)
    for name, d in set_texts.items():
        for i, t in d.items():
            set_cur[name][i] = enc.encode(t)

    by_bank = {}
    for i in range(n):
        slot, bank = D.table_slot(jp, i)
        by_bank.setdefault(bank, []).append((slot, cur[i]))
    for k, op in enumerate(SHOUT_OPERANDS):
        by_bank[0x8E].append((op, shouts[k]))
    # Free space reserved for the extra glyph blocks must stay untouched.
    reserved = [range(fontext1.off(b, a), fontext1.off(b, a) + 0x1000) for b, a in fontext1.BLOCKS]
    leftover = {}
    for bank, items in sorted(by_bank.items()):
        leftover[bank] = repack(rom, items, [spans[bank]], f"bank {bank:02X}")
    for name, codes in sorted(set_cur.items()):
        bank = textsets.SETS[name][0]
        extra = leftover.pop(bank, []) + subtract(ff_areas(jp, rom, bank), reserved)
        slots = [slot for slot, _ in textsets.pointers(jp, name)]
        items, span = list(zip(slots, codes)), set_span(jp, name)
        if name == "event":
            # The list scrolls one hidden row past the last event and draws entry
            # 204, which in the original reads the first string's codes as a WRAM
            # pointer; garbage there can wrap the line and hang the screen.
            guard = slots[-1] + 2
            items.append((guard, []))
            span = (max(span[0], guard + 2), span[1])
        leftover[bank] = repack(rom, items, [span] + extra, name)

    for o, old, new, cap in ui_fixes:
        cur = D.words(rom, o, 200)
        codes = enc.encode(new)
        if len(codes) > (cap or len(cur)):
            sys.exit(f"ui {o:06X}: {new!r} is {len(codes)} codes, slot holds {cap or len(cur)}")
        rom[o:o + 2 * len(codes) + 2] = b"".join(c.to_bytes(2, "little") for c in codes) + b"\0\0"
    if ui_fixes:
        print(f"ui: {len(ui_fixes)} strings")

    open(sys.argv[3], "wb").write(rom)
    with open(sys.argv[4], "w", encoding="utf-8") as f:
        f.writelines(f"{c:03X}={table[c]}\n" for c in sorted(table))


if __name__ == "__main__":
    main()
