"""Dump the v1.0 (KR) or JP script as text.

usage: dump.py kr rom.sfc table.tbl out.txt
       dump.py jp rom.sfc table.tbl out.txt
Characters come from the table ("code<TAB>char"); unknown codes print as <NNNN>.
Control codes print as {XX} or {XX:a,b}; jump targets as @addr. Each item that is a
jump target starts a new line with its address.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from script import KRReader, JPReader, read_op, unlorom

KR_START, KR_END = 0x208000, 0x359AD3
JP_END_BITS = 2460960
# scenario start points ($02:A627); KR entry 2 is the corrected one
ENTRIES = {'kr': (0x208000, 0x2ED6A9, 0x25E6A4), 'jp': (0, 1693536, 666552)}


def load_table(path):
    t = {}
    if path and os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            line = line.rstrip('\n')
            if '\t' in line:
                k, v = line.split('\t', 1)
                t[int(k)] = v
    return t


def items(kind, rom):
    if kind == 'kr':
        rd = KRReader(rom, KR_START)
        while rd.addr < KR_END:
            yield read_op(rom, rd)
    else:
        rd = JPReader(rom, 0)
        while rd.pos < JP_END_BITS:
            yield read_op(rom, rd)


def render(kind, rom, table):
    its = list(items(kind, rom))
    targets = {v for _, _, a in its for k, v in a if k == 'r'}
    targets |= set(ENTRIES[kind])
    fmt = (lambda p: '%06X' % p) if kind == 'kr' else (lambda p: 'b%07d' % p)
    out = []
    for p, s, a in its:
        if p in targets:
            out.append('\n#' + fmt(p) + '\n')
        if s < 0x1000:
            out.append(table.get(s, '<%04d>' % s))
        else:
            code = s & 0xFFF
            if a:
                args = ','.join(('@' + fmt(v)) if k == 'r' else str(v) for k, v in a)
                out.append('{%02X:%s}' % (code, args))
            else:
                out.append('{%02X}' % code)
            if code == 0x25:
                out.append('\n')
    return ''.join(out)


if __name__ == '__main__':
    kind, romp, tbl, outp = sys.argv[1:5]
    rom = open(romp, 'rb').read()
    open(outp, 'w', encoding='utf-8').write(render(kind, rom, load_table(tbl)))
