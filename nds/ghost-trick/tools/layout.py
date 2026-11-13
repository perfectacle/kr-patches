"""롬을 일본판과 같은 순서로, 영역마다 0x200 경계에 다시 놓는다.

    layout.relayout(JP 바이트, 롬 바이트) -> 새 롬 바이트

v1.1 은 다른 도구로 다시 묶여 ARM7·FNT·FAT·배너와 파일 대부분이 0x200 경계에 있지 않고,
ARM9 뒤 12바이트(nitrocode 꼬리)도 없다. 펌웨어(BIOS) 부팅은 카드에서 ARM7 을 0x200 단위로
읽는데, 카드는 0x1000 페이지 경계를 넘는 읽기를 페이지 처음으로 되감는다. 그래서 정렬되지
않은 ARM7 이 깨진 채 올라가 흰 화면에서 멈춘다. 다이렉트 부팅은 에뮬레이터가 롬에서 바로
복사해 문제가 드러나지 않는다.

일본판의 영역 순서(ARM9, 오버레이 표, 파일, ARM7, FNT, FAT, 배너, 나머지 파일)를 따르고,
ARM9 은 0x4000 그대로, 나머지는 앞 영역 끝 다음 0x200 경계에 둔다. 사이는 일본판처럼 0xFF.
ARM9 꼬리는 일본판에서 가져온다. 헤더는 오프셋, 사용 크기(0x80), CRC16 만 바뀐다.
"""
import struct

from kr_patch.nds.rom import Rom, crc16

ALIGN = 0x200
FOOTER = 12
FOOTER_MAGIC = 0xDEC00621


def _up(n):
    return -(-n // ALIGN) * ALIGN


def _order(jp):
    """일본판 오프셋 순서의 영역 이름 목록. 파일은 FAT 번호가 아니라 경로로 짝짓는다."""
    paths = {fid: "data/" + n for fid, n in jp.names.items()}
    paths.update({fid: p for p, fid in jp.overlay_files().items()})
    regs = [(jp.arm9[0], "arm9"), (jp.arm7[0], "arm7"), (jp.fnt[0], "fnt"), (jp.fat[0], "fat")]
    regs += [(t[0], n) for t, n in ((jp.ovt9, "ovt9"), (jp.ovt7, "ovt7")) if t[1]]
    if jp.banner:
        regs.append((jp.banner, "banner"))
    regs += [(s, paths[fid]) for fid, (s, e) in enumerate(jp.entries) if e > s]
    return [n for _, n in sorted(regs)]


def relayout(jp_bytes, rom_bytes, banner=None):
    jp, rom = Rom(jp_bytes), Rom(rom_bytes)
    d = rom.data
    fids = {"data/" + n: fid for fid, n in rom.names.items()}
    fids.update(rom.overlay_files())
    footer = jp.data[sum(jp.arm9):sum(jp.arm9) + FOOTER]
    if struct.unpack_from("<I", footer)[0] != FOOTER_MAGIC:
        raise ValueError("no nitrocode footer after the Japanese ARM9")
    blobs = {
        "arm9": d[rom.arm9[0]:sum(rom.arm9)] + footer,
        "arm7": d[rom.arm7[0]:sum(rom.arm7)],
        "fnt": d[rom.fnt[0]:sum(rom.fnt)],
        "fat": d[rom.fat[0]:sum(rom.fat)],
        "ovt9": d[rom.ovt9[0]:sum(rom.ovt9)],
        "ovt7": d[rom.ovt7[0]:sum(rom.ovt7)],
        "banner": banner if banner is not None else d[rom.banner:rom.banner + rom.banner_size()],
    }
    order = _order(jp)
    if sorted(n for n in order if n.startswith(("data/", "overlay"))) != sorted(fids):
        raise ValueError("the ROM and the Japanese ROM have different file lists")
    if any(e <= s for s, e in rom.entries):
        raise ValueError("empty FAT entries are not handled")

    out = bytearray(d[:rom.arm9[0]])
    pos, where = rom.arm9[0], {}
    for name in order:
        blob = blobs[name] if name in blobs else rom.file(fids[name])
        pos = rom.arm9[0] if name == "arm9" else _up(pos)
        out += b"\xFF" * (pos - len(out))
        out += blob
        where[name] = pos
        pos += len(blob)

    fat = where["fat"]
    for path, fid in fids.items():
        struct.pack_into("<II", out, fat + fid * 8, where[path], where[path] + len(rom.file(fid)))
    for off, name in ((0x30, "arm7"), (0x40, "fnt"), (0x48, "fat"), (0x50, "ovt9"), (0x58, "ovt7"), (0x68, "banner")):
        if name in where:
            struct.pack_into("<I", out, off, where[name])
    struct.pack_into("<I", out, 0x80, len(out))
    struct.pack_into("<H", out, 0x15E, crc16(out[:0x15E]))
    return bytes(out)
