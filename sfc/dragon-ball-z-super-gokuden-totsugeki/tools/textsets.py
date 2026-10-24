"""Pointer-table text sets besides dialogue. Each table holds 16-bit pointers into its own bank."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dialogue1 import off, words  # noqa: E402

SETS = {  # name: (bank, table address, count)
    "battle": (0xB1, 0x9C34, 769),
    "event": (0xAD, 0x8000, 204),
    "choice": (0xA9, 0x8000, 117),
    "minigame": (0x98, 0x8000, 56),
    "place": (0x87, 0x8000, 100),
    "map": (0x82, 0xB306, 0x36),
    "tech": (0x84, 0xB605, None),
    "advice": (0x9F, 0x8000, None),  # rival/partner/advisor comments
    "enemy": (0xAE, 0xC910, 55),  # enemy names in battle
    # Save point talk: pointers are LDA # operands in bank 81 (file offsets).
    "save": (0x81, [0xD85A, 0xD860, 0xD8C1, 0xD86E, 0xD874, 0xD882,
                    0xD6AE, 0xD6BF, 0xD6D0, 0xD6E1, 0xD6F2, 0xDA23], None),
}


def pointers(rom, name):
    bank, table, n = SETS[name]
    if isinstance(table, list):
        return [(o, rom[o] | rom[o + 1] << 8) for o in table]
    t = off(bank, table)
    if n is None:  # table runs until the first string
        first = rom[t] | rom[t + 1] << 8
        n = (first - table) // 2
    return [(t + 2 * i, rom[t + 2 * i] | rom[t + 2 * i + 1] << 8) for i in range(n)]


def strings(rom, name):
    bank = SETS[name][0]
    return [(slot, p, off(bank, p), words(rom, off(bank, p))) for slot, p in pointers(rom, name)]
