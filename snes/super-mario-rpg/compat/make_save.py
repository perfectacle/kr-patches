"""Put Yoshi Cookies in the first item slots of save slot 1 and fix its checksum.

usage: make_save.py IN.srm OUT.srm [count]

Slot 1 is $0000-$07FF of the 32KB save RAM; its first bytes are a copy of
$7F:F800 (stats), so the item inventory ($7F:F882) is at $0082. The word at
$07FC is the complement of the 16-bit sum of $0000-$07FB; a slot whose sum
does not match is shown as empty.
"""
import struct
import sys

YOSHI_COOKIE = 0x6D

s = bytearray(open(sys.argv[1], 'rb').read())
for i in range(int(sys.argv[3]) if len(sys.argv) > 3 else 6):
    s[0x82 + i] = YOSHI_COOKIE
struct.pack_into('<H', s, 0x7FC, ~sum(s[:0x7FC]) & 0xFFFF)
open(sys.argv[2], 'wb').write(s)
