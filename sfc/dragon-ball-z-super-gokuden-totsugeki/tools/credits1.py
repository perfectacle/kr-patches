"""Ending cast and staff rows: centre each Korean name under its portrait column
and each staff line on the screen.

usage: credits1.py jp.smc v1.0.smc   (prints rows for tables/ui-fixes.tsv; the last
column caps the codes at the Japanese row length, since each row owns its slot)

Each row is a fixed slot in bank B7. Column centres are measured from the
Japanese rows (3 columns at 48/128/208 px, 2 columns at 88/168 px); names too wide for their column are
written without spaces or nudged sideways. Gaps are filled with the space (9 px) and the narrow spacers {sp2}..{sp7}.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402
from layout1 import text_px  # noqa: E402

ROWS = [  # (file offset, [(name, centre px), ...])
    (0x1BDE83, [("오룡", 48), ("손오공", 128), ("부르마", 208)]),
    (0x1BDEBB, [("무천도사", 88), ("바다거북", 168)]),
    (0x1BDEE7, [("야무치", 88), ("푸알", 168)]),
    (0x1BDF17, [("우마왕", 88), ("치치", 168)]),
    (0x1BDF43, [("토끼단", 48), ("당근토끼", 128), ("토끼단", 216)]),
    (0x1BDF7B, [("슈", 48), ("피라후", 128), ("마이", 208)]),
    (0x1BDFB5, [("런치", 48), ("크리링", 128), ("무서운 런치", 208)]),
    (0x1BDFF5, [("박테리안", 48), ("아나운서", 128), ("기란", 208)]),
    (0x1BE02F, [("나무", 48), ("잭키 춘", 128), ("란판", 208)]),
    (0x1BE06B, [("블루 장군", 48), ("레드 총수", 128), ("블랙 참모", 208)]),
    (0x1BE0A3, [("무라사키상사", 48), ("화이트장군", 128), ("메탈릭중사", 208)]),
    (0x1BE0DD, [("바이올렛대령", 48), ("실버 대령", 128), ("옐로 대령", 208)]),
    (0x1BE115, [("팔봉이", 128)]),
    (0x1BE13D, [("우파", 48), ("카린님", 128), ("보라", 208)]),
    (0x1BE175, [("타오파이파이", 128)]),
    (0x1BE199, [("점쟁이 바바", 128)]),
    (0x1BE1BF, [("드라큘라맨", 48), ("안내 유령", 128), ("스케 씨", 208)]),
    (0x1BE1F9, [("미라 군", 42), ("수수께끼 가면남", 128), ("아크맨", 208)]),
    (0x1BE231, [("손오반", 128)]),
    (0x1BE255, [("천진반", 48), ("학선인", 128), ("차오즈", 204)]),
    (0x1BE287, [("차파왕", 48), ("펌프트", 128), ("사나이 늑대", 208)]),
    (0x1BE2BF, [("야지로베", 128)]),
    (0x1BE2E7, [("탬버린", 48), ("드럼", 128), ("심벌", 208)]),
    (0x1BE323, [("피콜로 대마왕", 86), ("피아노", 164)]),
    (0x1BE34F, [("피콜로 대마왕", 126)]),
    (0x1BE377, [("브리프", 88), ("부르마 엄마", 168)]),
    (0x1BE3A9, [("갓짱", 48), ("아라레", 128), ("갓짱", 208)]),
    (0x1BE3E7, [("미도리 씨", 48), ("센베 씨", 128), ("터보 군", 208)]),
    (0x1BE425, [("스파맨（전）", 80), ("스파맨（후）", 176)]),
]
# Staff rows: blank lines first (as in the Japanese rows), then centred lines.
# Names keep v1.0's given-name-first order; 東海林隆 was misread in v1.0.
STAFF = [
    (0x1BE5F1, 1, ["총괄 프로듀서", "에이사쿠 마니와"]),
    (0x1BE64D, 3, ["치프 프로듀서", "타카시 쇼지"]),
    (0x1BE6AD, 3, ["프로듀서", "토시히로 스즈키"]),
    (0x1BE709, 3, ["어시스턴트 프로듀서", "타케오 이소가이", "다이스케 우치야마"]),
    (0x1BE791, 3, ["디렉터", "신사쿠 시마다"]),
    (0x1BE7EB, 3, ["코디네이터", "카바"]),
]
SPACERS = [(" ", 9), ("{sp7}", 7), ("{sp6}", 6), ("{sp4}", 4), ("{sp2}", 2)]


def fill(gap):
    """fewest spacer tokens summing to gap (or gap - 1 when gap is odd and unreachable)"""
    for target in (gap, gap - 1, gap + 1):
        for n in range(0, 40):
            for combo in itertools.combinations_with_replacement(SPACERS, n):
                if sum(w for _, w in combo) == target:
                    return "".join(t for t, _ in combo)
    raise ValueError(gap)


def row_text(names):
    out, x, last_end = "", 0, None
    for name, centre in names:
        w = text_px(name)
        start = round(centre - w / 2)
        if last_end is not None and start < last_end + 8:
            raise SystemExit(f"{name}: overlaps the previous name")
        out += fill(start - x) + name
        x = start + w
        last_end = x
    return out


def main():
    jp = open(sys.argv[1], "rb").read()
    rom = open(sys.argv[2], "rb").read()
    root = os.path.join(os.path.dirname(__file__), "..", "tables")
    old_table = D.load_table(os.path.join(root, "kr-v1.0.txt"))
    rows = [(o, row_text(names)) for o, names in ROWS]
    rows += [(o, "{s: }/" * blank + "/".join(row_text([(t, 128)]) for t in lines))
             for o, blank, lines in STAFF]
    for o, text in rows:
        old = D.decode(D.words(rom, o, 200), old_table)
        print(f"{o:06X}\t{old}\t{text}\t{len(D.words(jp, o, 200))}")


if __name__ == "__main__":
    main()
