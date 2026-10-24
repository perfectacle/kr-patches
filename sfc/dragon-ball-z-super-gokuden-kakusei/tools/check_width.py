"""Fail when a line is wider or taller than its window: check_width.py jp.smc rom.smc

Every glyph advances 12 pixels and the engine ($80:9B2C) moves to the next
line when the next glyph would pass the window width ($020E tiles x 8). The
overflowing glyphs take an extra line, which pushes the rest of the page down
or, in battle bubbles, out of the window.

Story dialogue ($80:B879): narration window (speaker byte 0xFF) 0x15 tiles =
14 glyphs, face window 0x10 tiles = 10 glyphs. Ids below 0x200 have no
speaker byte and always use the face window. Font-test lines are skipped.

Battle bubbles ($B4:8000, ids 0x1000-0x13FF) are shown by battle script
opcodes in bank $B5: opcode 01 ($82:D172) opens 0x0C x 0x0A tiles = 8 glyphs
x 5 lines, opcodes 02/03 ($82:D1DC) open 0x12 x 0x06 tiles = 12 glyphs x 3
lines. Bubble ids no script references are checked against the window the
Japanese line fits (more than 3 lines needs the tall one); Japanese lines that
fit neither are listed but do not fail.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dialogue import line_offset, off, words  # noqa: E402
from extract import speaker  # noqa: E402
from usedsheet import N, odd  # noqa: E402

FACE, NARRATION = 10, 14
TALL, WIDE = (8, 5), (12, 3)
BUBBLE_TABLE = off(0xB4, 0x8000)
BUBBLES = 0x400
# Battle script entry tables (bank $B5), read at $82:D099/D0DE/D0EF/D125.
SCRIPT_TABLES = (0xBA7E, 0xC5AC, 0xCC74, 0xD141)
SCRIPT_ENTRIES = 80
# Opcode lengths from the handlers at $82:D14C; 0E-11 also jump to a 16-bit target.
OP_LEN = {1: 3, 2: 3, 3: 3, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 0xA: 3, 0xB: 1,
          0xC: 2, 0xD: 2, 0xE: 4, 0xF: 4, 0x10: 4, 0x11: 4, 0x12: 3}


def lines(ws):
    out = [0]
    for w in ws:
        if w == 0x0A:
            out.append(0)
        else:
            out[-1] += 1
    return out


def fits(shape, window):
    return max(shape) <= window[0] and len(shape) <= window[1]


def script_windows(rom):
    """Bubble id -> windows, from every opcode 01-03 the battle scripts can reach."""
    w16 = lambda a: rom[off(0xB5, a)] | rom[off(0xB5, a) + 1] << 8
    todo = [w16(t + 2 * k) for t in SCRIPT_TABLES for k in range(SCRIPT_ENTRIES)]
    seen, out = set(), {}
    while todo:
        a = todo.pop()
        while a not in seen:
            seen.add(a)
            op = rom[off(0xB5, a)]
            if op not in OP_LEN:
                break
            if op in (1, 2, 3):
                out.setdefault(w16(a + 1), set()).add(TALL if op == 1 else WIDE)
            if op in (0xE, 0xF, 0x10, 0x11):
                todo.append(w16(a + 2))
            a += OP_LEN[op]
    return out


def bubble(rom, k):
    p = rom[BUBBLE_TABLE + 2 * k] | rom[BUBBLE_TABLE + 2 * k + 1] << 8
    return words(rom, off(0xB4, p))


def main():
    jp = open(sys.argv[1], "rb").read()
    rom = open(sys.argv[2], "rb").read()
    bad = 0
    for i in range(N):
        o = line_offset(rom, i)
        if o is None:
            continue
        ws = words(rom, o)
        if any(odd(w & 0x7FFF) for w in ws if w != 0x0A):
            continue
        width = NARRATION if speaker(rom, i) == "ff" else FACE
        over = [n for n in lines(ws) if n > width]
        if over:
            bad += 1
            print(f"{i:03x}: {over} glyphs, window holds {width}")

    windows = script_windows(jp)
    for k in range(BUBBLES):
        i = 0x1000 + k
        jw, kw = bubble(jp, k), bubble(rom, k)
        if any(odd(w & 0x7FFF) for w in jw + kw if w != 0x0A):
            continue
        shape = lines(kw)
        if i in windows:
            need = windows[i]
        else:
            jshape = lines(jw)
            win = TALL if len(jshape) > WIDE[1] else WIDE
            if not fits(jshape, win):
                print(f"{i:04x}: no script shows it; Japanese {jshape} fits no window, Korean {shape}")
                continue
            need = {win}
        for win in need:
            if not fits(shape, win):
                bad += 1
                print(f"{i:04x}: {shape} glyphs per line, window holds {win[0]} x {win[1]}")
    if bad:
        sys.exit(f"{bad} lines are wider or taller than their window")
    print("dialogue and bubble widths ok")


if __name__ == "__main__":
    main()
