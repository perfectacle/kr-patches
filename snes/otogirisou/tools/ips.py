"""Create or apply IPS patches.

usage: ips.py make original.smc modified.smc out.ips
       ips.py apply original.smc patch.ips out.smc
"""
import sys

EOF_OFF = 0x454F46  # "EOF" as an offset would be read as the end marker


def make(a, b):
    assert len(b) >= len(a) and len(b) <= 0x1000000
    out = bytearray(b"PATCH")
    i, n = 0, len(b)
    while i < n:
        if i < len(a) and a[i] == b[i]:
            i += 1
            continue
        start = i if i != EOF_OFF else i - 1
        end = i
        # Extend over short equal gaps: a new record costs 5 bytes of header.
        while end < n and end - start < 0xFFFF:
            if end >= len(a) or a[end] != b[end]:
                end += 1
                continue
            gap = end
            while gap < n and gap - end < 6 and gap < len(a) and a[gap] == b[gap]:
                gap += 1
            if gap - end >= 6 or gap >= n:
                break
            end = gap
        end = min(end, start + 0xFFFF)
        out += start.to_bytes(3, "big") + (end - start).to_bytes(2, "big") + b[start:end]
        i = end
    out += b"EOF"
    if len(b) > len(a):
        out += len(b).to_bytes(3, "big")
    return bytes(out)


def apply(a, p):
    assert p[:5] == b"PATCH"
    r = bytearray(a)
    i = 5
    while p[i:i + 3] != b"EOF":
        off = int.from_bytes(p[i:i + 3], "big")
        size = int.from_bytes(p[i + 3:i + 5], "big")
        i += 5
        if size == 0:
            rle = int.from_bytes(p[i:i + 2], "big")
            data = p[i + 2:i + 3] * rle
            i += 3
        else:
            data = p[i:i + size]
            i += size
        if off + len(data) > len(r):
            r.extend(b"\0" * (off + len(data) - len(r)))
        r[off:off + len(data)] = data
    if len(p) >= i + 6:
        r = r[:int.from_bytes(p[i + 3:i + 6], "big")]
    return bytes(r)


if __name__ == "__main__":
    cmd, x, y, z = sys.argv[1:5]
    rd = lambda f: open(f, "rb").read()
    if cmd == "make":
        open(z, "wb").write(make(rd(x), rd(y)))
    else:
        open(z, "wb").write(apply(rd(x), rd(y)))
