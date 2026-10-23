"""Make the Totsugeki-hen password readable on the Kakusei-hen input screen.

usage: password.py jp.smc in.smc out.smc table.txt

Totsugeki-hen v1.1 shows its ending password with its own Korean glyphs, one
per kana code. The input screen here must show the same glyph for each symbol,
and what a cell enters must match the pair table the checker reads:

  $81:8D56 / $81:8E00  code each hiragana / katakana cell enters (85 each,
                       index = row * 15 + column)
  $84:A3E0 / $84:A4D0  the two grids drawn on screen (16-bit strings)
  $83:A60E             256 pairs of codes; the checker ($83:A1F8) turns each
                       two typed characters into the byte whose pair matches
  $83:AEB0             name conversion: the name bytes in the password are
                       Totsugeki-hen codes listed at $83:AD58; the same index
                       here is the code the name is shown with

Every symbol gets one Kakusei-hen code whose glyph is the Korean letter in
tables/totsugeki-password.tsv, and all five tables use that code. Letters the
font lacks are drawn into unused glyph slots, like dialogue_patch.py does.

The same screen also takes phrase passwords: $83:A408 compares the typed
letters with six strings ($83:B008 ...) before the checker runs. v1.1 made
them Korean ("...신룡"); they are re-encoded here and any letter of theirs that
no symbol cell shows goes to a spare cell, so they stay typeable.

CLEAR_PHRASE is one more phrase, checked where $83:A408 gives up ($83:A4D0):
it starts the game as if a Totsugeki-hen clear password had been entered
(see README chapter 11 for the values), keeping Kakusei-hen's default name.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue_patch as dp  # noqa: E402
from dialogue import off, words  # noqa: E402
from extract import load  # noqa: E402
from usedsheet import N  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ENTRY = (off(0x81, 0x8D56), off(0x81, 0x8E00))
GRID = (off(0x84, 0xA3E0), off(0x84, 0xA4D0))
PAIRS = off(0x83, 0xA60E)
NAME_FROM, NAME_TO, NAME_LEN = off(0x83, 0xAD58), off(0x83, 0xAEB0), 171
CELLS = 85
PHRASES = [off(0x83, a) for a in (0xB008, 0xB046, 0xB0A4, 0xB10E, 0xB182, 0xB1E2)]
CLEAR_PHRASE = "손오공은사이어인"
NO_MATCH = off(0x83, 0xA4D0)  # LDA #0 / PLB / PLP / RTL: no phrase matched
ROUTINE, PHRASE_DATA = 0xFE00, 0xFE80  # bank $83, 0xFF in the Japanese ROM
STATS = (off(0x83, 0xA3C0), off(0x83, 0xA3FF))  # starting stats the password path sets
# Play time the debug-menu ending password carries (bytes 21-22): 0 h 2 min.
CLEAR_PLAY_MINUTES = 2


def w16(rom, o):
    return rom[o] | rom[o + 1] << 8


def put16(rom, o, v):
    rom[o], rom[o + 1] = v & 0xFF, v >> 8


def grid_offsets(base):
    """File offset of each cell in a drawn grid: rows of ' ' + 5 + ' ' + 5 + ' ' + 5 + newline."""
    out = []
    for cell in range(CELLS):
        r, c = divmod(cell, 15)
        out.append(base + 2 * (r * 19 + 1 + c + c // 5))
    return out


def counterpart(kana):
    """Hiragana <-> katakana; Totsugeki-hen uses hiragana for some look-alike symbols."""
    o = ord(kana)
    if 0x3041 <= o <= 0x3096:
        return chr(o + 0x60)
    if 0x30A1 <= o <= 0x30F6:
        return chr(o - 0x60)
    return None


def main():
    jp = open(sys.argv[1], "rb").read()
    rom = bytearray(open(sys.argv[2], "rb").read())
    table = load(sys.argv[4])
    jt = load(os.path.join(ROOT, "tables", "jp.txt"))

    letters, pairs = {}, []
    for line in open(os.path.join(ROOT, "tables", "totsugeki-password.tsv"), encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if line.startswith("#"):
            continue
        if p[0] == "pair":
            pairs.append((int(p[2], 16), int(p[3], 16)))
        else:
            letters[int(p[0], 16)] = (p[1], p[3])
    symbols = sorted({c for pair in pairs for c in pair})
    targets = [letters[c][1] for c in symbols]
    if len(set(targets)) != len(targets):
        sys.exit("two password symbols would show the same letter")

    enc = {}
    for c in sorted(table):
        enc.setdefault(table[c], c)
    names = {letters[c][1] for c in letters if letters[c][1] not in ("⋮", "ー", "")}
    phrases = []
    for o in PHRASES:
        text, k = "", o
        while w16(rom, k):
            text += table[w16(rom, k)]
            k += 2
        phrases.append((o, text))
    phrase_letters = set("".join(t for _, t in phrases) + CLEAR_PHRASE)
    missing = sorted((set(targets) | names | phrase_letters) - set(enc))
    if missing:
        keep = set()
        for i in range(N):
            bank, _, p = dp.pointer(rom, i)
            if p >= 0x8000:
                keep.update(dp.canon(w & 0x7FFF) for w in words(rom, off(bank, p)) if w != 0x0A)
        keep |= dp.other_text_codes(jp, rom)
        keep |= {dp.canon(enc[t]) for t in targets if t in enc}
        free = [c for c in sorted(table) if 0x100 <= c < 0x900 and dp.canon(c) not in keep and table[c] != " "]
        if len(missing) > len(free):
            sys.exit(f"need {len(missing)} new glyphs, only {len(free)} free slots")
        for ch, c in zip(missing, free):
            dp.write_glyph(rom, c, dp.draw_glyph(ch))
            print(f"new glyph {ch} -> {c:03x} (was {table[c]})")
            for k in [k for k, v in enc.items() if v == c]:
                del enc[k]
            enc[ch] = c
            table[c] = ch
        with open(sys.argv[4], "w", encoding="utf-8") as f:
            f.writelines(f"{c:03x}={table[c]}\n" for c in sorted(table))

    code_of = {c: enc[letters[c][1]] for c in symbols}

    for i, (a, b) in enumerate(pairs):
        put16(rom, PAIRS + 4 * i, code_of[a])
        put16(rom, PAIRS + 4 * i + 2, code_of[b])

    name_code = {}
    for i in range(NAME_LEN):
        letter = letters.get(w16(jp, NAME_FROM + 2 * i), ("", ""))[1]
        if letter in enc:
            name_code[w16(jp, NAME_TO + 2 * i)] = enc[letter]

    by_kana = {letters[c][0]: c for c in symbols}
    assign, spare, blank = {}, [], []
    for entry, grid in zip(ENTRY, GRID):
        cells = grid_offsets(grid)
        for cell in range(CELLS):
            kana = jt.get(w16(jp, entry + 2 * cell), "")
            if w16(jp, cells[cell]) != w16(jp, entry + 2 * cell):
                sys.exit(f"grid layout differs from the entry table at cell {cell}")
            sym = by_kana.get(kana, by_kana.get(counterpart(kana) or ""))
            spot = (entry + 2 * cell, cells[cell])
            if sym is not None:
                assign[spot] = code_of[sym]
                continue
            # Not a password symbol: show the letter a Totsugeki-hen name gets
            # for this kana; gaps in the や/わ rows stay blank.
            assign[spot] = name_code.get(w16(jp, entry + 2 * cell), w16(jp, entry + 2 * cell))
            (blank if kana == " " else spare if kana != "ー" else []).append(spot)
    shown = {table.get(c) for c in assign.values()}
    extra = sorted(phrase_letters - shown)
    if len(extra) > len(spare) + len(blank):
        sys.exit(f"no room on the grid for {''.join(extra)}")
    for ch, spot in zip(extra, spare + blank):
        assign[spot] = enc[ch]
    for (entry_at, grid_at), code in assign.items():
        put16(rom, entry_at, code)
        put16(rom, grid_at, code)

    for o, text in phrases:
        for k, ch in enumerate(text):
            put16(rom, o + 2 * k, enc[ch])

    # Clear phrase: compare like the six phrases, then set what $83:A313 sets
    # for a data password (technique 15, starting stats, play time) and return
    # 1, the "phrase accepted" result, so the name is not taken from the password.
    pd = off(0x83, PHRASE_DATA)
    lo, hi = PHRASE_DATA & 0xFF, PHRASE_DATA >> 8
    code = bytearray([
        0xA2, 0x00, 0x00,              # LDX #0
        0xBD, lo, hi,                  # loop: LDA phrase,X
        0xDD, 0x00, 0x1E,              # CMP $1E00,X
        0xD0, 0x09,                    # BNE no
        0xBD, lo, hi,                  # LDA phrase,X
        0xF0, 0x0A,                    # BEQ yes
        0xE8, 0xE8,                    # INX / INX
        0x80, 0xEF,                    # BRA loop
        0xA9, 0x00, 0x00,              # no: LDA #0
        0xAB, 0x28, 0x6B,              # PLB / PLP / RTL
        0xA9, 0x0F, 0x00,              # yes: LDA #$000F
        0x22, 0xFB, 0xED, 0x82,        # JSL $82EDFB (learn technique 15)
    ])
    code += rom[STATS[0]:STATS[1]]     # the stat block of $83:A313, verbatim
    code += bytearray([
        0xA9, CLEAR_PLAY_MINUTES, 0x00,  # LDA #minutes
        0x8D, 0x66, 0x02,              # STA $0266 (play time minutes, hours)
        0xA9, 0x01, 0x00,              # LDA #1
        0xAB, 0x28, 0x6B,              # PLB / PLP / RTL
    ])
    r = off(0x83, ROUTINE)
    if any(b != 0xFF for b in rom[r:r + len(code)] + rom[pd:pd + 2 * len(CLEAR_PHRASE) + 2]):
        sys.exit("phrase routine area is not free")
    rom[r:r + len(code)] = code
    for k, ch in enumerate(CLEAR_PHRASE):
        put16(rom, pd + 2 * k, enc[ch])
    put16(rom, pd + 2 * len(CLEAR_PHRASE), 0)
    rom[NO_MATCH:NO_MATCH + 6] = bytes([0x4C, ROUTINE & 0xFF, ROUTINE >> 8, 0xEA, 0xEA, 0xEA])  # JMP routine

    for i in range(NAME_LEN):
        jcode = w16(jp, NAME_TO + 2 * i)
        put16(rom, NAME_TO + 2 * i, name_code.get(jcode, jcode))

    open(sys.argv[3], "wb").write(rom)
    print(f"{len(symbols)} password symbols, {len(assign)} input cells, {NAME_LEN} name letters, "
          f"phrase letters added to the grid: {''.join(extra) or '-'}")


if __name__ == "__main__":
    main()
