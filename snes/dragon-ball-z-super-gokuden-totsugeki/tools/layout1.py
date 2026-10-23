"""Check Korean dialogue layout: pixel width per window and 3-line pages.

usage: layout1.py file.tsv   (columns: id, info, ...; text is the "text" column, else the last)

Face windows are 128 px wide, narration windows (info FFxx) 176 px; Hangul is
13 px, kana/punctuation 9 px. A page holds 3 lines; "/" ends a line, so blank
lines pad a page out and the next text starts a new page.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import kr1  # noqa: E402
import width1  # noqa: E402

ENC = kr1.default()


def text_px(s):
    """width of one line; characters not in the font count as Hangul (13 px)"""
    return sum(width1.char_width(ENC.code(t)) if not ENC.missing(t) else 13 for t in ENC.tokens(s))


def limit(info):
    """info "Lnnn" sets the width directly (menus, lists); FFxx is narration."""
    if info.startswith("L"):
        return int(info[1:])
    return 176 if info.upper().startswith("FF") else 128


def check(text, info):
    errs = []
    lines = text.split("/")
    lim = limit(info)
    for k, l in enumerate(lines):
        w = text_px(l)
        if w > lim:
            errs.append(f"line {k + 1} {w}px > {lim}px: {l}")
        if l != l.rstrip():
            errs.append(f"line {k + 1} trailing space")
    pages = [lines[i:i + 3] for i in range(0, len(lines), 3)]
    for p, pg in enumerate(pages):
        if pg and pg[0] == "" and any(pg):
            errs.append(f"page {p + 1} starts with a blank line")
        seen_blank = False
        for l in pg:
            if l == "":
                seen_blank = True
            elif seen_blank:
                errs.append(f"page {p + 1} has text after a blank line")
                break
    if text and lines[-1] == "":
        errs.append("ends with a blank line")
    return errs


def main():
    bad = 0
    col = -1
    for row in open(sys.argv[1], encoding="utf-8"):
        cols = row.rstrip("\n").split("\t")
        if cols[0] == "id":
            col = cols.index("text") if "text" in cols else -1
            continue
        if len(cols) < 3:
            continue
        errs = check(cols[col], cols[1])
        if errs:
            bad += 1
            print(cols[0], "; ".join(errs))
    print(f"{bad} lines with problems")


if __name__ == "__main__":
    main()
