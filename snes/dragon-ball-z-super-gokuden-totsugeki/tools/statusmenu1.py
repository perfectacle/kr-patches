"""Story-status screen fixes that need code: two-glyph list marks and a stale string pointer.

usage: statusmenu1.py rom.smc table.txt

The technique list ($80:40BC) and the event list ($80:3D83) write one glyph in
front of each row: 0x0BA0 / 0x0BA1 (v1.0 squeezed 습득 / 완료 into one 16x16
glyph) or the blank 0x0AD5. Each site is replaced by a JSL to a routine in the
free tail of bank B7 that writes two 16 px glyphs (or two blanks) and a narrow
gap. Both rows are 224 px windows; the gap is chosen so the longest row still
fits (technique 224 px, event 223 px with the 4- and 7-px spacers).

v1.0 moved the category list of the technique menu to $80:B599 and updated the
operand at $80:AAD5 but left the second user at $80:D803 pointing at $B5A3.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402
import kr1  # noqa: E402

ROUTINE = 0x1BFB00  # $B7:FB00, 0xFF in the Japanese ROM and in every earlier release
BLANK = 0x0AD5      # empty 16x16 glyph the game uses for "not yet"
TECH_SITE = 0x40BC  # BNE / LDA #$0AD5 / BRA / LDA #$0BA0 / STA $0A00,Y ... up to $80:40D3
TECH_OLD = bytes.fromhex("d005a9d50a8003a9a00b99000ac8c8a9c50299000ac8c8")
EVENT_SITE = 0x3D83  # same pattern, then TYX and a second space through X, up to $80:3DA3
EVENT_OLD = bytes.fromhex("d005a9d50a8003a9a10b99000ac8c8a9c50299000ac8c8bba9c5029d000ae8e8")
CATEGORY_OPERAND = 0x5804  # LDA #$B5A3 at $80:D803


def w16(v):
    return [v & 0xFF, v >> 8]


def mark_routine(first, second, gap, tail):
    """BNE set; write BLANK twice; BRA; set: write first, second; then gap; RTL.
    Entered with the Z flag of the earlier AND, A 16-bit, Y = row write index."""
    put = lambda v: [0xA9] + w16(v) + [0x99, 0x00, 0x0A, 0xC8, 0xC8]  # noqa: E731  LDA #v / STA $0A00,Y / INY INY
    blank = [0xA9] + w16(BLANK) + [0x99, 0x00, 0x0A, 0xC8, 0xC8, 0x99, 0x00, 0x0A, 0xC8, 0xC8]
    done = put(first) + put(second)
    code = [0xD0, len(blank) + 2] + blank + [0x80, len(done)] + done + put(gap) + tail
    return bytes(code)


def main():
    rom = bytearray(open(sys.argv[1], "rb").read())
    enc = kr1.Encoder(D.load_table(sys.argv[2]))
    code = enc.code

    assert rom[TECH_SITE:TECH_SITE + len(TECH_OLD)] == TECH_OLD, "technique list site differs"
    assert rom[EVENT_SITE:EVENT_SITE + len(EVENT_OLD)] == EVENT_OLD, "event list site differs"
    assert rom[CATEGORY_OPERAND - 1:CATEGORY_OPERAND + 2] == bytes.fromhex("a9a3b5"), "category operand differs"

    tech = mark_routine(code("습"), code("득"), code("{sp4}"), [0x6B])
    event = mark_routine(code("완"), code("료"), code("{sp7}"), [0x6B])
    end = ROUTINE + len(tech) + len(event)
    assert all(b == 0xFF for b in rom[ROUTINE:end]), "routine area is not free"
    rom[ROUTINE:ROUTINE + len(tech)] = tech
    rom[ROUTINE + len(tech):end] = event
    tech_addr = 0x8000 | (ROUTINE & 0x7FFF)
    event_addr = tech_addr + len(tech)

    # JSL routine, then BRA to the instruction after the old site.
    site = [0x22] + w16(tech_addr) + [0xB7]
    site += [0x80, len(TECH_OLD) - len(site) - 2]
    rom[TECH_SITE:TECH_SITE + len(TECH_OLD)] = bytes(site).ljust(len(TECH_OLD), b"\xea")
    # The event row continues through X, so copy the index after the routine.
    site = [0x22] + w16(event_addr) + [0xB7, 0xBB]
    site += [0x80, len(EVENT_OLD) - len(site) - 2]
    rom[EVENT_SITE:EVENT_SITE + len(EVENT_OLD)] = bytes(site).ljust(len(EVENT_OLD), b"\xea")

    rom[CATEGORY_OPERAND] = 0x99  # $B5A3 -> $B599

    open(sys.argv[1], "wb").write(rom)
    print(f"status marks: $B7:{tech_addr:04X} ({len(tech)} bytes), $B7:{event_addr:04X} ({len(event)} bytes)")


if __name__ == "__main__":
    main()
