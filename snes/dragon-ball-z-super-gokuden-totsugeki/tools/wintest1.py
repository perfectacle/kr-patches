"""Make test ROMs for the dialogue window width limit.

usage: wintest1.py kr-v1.1.smc outdir

Replaces dialogue 0x000 (the first narration of a new game) in place with three lines of
「어」(13 px) and 「！」(9 px): 176, 177 and 173 px. narr.smc keeps the narration window
(info FF xx, 176 px); face.smc sets the info to 19 00 (face window, 128 px) and uses
128, 129 and 124 px lines. Run lua/wintest.lua on each and look for "WRAP" in log.txt.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1  # noqa: E402
import width1  # noqa: E402

EO, EX = 0x08F3, 0x016C  # 어, ！ in the v1.1 table


def line(a, b):
    return [EO] * a + [EX] * b


def build(rom, path, lines, info=None):
    r = bytearray(rom)
    ws = []
    for k, l in enumerate(lines):
        if k:
            ws.append(0x000A)
        ws += l
    ws.append(0)
    o = dialogue1.line_offset(r, 0)
    assert len(ws) <= len(dialogue1.words(r, o)) + 1, "test text is longer than dialogue 0x000"
    for k, c in enumerate(ws):
        r[o + 2 * k] = c & 0xFF
        r[o + 2 * k + 1] = c >> 8
    if info:
        i = dialogue1.off(0x8E, 0xC9BA)
        r[i:i + 2] = bytes(info)
    open(path, "wb").write(r)
    print(os.path.basename(path), [sum(width1.char_width(c) for c in l) for l in lines])


def main():
    rom = open(sys.argv[1], "rb").read()
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    build(rom, os.path.join(out, "narr.smc"), [line(8, 8), line(6, 11), line(5, 12)])
    build(rom, os.path.join(out, "face.smc"), [line(5, 7), line(3, 10), line(4, 8)], info=[0x19, 0x00])


if __name__ == "__main__":
    main()
