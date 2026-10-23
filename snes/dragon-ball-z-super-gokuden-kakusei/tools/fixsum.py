"""Recompute the LoROM header checksum in place: fixsum.py rom.smc"""
import sys

rom = bytearray(open(sys.argv[1], "rb").read())
rom[0x7FDC:0x7FE0] = b"\xff\xff\x00\x00"   # complement/checksum bytes always sum to 0x1FE
s = sum(rom) & 0xFFFF
rom[0x7FDC:0x7FE0] = bytes([~s & 0xFF, (~s >> 8) & 0xFF, s & 0xFF, s >> 8])
open(sys.argv[1], "wb").write(rom)
print(f"checksum {s:04X}")
