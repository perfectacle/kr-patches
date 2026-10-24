"""Dialogue table of SMRPG (JP layout, as used by the Korean V1.0 patch).

Address of dialogue `id` (see $C0:5800):
  off   = u16 at ROM 0x37E000 + id*2          (offset inside the dialogue's group)
  group = id >> 9                              (512 dialogues per group)
  Starting at bank $E2, each bank begins with a header: u16 header size, then
  u16 group base addresses. Groups that do not fit in a bank's header carry
  over to the next bank ($E3, $E4).
"""
from pathlib import Path

PTR_TABLE = 0x37E000
FIRST_BANK = 0x22
COUNT = 4096


def group_base(rom, group):
    bank = FIRST_BANK
    a = (group * 2) & 0xFFFE
    while True:
        hdr = int.from_bytes(rom[(bank << 16):(bank << 16) + 2], 'little')
        if a < hdr:
            return bank, int.from_bytes(rom[(bank << 16) + a:(bank << 16) + a + 2], 'little')
        a -= hdr
        bank += 1


def address(rom, i):
    off = int.from_bytes(rom[PTR_TABLE + i * 2:PTR_TABLE + i * 2 + 2], 'little')
    bank, base = group_base(rom, i >> 9)
    return (bank << 16) | ((base + off) & 0xFFFF)


def all_addresses(rom):
    return [address(rom, i) for i in range(COUNT)]
