"""Binary fixes on top of the v1.0 ROM, applied in place: fixes.py rom.sfc"""
import sys

rom = bytearray(open(sys.argv[1], "rb").read())

# Scenario start table $02:A627 (3 x 24-bit). v1.0 relocated entries 0 and 1 to the
# plain-text stream but left entry 2 as the JP Huffman bit pointer, which the patched
# reader takes as byte address $C5:4BC0. Entry 2 is drawn at random from the second
# playthrough on, so the game froze there. $25:E6A4 is where JP block 2 starts in v1.0.
ENTRY2 = 0x1262D
assert rom[ENTRY2:ENTRY2 + 3] in (b"\xc0\x4b\xc5", b"\xa4\xe6\x25")
rom[ENTRY2:ENTRY2 + 3] = b"\xa4\xe6\x25"

# v1.0 doubled the ROM to 2MB without updating the header size byte.
rom[0x7FD7] = 0x0B

open(sys.argv[1], "wb").write(rom)
