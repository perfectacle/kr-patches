"""Check Korean item names drawn by the patch in a field-menu dump.

usage: verify_menu.py DUMPDIR ID [ID ...]
DUMPDIR must hold end.vram / end.wram from tools/run_seq.sh.
IDs are the item ids expected in the list (hex), in inventory order.

1. Every slot listed in the WRAM slot table must hold, in VRAM, the outlined
   form of its glyph (body pixels == glyph pixels).
2. The BG1 tilemap is decoded back to text and every expected name must appear.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLOT_VRAM = 0x6000
SLOT_TILE = 0x200
FONT_VRAM = 0x2000
WRAM_TABLE = 0x0C40
WRAM_CNT2 = 0x0C00


def tile_body(vram, tile):
    """Rows of pixels whose 2bpp value is 1 (glyph body) for a 4bpp BG1 tile."""
    base = FONT_VRAM + tile * 32
    rows = []
    for y in range(8):
        lo, hi = vram[base + y * 2], vram[base + y * 2 + 1]
        rows.append(lo & ~hi & 0xFF)
    return rows


def main():
    d = Path(sys.argv[1])
    ids = [int(x, 16) for x in sys.argv[2:]]
    vram = (d / 'end.vram').read_bytes()
    wram = (d / 'end.wram').read_bytes()
    rom = (ROOT / 'build/test.sfc').read_bytes()
    offs = (ROOT / 'build/glyph_offs.bin').read_bytes()
    glyph_at = lambda g: 0x242B00 + int.from_bytes(offs[g * 2:g * 2 + 2], 'little')
    gidx = {}
    for line in (ROOT / 'build/glyphs.txt').read_text(encoding='utf-8').splitlines():
        i, ch = line.split()
        gidx[int(i, 16)] = ch
    static = {}
    for line in (ROOT / 'data/tbl/korTBL2.utf8.tbl').read_text(encoding='utf-8').splitlines():
        m = re.match(r'([0-9A-Fa-f]{2})=(.)$', line)
        if m:
            static[int(m.group(1), 16)] = m.group(2)
    names = {int(x['id_hex'], 16): x['ko'].replace(' ', '') for x in json.loads((ROOT / 'data/items_ko.json').read_text())}
    for h, ko in json.loads((ROOT / 'data/name_overrides.json').read_text())['item'].items():
        names[int(h, 16)] = ko

    errors = 0
    cnt = int.from_bytes(wram[WRAM_CNT2:WRAM_CNT2 + 2], 'little') // 2
    slots = [int.from_bytes(wram[WRAM_TABLE + s * 2:WRAM_TABLE + s * 2 + 2], 'little') for s in range(cnt)]
    for s, g in enumerate(slots):
        want = [rom[glyph_at(g) + y * 2] for y in range(12)]
        # The outline routine draws the glyph one row lower to leave room for the top edge.
        got = (tile_body(vram, SLOT_TILE + s * 2) + tile_body(vram, SLOT_TILE + s * 2 + 1))[1:13]
        if want != got:
            errors += 1
            print(f'slot {s:3d} glyph {g:03X} {gidx.get(g)}: VRAM bitmap mismatch')
    print(f'slots in use: {cnt}, bitmap mismatches: {errors}')

    def cell_char(entry):
        t = entry & 0x3FF
        if t >= SLOT_TILE:
            s = (t - SLOT_TILE) // 2
            return gidx.get(slots[s], '?') if s < cnt else '#'
        return static.get(t // 2 + 0x20, '?')

    # The list is built in the WRAM tilemap buffer at $7E:6000 (32 cells per row)
    # and only the visible part is in VRAM, so decode the buffer.
    text = []
    for row in range(128):
        line = ''
        for col in range(32):
            off = 0x6000 + (row * 32 + col) * 2
            e = wram[off] | wram[off + 1] << 8
            line += cell_char(e) if e & 0x3FF else '\0'
        text.append(line)
    blob = '\n'.join(text)
    missing = 0
    for i in ids:
        n = names.get(i)
        if n and n not in blob:
            missing += 1
            print(f'{i:02X} {n}: not found on BG1')
    print(f'names checked: {len(ids)}, missing: {missing}')
    sys.exit(1 if errors or missing else 0)


if __name__ == '__main__':
    main()
