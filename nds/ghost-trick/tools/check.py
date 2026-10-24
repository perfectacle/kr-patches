"""대사 TSV 자동 검사.

    check.py JP.nds V11.nds SCRIPT.tsv [PROPOSAL.tsv]

검사: 글자표에 없는 글자, 제어 코드 열이 v1.1 과도 일본판과도 다름({01}·{02}·{FE} 는 제외),
줄 넘침(좁은 창 13자, 일본어에 14자 넘는 줄이 있으면 넓은 창 16자),
창 하나에 일본어보다 많은 줄(두 줄 넘게), 남은 일본어(가나·한자).
일본어와 v1.1 대사는 두 롬에서 읽는다. PROPOSAL.tsv(열: file, run, i, ko)를 주면
그 줄의 ko 로 바꿔 검사하고 그 줄만 보고한다. 문제가 있으면 종료 코드 1.
"""
import csv
import re
import sys
from pathlib import Path

import dump
import textcodec as T

HERE = Path(__file__).resolve().parent.parent
TOKEN = re.compile(r"\{([0-9A-F]{2})(?::([0-9a-f,]+))?\}|\[([0-9a-f]+)\]|(.)", re.S)
# 대화창 화자 코드(이 코드 뒤의 줄만 폭을 검사한다)
LIMIT = {"08", "19", "1B", "24"}
NARROW, WIDE = 13, 16
JA = re.compile(r"[぀-ゟ゠-ヺヽ-ヿ一-鿿]")  # 장음 기호 ー(U+30FC)는 한국어판도 쓴다


def boxes(text):
    """[(화자 코드, [줄...])] — {02} 로 창을 나누고 {01} 로 줄을 나눈다."""
    out, lines, cur, win = [], [], "", "?"
    for m in TOKEN.finditer(text):
        code, _, raw, ch = m.groups()
        if code == "01":
            lines.append(cur); cur = ""
        elif code == "02":
            lines.append(cur); out.append((win, lines)); lines, cur = [], ""
        elif code in LIMIT:
            win = code
        elif code is None:
            cur += ch if ch else "□"
    lines.append(cur)
    out.append((win, lines))
    return out


def codes(text):
    return [m.group(0) for m in TOKEN.finditer(text) if m.group(1) and m.group(1) not in ("01", "02", "FE")]


def repaired(cs):
    """v1.1 이 인수 하나짜리 코드의 인수를 코드로 넣은 곳(`{05}{06}`, 일본판은 `{05:6}`)을 바로잡은 코드 열."""
    out = []
    for c in cs:
        prev = out[-1] if out else ""
        if len(c) == 4 and len(prev) == 4 and T.ARGS.get(int(prev[1:3], 16)) == 1:
            out[-1] = "{%s:%x}" % (prev[1:3], int(c[1:3], 16))
        else:
            out.append(c)
    return out


def leftover_ja(ko, ja):
    """한국어 대사에 남은 일본어 글자. 제어 코드 사이에 낀 값이 우연히 가나 번호와 같아 글자로
    읽히는 대사가 있어서, 일본판과 똑같은 머리 부분에서 앞뒤가 모두 제어 코드인 낱글자는 뺀다."""
    tk, tj = [m.group(0) for m in TOKEN.finditer(ko)], [m.group(0) for m in TOKEN.finditer(ja)]
    n = 0
    while n < min(len(tk), len(tj)) and tk[n] == tj[n]:
        n += 1

    def between_codes(i):
        return 0 < i < n and i + 1 < len(tk) and tk[i - 1][0] == "{" and tk[i + 1][0] == "{"

    return [t for i, t in enumerate(tk) if len(t) == 1 and JA.match(t) and not between_codes(i)]


def check_row(ko, ja, base_ko, kc):
    problems = []
    try:
        kc.encode(ko)
    except ValueError as e:
        problems.append(f"글자: {e}")
    # v1.1 그대로이거나, 일본판과 같거나, v1.1 의 인수 실수만 바로잡은 것이면 통과
    if codes(ko) not in (codes(base_ko), codes(ja), repaired(codes(base_ko))):
        problems.append("제어 코드가 v1.1·일본판과 다름")
    ja_max = max((len(l.rstrip()) for _, ls in boxes(ja) for l in ls), default=0)
    ja_lines = max((len(ls) for _, ls in boxes(ja)), default=2)
    # 초상화가 창 안에 있는 대화창은 13자, 전체 폭 창은 16자(글자당 14px, 넘치면 잘림).
    # 창 종류는 장면이 정해서 텍스트로는 모른다: 일본어가 모두 13자 이하면 좁은 창으로 본다.
    lim = NARROW if ja_max <= NARROW else max(WIDE, ja_max)
    for win, lines in boxes(ko):
        if len(lines) > max(2, ja_lines):
            problems.append(f"창 하나에 {len(lines)}줄")
        if win not in LIMIT:
            continue
        for l in lines:
            n = len(l.rstrip())
            if n > lim:
                problems.append(f"줄 넘침 {n}>{lim}: {l}")
    if leftover_ja(ko, ja):
        problems.append("일본어가 남음")
    return problems


def read(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))


def main(jp_rom, v11_rom, script, proposal=None):
    kc = T.Codec(T.ko_table(HERE / "tables/low.tsv"))
    ref = {(r["file"], r["run"], r["i"]): r for r in dump.rows(dump.load(jp_rom), dump.load(v11_rom))}
    targets = read(proposal or script)
    bad = 0
    for r in targets:
        key = (r["file"], r["run"], r["i"])
        if key not in ref:
            raise SystemExit(f"{key} is not a message of the Japanese ROM")
        ps = check_row(r["ko"], ref[key]["ja"], ref[key]["ko"], kc)
        if ps:
            bad += 1
            print("\t".join(key) + "\t" + " / ".join(ps))
    keys = [(r["file"], r["run"], r["i"]) for r in targets]
    dup = sorted({k for k in keys if keys.count(k) > 1}) if len(set(keys)) != len(keys) else []
    if dup:
        print(f"{len(dup)} messages appear more than once, first {dup[:1]}")
        bad += len(dup)
    if not proposal:
        missing = sorted(set(ref) - set(keys))
        if missing:
            print(f"{len(missing)} messages are not in {script}, first {missing[:1]}")
            bad += len(missing)
    print(f"# {bad} / {len(targets)} rows with problems", file=sys.stderr)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:5]) else 0)
