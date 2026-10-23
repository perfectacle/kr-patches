"""Dialogue lines of Totsugeki-hen, addressed by 16-bit id (dispatch at $81:AC4C).

Each id range lives in one bank with a table of 16-bit pointers into that bank.
Per-id window info (speaker etc.) is a 2-byte entry at $8E:C9BA + id*2.
Strings: 16-bit LE codes, 0x000A newline, 0x0000 end.
"""

BANKS = [  # (first id, end id exclusive, bank, table address)
    (0x000, 0x25C, 0xA8, 0x8000),
    (0x25C, 0x571, 0xA9, 0x87D6),
    (0x571, 0x81C, 0xAB, 0x8000),
    (0x81C, 0xA65, 0x9D, 0x8000),
    (0xA65, 0xCC7, 0x9E, 0x8000),
    (0xCC7, 0xF58, 0xB2, 0x8000),
    (0xF58, 0x121F, 0xB4, 0x8000),
    (0x121F, 0x14AD, 0xB5, 0x8000),
    (0x14AD, None, 0x8E, 0xB67A),
]
INFO = 0x8EC9BA


def off(bank, addr):
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def words(rom, o, limit=4000):
    out = []
    while len(out) < limit:
        w = rom[o] | rom[o + 1] << 8
        if w == 0:
            break
        out.append(w)
        o += 2
    return out


def count(rom):
    lo, _, bank, table = BANKS[-1]
    t = off(bank, table)
    first = rom[t] | rom[t + 1] << 8
    return lo + (first - table) // 2


def table_slot(rom, i):
    """file offset of the pointer for id i, and its bank"""
    for lo, hi, bank, table in BANKS:
        if lo <= i and (hi is None or i < hi):
            return off(bank, table) + (i - lo) * 2, bank
    return None


def line_offset(rom, i):
    t, bank = table_slot(rom, i)
    return off(bank, rom[t] | rom[t + 1] << 8)


def all_lines(rom):
    return [(i, line_offset(rom, i)) for i in range(count(rom))]


def load_table(path):
    t = {}
    for l in open(path, encoding="utf-8"):
        l = l.rstrip("\n")
        if "=" in l:
            k, v = l.split("=", 1)
            t[int(k, 16)] = v
    return t


def decode(ws, table):
    out = []
    for w in ws:
        if w == 0x000A:
            out.append("/")
        else:
            c = w & 0x7FFF
            ch = table.get(c)
            if ch is None:
                out.append("{%04X}" % w)
            else:
                out.append(ch if not w & 0x8000 else "{s:%s}" % ch)
    return "".join(out)
