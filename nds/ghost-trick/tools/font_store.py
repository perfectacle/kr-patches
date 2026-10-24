"""대사 폰트(fonts2bpp_new.imb)를 krpatch 글리프 저장소(JSON)로.

16x24, 2bpp, 한 줄 4바이트. 바이트 하나에 픽셀 4개: 상위 니블이 앞 두 픽셀,
니블 안에서는 하위 2비트가 먼저다(비트 위치 4,6,0,2).
"""
import sys

from kr_patch.glyph import store

W, H, SIZE = 16, 24, 96
SHIFT = (4, 6, 0, 2)


def decode(data, i):
    o = i * SIZE
    return [[(data[o + y * 4 + x // 4] >> SHIFT[x % 4]) & 3 for x in range(W)] for y in range(H)]


def encode(pix):
    out = bytearray(SIZE)
    for y in range(H):
        for x in range(W):
            out[y * 4 + x // 4] |= (pix[y][x] & 3) << SHIFT[x % 4]
    return bytes(out)


def glyphs(data, start=0, count=None):
    n = len(data) // SIZE
    count = n - start if count is None else count
    return {f"{i:04x}": [[1 if v else 0 for v in row] for row in decode(data, i)] for i in range(start, start + count)}


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    g = glyphs(data, int(sys.argv[3], 0) if len(sys.argv) > 3 else 0, int(sys.argv[4]) if len(sys.argv) > 4 else None)
    store.save(sys.argv[2], g)
    print(len(g))
