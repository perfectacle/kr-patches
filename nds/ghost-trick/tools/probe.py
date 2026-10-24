"""시험용 롬: 대사 하나를 주어진 텍스트로 바꾼다(폭 실험용, 배포용 아님).

    probe.py JP.nds IN.nds OUT.nds FILE RUN I "TEXT"
TEXT 는 대사 TSV 의 ko 와 같은 표기. 같은 묶음의 나머지 대사는 그대로 둔다.
"""
import sys
from pathlib import Path

import lmg
import textcodec as T
from kr_patch import lz11
from kr_patch.nds.rom import Rom, rebuild

HERE = Path(__file__).resolve().parent.parent
jp_path, src, dst, name, run, idx, text = sys.argv[1:8]
kc = T.Codec(T.ko_table(HERE / "tables/low.tsv"))
packed = name.endswith(".lz")
rom = Rom(open(src, "rb").read())
fid = rom.find(name)
K = rom.file(fid)
# 묶음 범위는 일본판에서(다시 만든 롬은 묶음 끝 여유 칸이 0 이라 runs() 가 짧게 잡는다)
jp = Rom(open(jp_path, "rb").read())
J = jp.file(jp.find(name))
if packed:
    K, J = lz11.decompress(K)[0], lz11.decompress(J)[0]
w = lmg.code_words(K)
layout = [(a, b, lmg.locate(w, a, len(m))) for a, b, m in lmg.runs(J)]
new = []
for r, (a, b, msgs) in enumerate(layout):
    run_new = []
    for k, (s, e) in enumerate(msgs):
        body = tuple(w[s + 3:e - 1])
        if r == int(run) and k == int(idx):
            body = kc.encode(text)
        run_new.append((lmg.MSG, w[s + 1], w[s + 2]) + body + (lmg.END,))
    new.append(run_new)
out = lmg.repack(K, layout, new)
open(dst, "wb").write(rebuild(rom, {fid: lz11.compress(out) if packed else out}))
print(dst)
