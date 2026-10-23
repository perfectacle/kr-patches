"""Write IPS patches from the JP ROM to a patched ROM, for headerless and
headered (512-byte copier header) ROMs, and check that each one reproduces it.

usage: make_ips.py base.sfc patched.sfc out.ips out_headered.ips
"""
import sys
from pathlib import Path

HEADER = 512
MAX_LEN = 0xFFFF
EOF_OFFSET = 0x454F46   # a record at this offset would read as the "EOF" marker
GAP = 6                 # equal bytes shorter than a record header are cheaper to copy


def runs(a, b):
    i, n = 0, len(b)
    while i < n:
        if a[i] == b[i]:
            i += 1
            continue
        j = i
        k = i
        while k < n and k - i < MAX_LEN:
            if a[k] != b[k]:
                j = k + 1
            elif k - j >= GAP:
                break
            k += 1
        yield i, b[i:j]
        i = j


def ips(base, patched, shift):
    out = bytearray(b'PATCH')
    for off, data in runs(base, patched):
        off += shift
        if off == EOF_OFFSET:
            off -= 1
            data = patched[off - shift:off - shift + 1] + data
        out += off.to_bytes(3, 'big') + len(data).to_bytes(2, 'big') + data
    return bytes(out + b'EOF')


def apply(rom, patch):
    r = bytearray(rom)
    i = 5
    while patch[i:i + 3] != b'EOF':
        off = int.from_bytes(patch[i:i + 3], 'big')
        n = int.from_bytes(patch[i + 3:i + 5], 'big')
        r[off:off + n] = patch[i + 5:i + 5 + n]
        i += 5 + n
    return bytes(r)


def main():
    base, patched = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    if len(base) != len(patched):
        sys.exit('ROM sizes differ')
    pad = bytes(HEADER)
    for path, shift, src, want in ((sys.argv[3], 0, base, patched), (sys.argv[4], HEADER, pad + base, pad + patched)):
        p = ips(base, patched, shift)
        if apply(src, p) != want:
            sys.exit(f'{path}: does not reproduce the patched ROM')
        Path(path).write_bytes(p)
        print(f'{path}: {len(p)} bytes')


if __name__ == '__main__':
    main()
