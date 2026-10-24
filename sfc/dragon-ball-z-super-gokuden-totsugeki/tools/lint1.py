"""Style lint for review TSVs (columns id, info, text, ...): rules from review/style-guide.md
that a script can check. usage: lint1.py file.tsv"""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")

BANNED = [  # (pattern, message)
    (r"렛츠|레츠|LETS|땡큐|오케이", "외래어 감탄은 한국어로 (판례)"),
    (r"슈우", "シュウ → 슈"),
    (r"후라이팬", "프라이팬 산"),
    (r"용신", "神龍 → 신룡"),
    (r"[1-7]성구", "일성구~칠성구로 (사성구)"),
    (r"드라쿨라", "드라큘라맨"),
    (r"도동파", "도돈파"),
    (r"전기밥통", "전자밥솥"),
    (r"레드 ?사령관", "레드 총수"),
    (r"카린탑", "카린 탑"),
    (r"거북 ?하우스", "카메하우스"),
    (r"머슬타워", "머슬 타워"),
    (r"마이크로밴드", "마이크로 밴드"),
    (r"징글 마을", "징글촌"),
    (r"(?<=[가-힣]) 님(?:께서|께|에게|을|를|이|은|의|도|과|와)?(?![가-힣])", "호칭 「님」은 붙여 씀"),
    (r"거북선인|거북신선", "무천도사"),
    (r"ー", "장음 기호 쓰지 않음"),
    (r"[A-Za-z]+(?!버튼)", "영문자 (버튼 이름만 허용)"),
]

# v1.0 jokes the patch author chose to keep in v1.1
KEPT_JOKES = {"0C20", "0F58", "1169", "choice:072", "choice:073", "choice:074",
              "advice:00B", "advice:02D", "advice:04F"}


def jp_texts():
    out = {}
    for name in os.listdir(os.path.join(ROOT, "tables")):
        if name.endswith("-v1.0.tsv"):
            for row in open(os.path.join(ROOT, "tables", name), encoding="utf-8"):
                c = row.rstrip("\n").split("\t")
                if c[0] != "id":
                    out[c[0]] = c[2]
    return out


def main():
    jp = jp_texts()
    bad = 0
    col = 2
    for row in open(sys.argv[1], encoding="utf-8"):
        c = row.rstrip("\n").split("\t")
        if c[0] == "id":
            col = c.index("text") if "text" in c else 2
            continue
        if len(c) <= col or c[0] in KEPT_JOKES:
            continue
        t, errs = c[col], []
        j = jp.get(c[0], "")
        pages = lambda s: (s.count("/") + 3) // 3  # noqa: E731
        if j and pages(t) > pages(j):
            errs.append(f"쪽 수 초과: 원문 {pages(j)}쪽, 번역 {pages(t)}쪽")
        if c[1][:2].upper() in ("2F", "7B", "5E") and "구먼" in t:
            errs.append("무천도사·잭키 춘·학선인은 「-구먼」 대신 「-구나」 (우마왕 전용)")
        if "～" in t and not re.search("[～〜]", j):
            errs.append("물결표: 원문에 ～ 없음")
        for m in re.finditer(r"(?<![^\s/「（])([^\s/])‥ (\S)", t):
            if m.group(2) == m.group(1):
                errs.append(f"더듬기 띄어 씀: {m.group(0)}")
        for pat, msg in BANNED:
            m = re.search(pat, t)
            if m and msg.startswith("영문자") and m.group(0) in j:
                continue
            if m:
                errs.append(f"{msg}: {m.group(0)}")
        if errs:
            bad += 1
            print(c[0], "; ".join(errs))
    print(f"{bad} lines with lint problems")


if __name__ == "__main__":
    main()
