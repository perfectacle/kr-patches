"""Rewrite ending-credit name lines in place: credits.py rom.smc

Entries live in bank 83 behind the 21-word pointer table at file 0x1949D. A
replacement that fits is written in place; a longer one goes to FREE, a run of
0xFF that is unused in the JP ROM too, and its pointer is updated.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from extract import load  # noqa: E402

TABLE = 0x1949D
FREE = 0x1F510
EDITS = {9: "   야지로베 카린  신  미스터 포포"}

kt = load(os.path.join(os.path.dirname(__file__), "..", "tables", "kr-v1.3.txt"))
enc = {}
for c in sorted(kt):
    enc.setdefault(kt[c], c)
rom = bytearray(open(sys.argv[1], "rb").read())
for k, text in EDITS.items():
    p = rom[TABLE + 2 * k] | rom[TABLE + 2 * k + 1] << 8
    o = 0x18000 + (p & 0x7FFF)
    n = 0
    while rom[o + 2 * n] | rom[o + 2 * n + 1] << 8:
        n += 1
    data = b"".join(enc[ch].to_bytes(2, "little") for ch in text) + b"\0\0"
    if len(text) <= n:
        rom[o:o + 2 * n + 2] = data + b"\xff" * (2 * n + 2 - len(data))
        continue
    if any(b != 0xFF for b in rom[FREE:FREE + len(data)]):
        sys.exit(f"credit {k}: free space at {FREE:#x} is taken")
    rom[FREE:FREE + len(data)] = data
    rom[TABLE + 2 * k:TABLE + 2 * k + 2] = (0x8000 | (FREE & 0x7FFF)).to_bytes(2, "little")
    FREE += len(data)
open(sys.argv[1], "wb").write(rom)
