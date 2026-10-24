"""타이틀 화면에서 v1.1 이 넣은 안내·제작자 문구를 지운다.

    title.py JP.nds BASE.nds OUT.png   (지운 타이틀을 PNG 로 미리 보기)

타이틀 상단 화면은 cpac_3d.bin 묶음 0 의 461번 항목(LZ11 로 압축한 sdt. 그림, 256×192 8bpp,
팔레트 256색)이다. v1.1 은 이 그림의 137–177줄에 「이 한글패치는 비영리 목적으로…」 두 줄과
「©KOREAN PATCHED BY …」 한 줄을 그려 넣었다. 그 줄들을 일본판 같은 그림의 픽셀로 되돌린다.
일본판 색은 v1.1 팔레트에 모두 그대로 있어 같은 색의 번호로 바꾼다. 새 압축 바이트가 원래 칸보다
작으므로 다른 항목은 옮기지 않고 그 칸에 다시 쓴다(크기 칸만 고치고 남는 곳은 0).
"""
import struct
import sys

from kr_patch import lz11

CPAC = "cpac_3d.bin"
SECTION, ENTRY = 0, 461
ROWS = range(137, 178)
WIDTH, PIXELS, PALETTE = 256, 0x24, 0xC024


def _entry(cpac):
    """(묶음 시작, 표 칸 위치, 데이터 위치, 크기 칸 값)"""
    sec = struct.unpack_from("<I", cpac, SECTION * 8)[0]
    assert cpac[sec + 8:sec + 12] == b"YEKB", "cpac_3d 묶음 형식이 다름"
    base = struct.unpack_from("<I", cpac, sec + 0x14)[0]
    slot = sec + 0x20 + ENTRY * 8
    off, size = struct.unpack_from("<II", cpac, slot)
    return slot, sec + base + off, size


def _image(cpac):
    slot, at, size = _entry(cpac)
    data = lz11.decompress(cpac[at:at + (size & 0xFFFFFF)])[0]
    assert data[:4] == b"sdt." and struct.unpack_from("<II", data, 0x1C) == (256, 192), "타이틀 그림이 아님"
    return data


def clean(jp_cpac, kr_cpac):
    """문구를 지운 cpac_3d.bin 바이트."""
    j, k = _image(jp_cpac), bytearray(_image(kr_cpac))
    pal_j = struct.unpack_from("<256H", j, PALETTE)
    pal_k = struct.unpack_from("<256H", k, PALETTE)
    index = {c: i for i, c in reversed(list(enumerate(pal_k)))}
    for y in ROWS:
        for x in range(WIDTH):
            o = PIXELS + y * WIDTH + x
            k[o] = index[pal_j[j[o]]]
    packed = lz11.compress(bytes(k))
    slot, at, size = _entry(kr_cpac)
    room = size & 0xFFFFFF
    assert len(packed) <= room, f"압축 결과 {len(packed)} 바이트가 원래 칸 {room} 바이트보다 큼"
    out = bytearray(kr_cpac)
    out[at:at + room] = packed + bytes(room - len(packed))
    struct.pack_into("<I", out, slot + 4, (size & 0xFF000000) | len(packed))
    return bytes(out)


if __name__ == "__main__":
    from pathlib import Path

    from kr_patch.nds.rom import Rom
    from PIL import Image

    jp, kr = (Rom(Path(p).read_bytes()) for p in sys.argv[1:3])
    data = _image(clean(jp.file(jp.find(CPAC)), kr.file(kr.find(CPAC))))
    pal = struct.unpack_from("<256H", data, PALETTE)
    rgb = [((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31) for c in pal]
    im = Image.new("RGB", (256, 192))
    im.putdata([rgb[b] for b in data[PIXELS:PIXELS + 256 * 192]])
    im.save(sys.argv[3])
