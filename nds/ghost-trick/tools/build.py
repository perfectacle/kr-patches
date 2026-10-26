"""대사 TSV 로 한국어판 롬을 만든다.

    build.py JP.nds BASE.nds OUT.nds SCRIPT.tsv

스크립트 파일은 일본판에서 다시 만든다: 묶음마다 TSV 의 한국어 대사를 이어 쓰고,
옮겨 간 대사를 가리키는 포인터·레이블을 고친다(lmg.repack). 대사 머리(FF2D 두 인수)는
일본판 값을 쓴다. 출발점(BASE)은 v1.1 롬이라 스크립트 밖 데이터(폰트·그래픽)는 v1.1 그대로다.
다만 타이틀 화면의 v1.1 안내·제작자 문구는 지운다(title.py). 실기·플래시카드에서 대사가 안 나오게 하는
AP 루틴은 오버레이 0 을 고쳐 끈다(apfix.py).
다시 만든 스크립트가 출발점과 같으면 출발점의 압축 바이트를 그대로 둔다.
"""
import csv
from pathlib import Path

import apfix
import lmg
import textcodec as T
import title
from kr_patch import lz11
from kr_patch.nds.rom import Rom, rebuild

HERE = Path(__file__).resolve().parent.parent


def load_script(path):
    """{파일: {(묶음, 순번): 한국어}}"""
    rows = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            rows.setdefault(r["file"], {})[(int(r["run"]), int(r["i"]))] = r["ko"]
    return rows


def script_file(J, msgs, kc):
    """일본판 스크립트 J 에 한국어 대사를 넣은 바이트. TSV 에 없는 대사가 있으면 KeyError."""
    wj = lmg.code_words(J)
    layout = lmg.runs(J)
    new = []
    for r, (a, b, m) in enumerate(layout):
        new.append([(lmg.MSG, wj[s + 1], wj[s + 2]) + kc.encode(msgs[(r, k)]) + (lmg.END,)
                    for k, (s, e) in enumerate(m)])
    return lmg.repack(J, layout, new)


def build(jp_rom, base_rom, script, out=None):
    kc = T.Codec(T.ko_table(HERE / "tables/low.tsv"))
    jp, base = Rom(Path(jp_rom).read_bytes()), Rom(Path(base_rom).read_bytes())
    files, changed = {}, []
    for name, msgs in sorted(load_script(script).items()):
        packed = name.endswith(".lz")
        J = jp.file(jp.find(name))
        fid = base.find(name)
        K = base.file(fid)
        if packed:
            J, K = lz11.decompress(J)[0], lz11.decompress(K)[0]
        try:
            K2 = script_file(J, msgs, kc)
        except (ValueError, KeyError) as e:
            raise SystemExit(f"{name}: {e}") from None
        if K2 != K:
            files[fid] = lz11.compress(K2) if packed else K2
            changed.append(name)
    fid = base.find(title.CPAC)
    files[fid] = title.clean(jp.file(jp.find(title.CPAC)), base.file(fid))
    changed.append(title.CPAC)
    ov = f"overlay9/overlay_{apfix.OVERLAY:04d}.bin"
    fid = base.overlay_files()[ov]
    files[fid] = apfix.patch(base.file(fid))
    changed.append(ov)
    data = rebuild(base, files)
    if out:
        Path(out).write_bytes(data)
    return data, changed


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("jp_rom")
    ap.add_argument("base_rom")
    ap.add_argument("out")
    ap.add_argument("script")
    a = ap.parse_args()
    _, changed = build(a.jp_rom, a.base_rom, a.script, a.out)
    print(len(changed), "files changed")
