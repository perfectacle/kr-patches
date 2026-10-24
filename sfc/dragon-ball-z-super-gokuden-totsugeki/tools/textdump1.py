"""Dump every known text string of a ROM as code lists.

usage: textdump1.py rom.smc out.tsv

Domains: dialogue ids, battle shouts, the pointer-table sets in textsets.py, and the
in-place strings listed in tables/ui-v1.0.tsv and tables/ui-fixes.tsv (menus, credits).
Columns: domain, id, file offset, codes (hex, space separated).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402
import textsets  # noqa: E402
from text_patch1 import FONT_AREAS, SHOUT_OPERANDS  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def ui_offsets():
    offs = set()
    for row in open(os.path.join(ROOT, "tables", "ui-v1.0.tsv"), encoding="utf-8"):
        c = row.split("\t")
        if c[0].startswith("ui:"):
            offs.add(int(c[0][3:], 16))
    # ui-v1.0.tsv also lists a few font bytes that v1.0 changed; they are not text.
    offs = {o for o in offs if not any(o in r for r in FONT_AREAS)}
    for row in open(os.path.join(ROOT, "tables", "ui-fixes.tsv"), encoding="utf-8"):
        if row.strip() and not row.startswith("#"):
            offs.add(int(row.split("\t")[0], 16))
    return sorted(offs)


def dump(rom):
    out = []
    for i, o in D.all_lines(rom):
        out.append(("dialogue", f"{i:04X}", o, D.words(rom, o)))
    for k, op in enumerate(SHOUT_OPERANDS):
        o = D.off(0x8E, rom[op] | rom[op + 1] << 8)
        out.append(("shout", str(k), o, D.words(rom, o)))
    for name in textsets.SETS:
        for k, (_, _, o, ws) in enumerate(textsets.strings(rom, name)):
            out.append((name, f"{k:03X}", o, ws))
    for o in ui_offsets():
        out.append(("ui", f"{o:06X}", o, D.words(rom, o, 200)))
    return out


def main():
    rom = open(sys.argv[1], "rb").read()
    with open(sys.argv[2], "w") as f:
        for dom, i, o, ws in dump(rom):
            f.write(f"{dom}\t{i}\t{o:06X}\t{' '.join(f'{w:04X}' for w in ws)}\n")


if __name__ == "__main__":
    main()
