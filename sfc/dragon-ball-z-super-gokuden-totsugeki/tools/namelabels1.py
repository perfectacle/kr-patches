"""Name-entry list labels: give every row the same width so the names line up.

usage: namelabels1.py rom.smc table.txt

The name list ($80:9529) draws each label from $80:F237 + row * 18 and appends the
name right after it, so the name starts where the label ends. v1.0 left the labels
at 63-67 px and the first row in English (PLAYER). Every label becomes 67 px, with the
small dots on x = 39, 47, 55 and a 4 px gap before the name. 플레이어 is 52 px, so its row
ends in the 9 px dot (code 0x016B) at x = 54 instead. A row holds 8 codes and its terminator.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402
import kr1  # noqa: E402
import width1  # noqa: E402

FIRST, STRIDE, ROW_CODES, WIDTH = 0x7237, 18, 8, 67
LABELS = {
    0: ("PLAYER‥{sp4}", "플레이어{sp2}‥{sp4}"),
    2: ("부하{s: }{s: }{s:‥}{s:‥}{s: }", "부하{sp7}{sp6}{s:‥}{s:‥}{s:‥}{sp4}"),
    3: ("나쁜놈{sp4}{sp4}{s:‥}{s: }", "나쁜놈{s: }{s:‥}{s:‥}{sp4}"),
    4: ("조언자{sp4}{s:‥}{s:‥}{s: }", "조언자{s: }{s:‥}{s:‥}{sp4}"),
}


def main():
    rom = bytearray(open(sys.argv[1], "rb").read())
    enc = kr1.Encoder(D.load_table(sys.argv[2]))
    for row, (old, new) in LABELS.items():
        o = FIRST + row * STRIDE
        assert D.words(rom, o, ROW_CODES + 1) == enc.encode(old), f"row {row} at {o:05X} differs"
        codes = enc.encode(new)
        assert len(codes) <= ROW_CODES, f"row {row}: {len(codes)} codes"
        rom[o:o + 2 * len(codes) + 2] = b"".join(c.to_bytes(2, "little") for c in codes) + b"\0\0"
    for row in range(5):
        w = sum(map(width1.char_width, D.words(rom, FIRST + row * STRIDE, ROW_CODES + 1)))
        assert w == WIDTH, f"row {row} is {w} px"
    open(sys.argv[1], "wb").write(rom)


if __name__ == "__main__":
    main()
