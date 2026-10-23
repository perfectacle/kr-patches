"""LZSS codec used by the game's decompressor at $80:9CFA.

Stream: u16 output size, then groups of 8 items led by a flag byte (LSB first).
Flag 1: literal byte. Flag 0: u16 LE word, length = (word & 0xF) + 3,
source position = out_pos - (word >> 4); positions before 0 read as zero.
The $80:9DA7 variant then re-interleaves each 16-byte tile from planar halves
(plane0 rows 0-7, plane1 rows 0-7) into SNES 2bpp row order.
"""


def decompress(rom, off):
    size = rom[off] | rom[off + 1] << 8
    i = off + 2
    out = bytearray()
    flags = bits = 0
    while len(out) < size:
        if bits == 0:
            flags = rom[i]; i += 1; bits = 8
        bits -= 1
        bit = flags & 1; flags >>= 1
        if bit:
            out.append(rom[i]); i += 1
        else:
            w = rom[i] | rom[i + 1] << 8; i += 2
            n = (w & 0xF) + 3
            src = len(out) - (w >> 4)
            for _ in range(n):
                out.append(out[src] if src >= 0 else 0)
                src += 1
    return bytes(out[:size]), i - off


def compress(data):
    """Greedy LZSS with a hash-free brute-force search (inputs are small)."""
    out = bytearray([len(data) & 0xFF, len(data) >> 8])
    pos = 0
    n = len(data)
    while pos < n:
        flag_at = len(out); out.append(0)
        flags = 0
        for bit in range(8):
            if pos >= n:
                break
            best_len, best_dist = 0, 0
            maxlen = min(18, n - pos)
            for dist in range(1, min(pos, 0xFFF) + 1):
                s = pos - dist
                l = 0
                while l < maxlen and data[s + l] == data[pos + l]:
                    l += 1
                if l > best_len:
                    best_len, best_dist = l, dist
                    if l == maxlen:
                        break
            # Zero run before start of buffer (virtual zeros at negative positions).
            if best_len < maxlen and pos < 0xFFF:
                l = 0
                while l < maxlen and data[pos + l] == 0 and l < 0xFFF - pos + l:
                    l += 1
                dist = pos + 1  # src = -1, ... reads zeros then data[0..]
                lz = 0
                src = pos - dist
                while lz < maxlen:
                    v = data[src + lz] if src + lz >= 0 else 0
                    if v != data[pos + lz]:
                        break
                    lz += 1
                if dist <= 0xFFF and lz > best_len:
                    best_len, best_dist = lz, dist
            if best_len >= 3:
                w = (best_dist << 4) | (best_len - 3)
                out += bytes([w & 0xFF, w >> 8])
                pos += best_len
            else:
                flags |= 1 << bit
                out.append(data[pos])
                pos += 1
        out[flag_at] = flags
    return bytes(out)


def planar_to_snes(data):
    out = bytearray(len(data))
    for t in range(0, len(data), 16):
        for r in range(8):
            out[t + r * 2] = data[t + r]
            out[t + r * 2 + 1] = data[t + 8 + r]
    return bytes(out)


def snes_to_planar(data):
    out = bytearray(len(data))
    for t in range(0, len(data), 16):
        for r in range(8):
            out[t + r] = data[t + r * 2]
            out[t + 8 + r] = data[t + r * 2 + 1]
    return bytes(out)
