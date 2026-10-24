"""Dump dialogue as TSV: id, window info, JP text, KR text ("/" = newline).

usage: extract1.py jp.smc kr.smc jp_table kr_table out.tsv
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402


def main():
    j = open(sys.argv[1], "rb").read()
    k = open(sys.argv[2], "rb").read()
    jt, kt = D.load_table(sys.argv[3]), D.load_table(sys.argv[4])
    base = D.off(0x8E, D.INFO & 0xFFFF)
    with open(sys.argv[5], "w", encoding="utf-8") as f:
        f.write("id\tinfo\tjp\tkr\n")
        for i in range(D.count(j)):
            wj = D.words(j, D.line_offset(j, i))
            wk = D.words(k, D.line_offset(k, i))
            f.write("%04X\t%02X%02X\t%s\t%s\n" % (i, j[base + 2 * i], j[base + 2 * i + 1],
                                                 D.decode(wj, jt), D.decode(wk, kt)))


if __name__ == "__main__":
    main()
