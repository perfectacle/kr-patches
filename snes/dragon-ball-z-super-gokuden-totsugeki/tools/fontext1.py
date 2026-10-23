"""Extra 16x16 glyph slots for codes 0xC00 and up.

The VWF renderer picks a glyph sheet by code range at $B7:9770; codes from
0x7F0 go to $BF:8000. We hook that branch ($B7:97BC) so codes >= 0xC00 look up
a 4 KB block (128 codes, 64 glyphs because odd sheet rows are bottom halves)
in a table of free ROM areas. Width handling already treats every code >= 0x500
as a 13 px glyph, so nothing else needs to change.
"""

HOOK = 0x1B97BC          # $B7:97BC, start of the $BF sheet branch
ROUTINE = 0xFA00         # $B7:FA00 (free 0xFF area)
FIRST = 0xC00
PER_BLOCK = 0x80
# (bank, address) of each 4 KB block; all 0xFF in the Japanese ROM and v1.0.
BLOCKS = [(0x81, 0xEF00), (0x84, 0xEE00), (0x86, 0xE000), (0x86, 0xF000),
          (0xA6, 0xE600), (0xAE, 0xEA00), (0xB1, 0xE500), (0xB6, 0xE600)]


def off(bank, addr):
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def routine():
    base_tab = ROUTINE + 0x60
    bank_tab = base_tab + 2 * len(BLOCKS)
    lo = lambda a: [a & 0xFF, a >> 8]  # noqa: E731
    code = []
    code += [0xC9] + lo(FIRST)                 # CMP #$0C00
    code += [0xB0, 0x1E]                       # BCS ext
    # original $BF branch
    code += [0x38, 0xE9, 0xF0, 0x07]           # SEC / SBC #$07F0
    code += [0x85, 0x2E]                       # STA $2E
    code += [0x0A] * 5                         # ASL x5 (32 bytes per code)
    code += [0x85, 0x26]                       # STA $26
    code += [0xE2, 0x20, 0xA9, 0xBF, 0x48, 0xAB, 0xC2, 0x20]   # DB = $BF
    code += [0xA9, 0x00, 0x80, 0x85, 0x4F]     # $4F = $8000
    code += [0x5C, 0xD6, 0x97, 0xB7]           # JML $B797D6
    assert len(code) == 0x23
    # ext:
    code += [0x38, 0xE9] + lo(FIRST)           # SEC / SBC #$0C00
    code += [0x85, 0x2E, 0x48]                 # STA $2E / PHA
    code += [0x29, PER_BLOCK - 1, 0x00]        # AND #$007F
    code += [0x0A] * 5 + [0x85, 0x26]          # offset in block -> $26
    code += [0x68] + [0x4A] * 7 + [0x0A]       # PLA / block * 2
    code += [0xDA, 0xAA]                       # PHX / TAX
    code += [0xBF] + lo(base_tab) + [0xB7]     # LDA base_tab,X
    code += [0x85, 0x4F, 0x8A, 0x4A, 0xAA]     # STA $4F / TXA / LSR / TAX
    code += [0xE2, 0x20]                       # SEP #$20
    code += [0xBF] + lo(bank_tab) + [0xB7]     # LDA bank_tab,X
    code += [0x48, 0xAB, 0xC2, 0x20, 0xFA]     # PHA / PLB / REP #$20 / PLX
    code += [0x5C, 0xD6, 0x97, 0xB7]           # JML $B797D6
    assert len(code) <= 0x60
    code += [0xFF] * (0x60 - len(code))
    for b, a in BLOCKS:
        code += lo(a)
    code += [b for b, _ in BLOCKS]
    return bytes(code)


def install(rom):
    o = off(0xB7, ROUTINE)
    data = routine()
    if any(x != 0xFF for x in rom[o:o + len(data)]) and rom[o:o + len(data)] != data:
        raise SystemExit("fontext1: routine area is not free")
    rom[o:o + len(data)] = data
    rom[HOOK:HOOK + 4] = bytes([0x5C, ROUTINE & 0xFF, ROUTINE >> 8, 0xB7])


def codes():
    for b in range(len(BLOCKS)):
        for k in range(PER_BLOCK):
            if (k // 8) % 2 == 0:
                yield FIRST + b * PER_BLOCK + k


def glyph_offset(code):
    i = code - FIRST
    bank, addr = BLOCKS[i // PER_BLOCK]
    return off(bank, addr) + (i % PER_BLOCK) * 32
