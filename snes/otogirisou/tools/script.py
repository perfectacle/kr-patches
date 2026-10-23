"""Otogirisou script stream parsing (JP Huffman bitstream and KR v1.0 plain 16-bit stream).

Symbols < 0x1000 are characters, 0x1000 + n are control codes. Argument layout per code
comes from the game's own skip table at $00:F41E: low byte = argument count, high byte =
bitmask of arguments that are raw 24-bit jump targets instead of symbols. Count 0x63 is
the choice form. The choice handler ($00:9DAE) reads three symbols and then (c & 7) - 1
raw targets; the skip routine ($00:A99F) reads only two symbols, so it is not followed here.
A raw target of 0 marks a disabled choice.

JP raw targets are bit offsets from the text base $15:E401 (file 0xAE401).
KR v1.0 stores each symbol as 2 bytes big-endian and raw targets as 3-byte little-endian
LoROM addresses (the bit-offset conversion at $02:C087 is bypassed).
"""

JP_TEXT_BASE = 0xAE401
TREE1 = 0x141E1   # $02:C1E1, taken when the bit is 1
TREE0 = 0x14D4F   # $02:CD4F
ROOT = 0x0B6C
ARGTAB = 0x741E   # $00:F41E
ENTRY_TAB = 0x12627  # $02:A627, 3 x 24-bit LoROM bit pointers


def lorom(off):
    return ((off >> 15) << 16) | 0x8000 | (off & 0x7FFF)


def unlorom(addr):
    return ((addr >> 16) & 0x7F) * 0x8000 + (addr & 0x7FFF)


def argspec(rom, code):
    v = rom[ARGTAB + 2 * code] | rom[ARGTAB + 2 * code + 1] << 8
    return v & 0xFF, v >> 8


class JPReader:
    def __init__(self, rom, bitpos):
        self.rom = rom
        self.pos = bitpos  # bit offset from JP_TEXT_BASE

    def bit(self):
        b = (self.rom[JP_TEXT_BASE + (self.pos >> 3)] >> (self.pos & 7)) & 1
        self.pos += 1
        return b

    def sym(self):
        x = ROOT
        while True:
            t = TREE1 if self.bit() else TREE0
            v = self.rom[t + x] | self.rom[t + x + 1] << 8
            if v & 0x8000:
                return v & 0x1FFF
            x = (v & 0x1FFF) * 2

    def raw(self):
        o = JP_TEXT_BASE + (self.pos >> 3)
        v = int.from_bytes(self.rom[o:o + 4], 'little') >> (self.pos & 7)
        self.pos += 24
        return v & 0xFFFFFF


class KRReader:
    def __init__(self, rom, addr):
        self.rom = rom
        self.addr = addr  # LoROM address

    def _inc(self):
        a = self.addr + 1
        if a & 0xFFFF == 0:
            a += 0x8000
        self.addr = a

    def byte(self):
        b = self.rom[unlorom(self.addr)]
        self._inc()
        return b

    def sym(self):
        hi = self.byte()
        lo = self.byte()
        return ((hi << 8) | lo) & 0x1FFF

    def raw(self):
        v = 0
        for i in range(3):
            v |= self.byte() << (8 * i)
        return v

    @property
    def pos(self):
        return self.addr


def read_op(rom, rd):
    """Read one item. Returns (pos, sym, args) where args is a list of ('s', v) / ('r', v)."""
    p = rd.pos
    s = rd.sym()
    args = []
    if s >= 0x1000:
        code = s & 0xFFF
        n, mask = argspec(rom, code)
        if n == 0x63:
            c = rd.sym()
            args.append(('s', c))
            args.append(('s', rd.sym()))
            args.append(('s', rd.sym()))
            for _ in range((c & 7) - 1):
                args.append(('r', rd.raw()))
        else:
            for i in range(n):
                if mask >> i & 1:
                    args.append(('r', rd.raw()))
                else:
                    args.append(('s', rd.sym()))
    return p, s, args
