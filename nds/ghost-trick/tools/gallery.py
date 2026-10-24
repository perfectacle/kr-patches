"""시험용 롬: 첫 장면(st01_game000)의 대사 자리에 확인할 대사를 차례로 넣는다.

    gallery.py IN.nds SCRIPT.tsv OUT.nds FILE:RUN:I [FILE:RUN:I ...]
부팅 후 A 를 누르면 넣은 대사가 순서대로 나온다(화면 표시 확인용, 배포용 아님).
대사 수가 첫 묶음 대사 수보다 많으면 앞에서부터 그만큼만 넣는다. 자리를 만들려고 뒤쪽 대사는
비운다(그 장면은 끝까지 진행할 수 없다).
"""
import csv
import sys
from pathlib import Path

import build
import lmg
import textcodec as T
from kr_patch import lz11
from kr_patch.nds.rom import Rom, rebuild

HERE = Path(__file__).resolve().parent.parent
TARGET = "st01/st01_game000_Expand.xml.lz"


def main(src, script, dst, keys):
    rows = {(r["file"], r["run"], r["i"]): r for r in
            csv.DictReader(open(script, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE)}
    kc = T.Codec(T.ko_table(HERE / "tables/low.tsv"))
    rom = Rom(open(src, "rb").read())
    fid = rom.find(TARGET)
    K, _ = lz11.decompress(rom.file(fid))
    w = lmg.code_words(K)
    (a, b, msgs), *_ = lmg.runs(K)
    new = []
    for k, (s, e) in enumerate(msgs):
        body = tuple(w[s + 3:e - 1])
        if k < len(keys):
            body = kc.encode(rows[tuple(keys[k].split(":"))]["ko"])
        elif k >= len(keys) + 6:   # 시험에 안 나오는 뒤쪽 대사는 비워 자리를 만든다
            body = ()
        new.append((lmg.MSG, w[s + 1], w[s + 2]) + body + (lmg.END,))
    out = lmg.repack(K, [(a, b, msgs)], [new])
    open(dst, "wb").write(rebuild(rom, {fid: lz11.compress(out)}))
    print(dst, min(len(keys), len(msgs)), "messages")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
