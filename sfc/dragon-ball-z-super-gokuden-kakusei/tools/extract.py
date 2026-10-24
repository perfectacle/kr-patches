"""Dump every dialogue line as JP/KR pairs: extract.py out.tsv

Columns: id, speaker byte (from the $98:8000 table, ids >= 0x200 only),
JP text, KR text. Line breaks are shown as '/'. Lines that contain glyph
codes from the font's lower half-rows are font-test garbage and are skipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dialogue import line_offset, off, words  # noqa: E402
from usedsheet import N, odd  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def load(path):
    t = {}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if "=" in line:
            k, v = line.split("=", 1)
            t[int(k, 16)] = v
    return t


def decode(ws, table):
    out = []
    for w in ws:
        if w == 0x0A:
            out.append("/")
        else:
            out.append(table.get(w & 0x7FFF, "{%03x}" % w))
    return "".join(out)


def speaker(rom, i):
    if i < 0x200:
        return ""
    o = off(0x98, 0x8000) + (i - 0x200) * 2
    return "%02x" % rom[o]


def main():
    jp_rom = open(os.path.join(ROOT, "super-gokuden-jp.smc"), "rb").read()
    kr_rom = open(os.path.join(ROOT, sys.argv[2] if len(sys.argv) > 2 else "v1.1/kr-v1.1.smc"), "rb").read()
    jt = load(os.path.join(ROOT, "tables", "jp.txt"))
    kt = load(os.path.join(ROOT, "tables", "kr.txt"))
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        for i in range(N):
            jw = words(jp_rom, line_offset(jp_rom, i))
            kw = words(kr_rom, line_offset(kr_rom, i))
            if any(odd(w & 0x7FFF) for w in jw + kw if w != 0x0A):
                continue
            f.write("%03x\t%s\t%s\t%s\n" % (i, speaker(jp_rom, i), decode(jw, jt), decode(kw, kt)))


if __name__ == "__main__":
    main()
