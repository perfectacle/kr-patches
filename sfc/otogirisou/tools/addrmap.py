"""Map ROM script addresses back to script lines.

usage: addrmap.py table.tbl script.txt out.tsv [--raw]
Writes "line<TAB>start<TAB>end" (LoROM addresses, end exclusive) for every script line,
using the same assembly as assemble.py. --raw skips punctuation normalization, which is
what the v1.0 dump needs to reproduce v1.0 addresses.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from assemble import parse, normalize_text, lorom_next
from dump import load_table, KR_START


def main(tbl, script, out, raw=False):
    table = load_table(tbl)
    text = open(script, encoding='utf-8').read()
    addr = KR_START
    rows = []
    for n, line in enumerate(text.split('\n'), 1):
        seg = line if raw else normalize_text(line)
        start = addr
        for kind, v in parse(seg + ('\n' if line.startswith('#') else ''), table):
            if kind != 'L':
                addr = lorom_next(addr, 2 if kind == 'S' else 3)
        rows.append('%d\t%06X\t%06X' % (n, start, addr))
    open(out, 'w').write('\n'.join(rows) + '\n')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], '--raw' in sys.argv)
