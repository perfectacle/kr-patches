"""시험용 롬: 「처음부터」가 다른 스테이지(와 그 안의 장면)에서 시작하도록 바꾼다.

    stage_rom.py IN.nds OUT.nds 06 [game004]
route.xml 의 시작 경로 st01/st01_root.xml 을 stNN/stNN_root.xml 로 바꾸고, 장면을 주면 그
스테이지 루트가 처음 부르는 장면 파일 이름을 주어진 장면으로 바꾼다(이름 길이가 같아야 함).
배포용이 아니다. 뒤쪽 장면을 에뮬레이터로 확인할 때만 쓴다. 앞 장면을 건너뛰므로 진행 상태
(아이템·플래그)는 실제 플레이와 다를 수 있다.
"""
import struct
import sys

from kr_patch import lz11
from kr_patch.nds.rom import Rom, rebuild


def swap(rom, path, old, new):
    fid = rom.find(path)
    data, _ = lz11.decompress(rom.file(fid))
    if data.count(old) < 1 or len(new) != len(old):
        raise SystemExit(f"{path}: cannot replace {old!r} with {new!r}")
    return fid, lz11.compress(data.replace(old, new, 1))


def first_scene(rom, st):
    data, _ = lz11.decompress(rom.file(rom.find(f"st{st}/st{st}_root.xml.lz")))
    h = struct.unpack_from("<4s12I", data, 0)
    names = [x for x in data[0x34 + h[2]:0x34 + h[2] + h[3]].split(b"\0") if x.endswith(b".xml")]
    return names[0]


if __name__ == "__main__":
    src, dst, st = sys.argv[1:4]
    rom = Rom(open(src, "rb").read())
    files = dict([swap(rom, "route.xml.lz", b"st01/st01_root.xml", f"st{st}/st{st}_root.xml".encode())])
    if len(sys.argv) > 4:
        old = first_scene(rom, st)
        new = f"st{st}/st{st}_{sys.argv[4]}_Expand.xml".encode()
        files.update([swap(rom, f"st{st}/st{st}_root.xml.lz", old, new)])
    open(dst, "wb").write(rebuild(rom, files))
    print(dst)
