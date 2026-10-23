"""Show a fixed phrase as the ending password instead of the generated 50 characters.

usage: endpw1.py rom.smc table.txt

The ending ($81:D0xx) packs the save data into 25 bytes at $7E:1F00, turns each byte
into two kana codes through the pair table $B7:F09F ($81:D169-$81:D19B, into $7E:1F80),
copies them to $7E:0A00 in groups of five ($81:D19C-$81:D1C4), then appends a newline and
" TO BE CONTINUED" ($81:D1C5) and draws $0A00 in an 18 x 14 window ($81:D1E7).

Kakusei-hen v1.3 accepts the phrase below (it carries no name), so the ending prints it instead: the code
from $81:D169 to $81:D1C4 is replaced by a copy of PHRASE_LINES into $0A00, and the
drawing continues at $81:D1C5 as before. The window is 144 px wide; the phrase is
eight small kana codes (8 px each), centred with five small spaces, on the second line,
so " TO BE CONTINUED" stays on the fifth line.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402

PHRASE = "손오공은사이어인"
START, END, RESUME = D.off(0x81, 0xD169), D.off(0x81, 0xD1C5), 0xD1C5
SMALL, SPACE, NEWLINE = 0x8000, 0x82C5, 0x000A
ROOT = os.path.join(os.path.dirname(__file__), "..")


def phrase_codes():
    """Totsugeki-hen kana codes whose 8 px glyph is each syllable (tables/password.tsv)."""
    shown = {}
    for line in open(os.path.join(ROOT, "tables", "password.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        c = line.rstrip("\n").split("\t")
        shown.setdefault(c[3], int(c[0], 16))
    return [shown[ch] for ch in PHRASE]


def main():
    path = sys.argv[1]
    rom = bytearray(open(path, "rb").read())
    jp = open(os.path.join(ROOT, "super-gokuden-jp.smc"), "rb").read()
    if rom[START:END] != jp[START:END]:
        sys.exit("endpw1: $81:D169-$81:D1C4 differs from the Japanese ROM")
    table = D.load_table(sys.argv[2])
    codes = phrase_codes()
    if "".join(table.get(c) for c in codes) != PHRASE:
        sys.exit("endpw1: table names do not spell the phrase")
    words = [NEWLINE] + [SPACE] * 5 + [SMALL | c for c in codes] + [NEWLINE, NEWLINE, 0]
    data = START + 0x14
    dpc = 0x8000 | (data & 0x7FFF)
    code = bytes([
        0xA2, 0x00, 0x00,                     # LDX #$0000
        0xBF, dpc & 0xFF, dpc >> 8, 0x81,     # LDA $81:data,X
        0xF0, 0x07,                           # BEQ done
        0x9D, 0x00, 0x0A,                     # STA $0A00,X
        0xE8, 0xE8,                           # INX / INX
        0x80, 0xF3,                           # BRA LDA
        0x9B,                                 # done: TXY (the code at $81:D1C5 writes from Y)
    ])
    after = 0x8000 | ((START + len(code) + 3) & 0x7FFF)
    rel = RESUME - after
    code += bytes([0x82, rel & 0xFF, rel >> 8])  # BRL $81:D1C5
    assert len(code) == 0x14
    blob = code + b"".join(w.to_bytes(2, "little") for w in words)
    if len(blob) > END - START:
        sys.exit("endpw1: phrase does not fit")
    rom[START:END] = blob + b"\xff" * (END - START - len(blob))
    open(path, "wb").write(rom)
    print(f"ending password: {PHRASE} ({' '.join(f'{c:03X}' for c in codes)})")


if __name__ == "__main__":
    main()
