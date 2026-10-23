"""Test-only ROM variants that send one room exit somewhere else, so a cutscene
can be reached the way the game reaches it (proper room and arrival point).

usage: scene_rom.py NAME
Writes build/scene_<NAME>.sfc (this patch) and build/scene_<NAME>_v1.sfc (V1.0).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# name: (ROM offset of the exit record, original bytes, replacement bytes)
SCENES = {
    # Bandit's Way 3 (room 77): its exit to area 2 leads to area 5 (room 206)
    # at the point where area 4's exit arrives (5, 66, z 0, facing southeast).
    'bw5': (0x1D34E2, 'CF A0 92 7C 00 1A 52 60 81', 'CE A0 92 7C 00 05 42 20 81'),
    # Bandit's Way 3's exit to area 2 leads to Moleville (room 108), arriving
    # next to the bucket girl (3, 62) at (3, 64, z 1) facing north, so A talks to her.
    'molev': (0x1D34E2, 'CF A0 92 7C 00 1A 52 60 81', '6C A0 92 7C 00 03 40 C1 81'),
}
# Moleville NPCs (room 108): arrive two steps south of the NPC facing north.
for npc, (x, y, z) in {'n0': (18, 47, 4), 'n2': (19, 39, 12), 'n4': (10, 76, 0), 'n5': (25, 54, 2)}.items():
    SCENES[f'molev_{npc}'] = (0x1D34E2, 'CF A0 92 7C 00 1A 52 60 81',
                              f'6C A0 92 7C 00 {x:02X} {y + 2:02X} {0xC0 | z:02X} 81')

# Other rooms, arriving two steps south of an NPC facing north: (room, x, y, z).
for key, (room, x, y, z) in {'castle_toad': (0x14, 3, 63, 0)}.items():
    SCENES[key] = (0x1D34E2, 'CF A0 92 7C 00 1A 52 60 81',
                   f'{room & 0xFF:02X} {0xA0 | room >> 8:02X} 92 7C 00 {x:02X} {y + 2:02X} {0xC0 | z:02X} 81')

name = sys.argv[1]
at, old, new = SCENES[name]
for src, dst in ((ROOT / 'build/smrpg_kr_item.sfc', ROOT / f'build/scene_{name}.sfc'),
                 (ROOT / 'rom/smrpg_kr_v1.sfc', ROOT / f'build/scene_{name}_v1.sfc')):
    rom = bytearray(src.read_bytes())
    assert rom[at:at + 9] == bytes.fromhex(old), f'{src.name}: exit record moved'
    rom[at:at + 9] = bytes.fromhex(new)
    dst.write_bytes(rom)
    print(dst.relative_to(ROOT))
