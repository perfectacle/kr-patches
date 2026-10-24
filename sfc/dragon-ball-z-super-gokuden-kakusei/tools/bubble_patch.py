"""Replace battle speech-bubble lines ($B4).

usage: bubble_patch.py in.smc bubbles.tsv out.smc table.txt

bubbles.tsv: `id<TAB>text` for ids 0x1000-0x13FF, '/' = line break. Several
ids can point at one string; a listed id rewrites that string for all of
them, so ids sharing a string must not be listed with different texts.
table.txt is the glyph table dialogue_patch.py wrote, so this runs after it
and uses no glyph that table lacks.

A string that fits in its old slot is rewritten in place; otherwise it moves
to a 0xFF run in bank $B4 and every pointer to it ($B4:8000 + (id-0x1000)*2,
16-bit, bank-relative) is updated.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dialogue import off, words  # noqa: E402
from dialogue_patch import tokenize  # noqa: E402
from extract import load  # noqa: E402

BANK = 0xB4
TABLE = off(BANK, 0x8000)
COUNT = 0x400
STRINGS = off(BANK, 0x8000 + 2 * COUNT)
END = off(BANK, 0xFFFF) + 1


def pointer(rom, k):
    return rom[TABLE + 2 * k] | rom[TABLE + 2 * k + 1] << 8


def main():
    rom = bytearray(open(sys.argv[1], "rb").read())
    table = load(sys.argv[4])
    enc = {}
    for c in sorted(table):
        enc.setdefault(table[c], c)

    fixes = {}
    for line in open(sys.argv[2], encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        i, text = line.split("\t", 1)
        fixes[int(i, 16) - 0x1000] = text

    groups = {}
    for k in range(COUNT):
        groups.setdefault(pointer(rom, k), []).append(k)
    strings = {}
    for k, text in fixes.items():
        p = pointer(rom, k)
        if strings.get(p, text) != text:
            sys.exit(f"{0x1000 + k:04x} shares its string with another listed id but has a different text")
        strings[p] = text

    pending = []
    for p, text in strings.items():
        data = bytearray()
        for tok in tokenize(text, enc):
            if tok != "/" and tok not in enc:
                sys.exit(f"no glyph for {tok!r} in {text}")
            w = 0x0A if tok == "/" else enc[tok]
            data += bytes([w & 0xFF, w >> 8])
        data += b"\0\0"
        o = off(BANK, p)
        old = 2 * len(words(rom, o)) + 2
        if len(data) <= old:
            rom[o:o + len(data)] = data
            rom[o + len(data):o + old] = b"\xff" * (old - len(data))
        else:
            rom[o:o + old] = b"\xff" * old
            pending.append((groups[p], data))

    # Free space: 0xFF runs after the pointer table, one byte of margin next
    # to live data, like dialogue_patch.py.
    runs, k = [], STRINGS
    while k < END:
        if rom[k] != 0xFF:
            k += 1
            continue
        e = k
        while e < END and rom[e] == 0xFF:
            e += 1
        s0, s1 = k + 1, (e - 1 if e < END else e)
        if s1 - s0 >= 2:
            runs.append([s0, s1])
        k = e
    for ids, data in sorted(pending, key=lambda x: -len(x[1])):
        for sp in runs:
            if sp[0] & 1:
                sp[0] += 1
            if sp[1] - sp[0] >= len(data):
                start = sp[0]
                sp[0] += len(data)
                break
        else:
            sys.exit(f"bank {BANK:02x} is out of space for {len(data)} bytes")
        rom[start:start + len(data)] = data
        newp = 0x8000 | (start & 0x7FFF)
        for k in ids:
            rom[TABLE + 2 * k], rom[TABLE + 2 * k + 1] = newp & 0xFF, newp >> 8
    open(sys.argv[3], "wb").write(rom)
    print(f"{len(fixes)} bubbles, {len(strings)} strings, {len(pending)} relocated, "
          f"{sum(max(0, e - s) for s, e in runs)} bytes free in bank {BANK:02x}")


if __name__ == "__main__":
    main()
