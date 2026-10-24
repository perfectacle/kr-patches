"""일본판·한국어판 롬에서 대사를 뽑아 나란히 적은 TSV 를 만든다(번역 작업용, 저장소에 넣지 않는다).

    dump.py JP.nds KR.nds OUT.tsv [경로 접두어]

열: 파일, 묶음, 묶음 안 순번, 장면, 번호, head(한국어판 FF2D 두 인수), 일본어, 한국어, 표시(이상한 점)
파일·묶음·순번은 일본판 기준이라 tables/v1.2/script.tsv 의 줄과 그대로 맞는다.
"""
import sys
from pathlib import Path

import lmg
import textcodec as T
from kr_patch import lz11
from kr_patch.nds.rom import Rom

HERE = Path(__file__).resolve().parent.parent
COLUMNS = ["file", "run", "i", "scene", "no", "head", "ja", "ko", "flags"]


def flags(words):
    """no-end: FFFE 없음, end-inside: FFFE 뒤에 글이 더 있음(잘려 안 보임), after-end: FFFE 뒤에 공백만."""
    if lmg.END not in words:
        return ["no-end"]
    first = words.index(lmg.END)
    if first == len(words) - 1:
        return []
    return ["end-inside" if any(x not in (0, 0xFF) for x in words[first + 1:]) else "after-end"]


def scripts(rom):
    """스크립트 파일 경로: stNN/*_Expand.xml.lz(LZ11) 와 system/*.bin(무압축)."""
    names = rom.names.values()
    return (sorted(n for n in names if n.endswith("_Expand.xml.lz"))
            + sorted(n for n in names if n.startswith("system/") and n.endswith(".bin")))


def read_script(rom, name):
    data = rom.file(rom.find(name))
    return lz11.decompress(data)[0] if name.endswith(".lz") else data


def rows(jp, kr, only=None):
    """일본판 대사마다 dict(COLUMNS). 한국어판은 대사 위치가 일본판과 달라 lmg.locate 로 찾는다."""
    jc = T.Codec(T.load_table(HERE / "tables/jp.tsv"))
    kc = T.Codec(T.ko_table(HERE / "tables/low.tsv"))
    for name in scripts(jp):
        if only and not name.startswith(only):
            continue
        J, K = read_script(jp, name), read_script(kr, name)
        wj, wk = lmg.code_words(J), lmg.code_words(K)
        layout = lmg.runs(J)
        spans = [(a, b) for a, b, _ in layout]
        for r, (a, b, msgs) in enumerate(layout):
            ids = [(wj[s + 1], wj[s + 2]) for s, _ in msgs]
            pm = lmg.pointer_map(wj, wk, [s for s, _ in msgs], spans)
            hint = [pm.get(s) for s, _ in msgs]
            orig = {(wj[s + 1], wj[s + 2]): tuple(wj[s + 3:s + 13]) for s, _ in msgs}
            for k, ((s, e), loc, mid) in enumerate(zip(msgs, lmg.locate(wk, a, len(msgs), ids, b, hint, orig), ids)):
                kw = wk[loc[0]:loc[1]] if loc else ()
                fl = flags(kw) if loc else ["missing"]
                if loc and (kw[1], kw[2]) != mid:
                    fl.append(f"head-{mid[0]:x},{mid[1]:x}>{kw[1]:x},{kw[2]:x}")
                yield dict(zip(COLUMNS, [
                    name, str(r), str(k), f"{mid[0]:x}", f"{mid[1]:x}", f"{kw[1]:x},{kw[2]:x}" if loc else "",
                    jc.decode(wj[s + 3:e - 1]), kc.decode(kw[3:-1] if kw and kw[-1] == lmg.END else kw[3:]),
                    ",".join(fl)]))


def load(path):
    return Rom(Path(path).read_bytes())


if __name__ == "__main__":
    jp_rom, kr_rom, out = sys.argv[1:4]
    lines = ["\t".join(COLUMNS)]
    lines += ["\t".join(r[c] for c in COLUMNS)
              for r in rows(load(jp_rom), load(kr_rom), sys.argv[4] if len(sys.argv) > 4 else None)]
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(len(lines) - 1)
