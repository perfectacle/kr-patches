"""Dialogue lines addressed by the script's text opcode (0x08, 16-bit id).

Ids are split across banks; each bank starts with a table of 16-bit pointers
into the same bank (see the id dispatch at $83:BA13).
"""

BANKS = [  # (first id, end id exclusive, bank, table address)
    (0x000, 0x3E0, 0x99, 0x8000),
    (0x3E0, 0x5B7, 0x9A, 0x8000),
    (0x5B7, 0x7AF, 0x9B, 0x8000),
    (0x7AF, 0x97D, 0x9C, 0x8000),
    (0x97D, 0xB45, 0x9D, 0x8000),
    (0xB45, 0xD16, 0x9E, 0x8000),
    (0xD16, 0xED4, 0x9F, 0x8000),
]
LAST_BANK = (0xED4, 0x98, 0xC1C8)


def off(bank, addr):
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def words(rom, o, limit=2000):
    out = []
    while len(out) < limit:
        w = rom[o] | rom[o + 1] << 8
        if w == 0:
            break
        out.append(w)
        o += 2
    return out


def line_offset(rom, i):
    for lo, hi, bank, table in BANKS:
        if lo <= i < hi:
            t = off(bank, table) + (i - lo) * 2
            return off(bank, rom[t] | rom[t + 1] << 8)
    lo, bank, table = LAST_BANK
    t = off(bank, table) + (i - lo) * 2
    p = rom[t] | rom[t + 1] << 8
    return off(bank, p) if p >= 0x8000 else None


def all_lines(rom, count):
    return [(i, line_offset(rom, i)) for i in range(count)]
