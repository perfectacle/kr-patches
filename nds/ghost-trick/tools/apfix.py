"""실기·플래시카드에서 대사가 안 나오게 하는 안티 파이러시(AP) 루틴을 끈다.

    apfix.py ROM.nds   (오버레이 0 에 이미 들어 있는지, 넣을 수 있는지 출력)

nds-bootstrap(TWiLight Menu++)은 일본판 롬을 띄울 때 retail/apfix/files/BGTJ-C8CD.ips 를 메모리에서
적용해 이 루틴을 끈다. 그 IPS 는 헤더 CRC16(0x15E)이 C8CD 인 롬에만 쓰이는데, 한글패치는 롬을 다시
묶어 헤더 CRC16 이 바뀌므로 적용되지 않는다. no$gba 도 같은 증상(대사·지문·선택지·말풍선이 빈 창)을
보인다. 그래서 같은 수정을 롬에 직접 넣는다.

IPS 는 일본판 롬 오프셋 0x84A9E·0x84B49 를 고치는데, 둘 다 오버레이 0 파일(BLZ 압축, 일본판 롬
0x84A00) 안이다. 한글판의 오버레이 0 은 일본판과 바이트 단위로 같고 위치만 옮겨 가므로, 롬 오프셋이
아니라 파일 안 위치로 적용한다. 압축 바이트를 고치는 수정이라 풀면 네 곳(0x6E·0x119·0x1C2·0x26D 부근)이
바뀐다.
"""
import sys

OVERLAY = 0
JP_FILE_OFFSET = 0x84A00
# (일본판 롬 오프셋, 원래 바이트, 고친 바이트): BGTJ-C8CD.ips 의 두 레코드
RECORDS = (
    (0x84A9E, bytes.fromhex("aae0"), bytes.fromhex("a939")),
    (0x84B49, bytes.fromhex("bfaae0"), bytes.fromhex("beaa36")),
)


def patch(overlay):
    """오버레이 0 파일에 AP 수정을 넣은 바이트. 이미 들어 있으면 그대로, 다른 파일이면 ValueError."""
    out = bytearray(overlay)
    for rom_off, old, new in RECORDS:
        at = rom_off - JP_FILE_OFFSET
        cur = bytes(out[at:at + len(old)])
        if cur == new:
            continue
        if cur != old:
            raise ValueError(f"overlay 0 +{at:#x}: {cur.hex()} (expected {old.hex()} or {new.hex()})")
        out[at:at + len(new)] = new
    return bytes(out)


if __name__ == "__main__":
    from kr_patch.nds.rom import Rom
    rom = Rom(open(sys.argv[1], "rb").read())
    fid = rom.overlay_files()[f"overlay9/overlay_{OVERLAY:04d}.bin"]
    ov = rom.file(fid)
    print("already patched" if patch(ov) == ov else "not patched (can be patched)")
