"""BGM 후보 녹음: SDAT 의 시퀀스 정보 레코드를 모두 곡 K 의 것으로 바꾼 시험 롬을 만들어,
「처음부터」 뒤 첫 장면에서 나오는 음악을 녹음한다(어느 곡을 틀든 곡 K 가 나온다).

    bgm_dump.py ROM OUTDIR [K ...] [--quiet]
--quiet 은 효과음(SSAR)을 꺼서 음악만 남긴다.
OUTDIR/NN_이름.wav (44.1kHz 스테레오). K 를 안 주면 모든 곡.
"""
import os
import struct
import subprocess
import sys
from pathlib import Path

from kr_patch.nds.rom import Rom, rebuild

HERE = Path(__file__).resolve().parent
SDAT = "sound_data.sdat"
# 부팅 → 타이틀 → 처음부터 → 첫 장면 대사 몇 개. 그 뒤로는 대사를 넘기지 않아 음악만 이어진다.
INTRO = "wait 1500; press start; wait 600; a 10"
RECORD_FRAMES = 60 * int(os.environ.get("BGM_SECONDS", "200"))


def seq_table(d):
    symb, _, info, _ = struct.unpack_from("<IIII", d, 0x10)
    names_at = symb + struct.unpack_from("<I", d, symb + 8)[0]
    names = []
    for i in range(struct.unpack_from("<I", d, names_at)[0]):
        o = struct.unpack_from("<I", d, names_at + 4 + i * 4)[0]
        names.append(d[symb + o:d.index(b"\0", symb + o)].decode())
    rec = info + struct.unpack_from("<I", d, info + 8)[0]
    entries = [info + struct.unpack_from("<I", d, rec + 4 + i * 4)[0]
               for i in range(struct.unpack_from("<I", d, rec)[0])]
    return names, entries


def mute_effects(sd, d):
    """효과음(SSAR 안의 시퀀스) 음량을 모두 0 으로. SSAR 레코드: 오프셋 u32, 뱅크 u16, 음량 u8, …(12 바이트)."""
    info = struct.unpack_from("<I", d, 0x18)[0]
    fat = struct.unpack_from("<I", d, 0x20)[0]
    rec = info + struct.unpack_from("<I", d, info + 12)[0]
    for i in range(struct.unpack_from("<I", d, rec)[0]):
        fid = struct.unpack_from("<H", d, info + struct.unpack_from("<I", d, rec + 4 + 4 * i)[0])[0]
        start = struct.unpack_from("<I", d, fat + 12 + fid * 16)[0]
        assert d[start:start + 4] == b"SSAR", d[start:start + 4]
        count = struct.unpack_from("<I", d, start + 0x1C)[0]
        for k in range(count):
            sd[start + 0x20 + k * 12 + 6] = 0


def main(rom_path, out, picks, quiet=False):
    rom = Rom(Path(rom_path).read_bytes())
    fid = rom.find(SDAT)
    d = rom.file(fid)
    names, entries = seq_table(d)
    os.makedirs(out, exist_ok=True)
    for k in picks or range(len(names)):
        wav = Path(out) / f"{k:02d}_{names[k]}.wav"
        if wav.exists():
            continue
        sd = bytearray(d)
        for e in ([entries[int(os.environ["BGM_SLOT"])]] if os.environ.get("BGM_SLOT") else entries):
            sd[e:e + 10] = d[entries[k]:entries[k] + 10]
        if quiet:
            mute_effects(sd, d)
        test = Path(out) / f"test_{k:02d}.nds"
        test.write_bytes(rebuild(rom, {fid: bytes(sd)}))
        # 녹음은 장면에 들어간 뒤부터 쓰도록 앞부분을 잘라 낸다(아래 trim)
        raw = Path(out) / f"raw_{k:02d}.wav"
        subprocess.run([sys.executable, str(HERE / "play.py"), str(test), str(Path(out) / "shots"), "--wav", str(raw),
                        "--cmd", f"{INTRO}; wait {RECORD_FRAMES}"], check=True, capture_output=True)
        test.unlink()
        trim(raw, wav)
        raw.unlink()
        print(wav, flush=True)


def trim(src, dst):
    """첫 소리 직전부터 남긴다(앞쪽 무음과 타이틀 이전 효과음 제외)."""
    import array
    import wave
    w = wave.open(str(src))
    rate, frames = w.getframerate(), w.readframes(w.getnframes())
    a = array.array("h", frames)
    start = 46 * rate   # 장면에 들어가는 시점(일본판 실측)
    i = start
    while i < len(a) // 2 and abs(a[2 * i]) < 64 and abs(a[2 * i + 1]) < 64:
        i += 1
    o = wave.open(str(dst), "wb")
    o.setnchannels(2), o.setsampwidth(2), o.setframerate(rate)
    o.writeframes(a[2 * max(start, i - rate // 20):].tobytes())
    o.close()


if __name__ == "__main__":
    args = sys.argv[3:]
    quiet = "--quiet" in args
    main(sys.argv[1], sys.argv[2], [int(x) for x in args if x != "--quiet"], quiet)
