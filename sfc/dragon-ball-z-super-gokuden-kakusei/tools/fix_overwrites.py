"""Undo translated text that was placed over live data at the end of two banks.

usage: fix_overwrites.py original_jp.smc in_kr.smc out.smc

The Korean text was put into what looked like free 0xFF space, but each spot
began a few bytes early and clobbered real data:
  - $83:F3AF: last entry (0xFFFF) of the cutscene actor X-position table
    read at $83:E44F / $83:E755. The actor slid towards x=0x2A5 instead.
  - $88:FFAE: the 0xFFFF terminator of the waypoint record at $88:FFAA and the
    whole record at $88:FFB0 (pointer table at $88:FC80). Map movement read
    text bytes as waypoints, so the moving object wandered off the map.
The original bytes are restored and each text block is shifted past them,
with the pointers that reference the block adjusted by the same amount.
"""
import sys

FIXES = [
    # (block start, block end exclusive, original data end, pointer offsets)
    (0x1F3AF, 0x1F4FF, 0x1F3B3, [0x19009, 0x1900B, 0x1900D, 0x194AB, 0x194C5]),
    (0x47FAE, 0x47FE0, 0x47FB6, [0x4000C, 0x40018, 0x4001C, 0x40048]),
]


def main():
    jp = open(sys.argv[1], "rb").read()
    rom = bytearray(open(sys.argv[2], "rb").read())
    for start, end, data_end, ptrs in FIXES:
        shift = data_end - start
        block = bytes(rom[start:end])
        if rom[start:data_end] == jp[start:data_end]:
            sys.exit(f"{start:#x}: already fixed")
        if any(b != 0xFF for b in rom[end:end + shift]):
            sys.exit(f"{start:#x}: no room to shift the block by {shift}")
        lo, hi = 0x8000 | (start & 0x7FFF), 0x8000 | ((end - 1) & 0x7FFF)
        for p in ptrs:
            v = rom[p] | rom[p + 1] << 8
            if not lo <= v <= hi:
                sys.exit(f"pointer at {p:#x} = {v:04X} is outside the block")
            v += shift
            rom[p], rom[p + 1] = v & 0xFF, v >> 8
        rom[start:data_end] = jp[start:data_end]
        rom[data_end:end + shift] = block
        print(f"{start:#x}: restored {shift} bytes, text moved to {data_end:#x}, {len(ptrs)} pointers")
    open(sys.argv[3], "wb").write(rom)


if __name__ == "__main__":
    main()
