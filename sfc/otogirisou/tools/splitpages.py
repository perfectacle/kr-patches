"""Split pages that would run past the 9 visible lines.

Each script line is cut into pages at {25}/{26}/{27}. A page whose simulated layout (same
rules as layout.py, word wrap on) needs more than MAX_LINES lines gets one of its {00}
breaks turned into {25}: only a break right after a waiting mark (. ? ! 」 』 after
normalization) qualifies, so the player still presses a key before the page clears.
The break that keeps both halves within the limit and splits them most evenly wins.
Pages that span jumps are not handled here; layout.py reports what remains.

usage: splitpages.py rom.sfc table.tbl script.txt
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from dump import load_table
from assemble import normalize_text
from layout import widths_of, hang_list, LEFT, RIGHT, TOP, LINE, SPACING, SPACE, COMMA, PERIOD, EXCLAIM
from waits import AUTO

MAX_LINES = 9
NAME_W = 4 * 12
PAGE_END = re.compile(r'(\{(?:25|26|27)(?::[^}]*)?\})')
TOKEN = re.compile(r'\{([0-9A-F]{2})(?::[^}]*)?\}|<(\d{4})>|(.)', re.S)


def lines_needed(text, inv, W, hang):
    """Lines used by one page of (normalized) text, or 0 if nothing is drawn."""
    toks = []
    for m in TOKEN.finditer(text):
        ctl, raw, ch = m.groups()
        if ctl is not None:
            toks.append(('C', int(ctl, 16)))
        else:
            toks.append(('S', int(raw) if raw else inv[ch]))
    x, y, lowest, pending = LEFT, TOP, None, False
    for i, (k, v) in enumerate(toks):
        if k == 'C':
            if v in (0x00, 0x1C):
                x, y = LEFT, y + LINE
            elif v == 0x20:
                x += NAME_W
            continue
        w = W.get(v, 12)
        if pending:
            pending, x, y = False, LEFT, y + LINE
        if v in (SPACE, COMMA, PERIOD, EXCLAIM):
            total, n = x + w + SPACING, 0
            for kk, vv in toks[i + 1:i + 41]:
                if kk != 'S' or vv == SPACE:
                    break
                n += 1
                if vv not in hang:
                    total += W.get(vv, 12) + SPACING
            if n and total - SPACING >= RIGHT:
                if v == SPACE:
                    x, y = LEFT - w - SPACING, y + LINE
                else:
                    pending = True
        if x + w >= 256 or (x + w >= RIGHT and v not in hang):
            x, y = LEFT, y + LINE
        x += w + SPACING
        lowest = y if lowest is None else max(lowest, y)
    return 0 if lowest is None else (lowest - TOP) // LINE + 1


def split_page(raw, inv, W, hang):
    """Return the page with one {00} replaced by {25}, or None if no split works."""
    norm = lambda s: normalize_text(s)
    if lines_needed(norm(raw), inv, W, hang) <= MAX_LINES:
        return None
    best = None
    for m in re.finditer(r'\{00\}', raw):
        before, after = raw[:m.start()], raw[m.end():]
        nb = norm(before)
        tail = re.sub(r'(\{[0-9A-F]{2}(?::[^}]*)?\})+$', '', nb)
        last = tail[-1:] if tail else ''
        if not last or inv.get(last) not in AUTO or tail[:-1].endswith('{13}'):
            continue   # {13} right before the mark cancels its wait
        a, b = lines_needed(nb, inv, W, hang), lines_needed(norm(after), inv, W, hang)
        if a <= MAX_LINES and b <= MAX_LINES and b > 0:
            score = abs(a - b)
            if best is None or score < best[0]:
                best = (score, before + '{25}' + after)
    return best[1] if best else None


def fit(page, inv, W, hang, lineno, stats):
    """Split page recursively until every part fits."""
    new = split_page(page, inv, W, hang)
    if new is None:
        if lines_needed(normalize_text(page), inv, W, hang) > MAX_LINES:
            stats['failed'] += 1
            print('line %d: could not split: %s' % (lineno, page[:80]))
        return page
    stats['split'] += 1
    before, after = new.split('{25}', 1)
    return fit(before, inv, W, hang, lineno, stats) + '{25}' + fit(after, inv, W, hang, lineno, stats)


def main(romp, tblp, scriptp):
    rom = open(romp, 'rb').read()
    inv = {}
    for code, ch in load_table(tblp).items():
        inv.setdefault(ch, code)
    W, hang = widths_of(rom), hang_list(rom)
    lines = open(scriptp, encoding='utf-8').read().split('\n')
    stats = {'split': 0, 'failed': 0}
    for i, line in enumerate(lines):
        if line.startswith('#'):
            continue
        parts = PAGE_END.split(line)
        changed = False
        for j in range(0, len(parts), 2):
            page = fit(parts[j], inv, W, hang, i + 1, stats)
            if page != parts[j]:
                parts[j], changed = page, True
        if changed:
            lines[i] = ''.join(parts)
    open(scriptp, 'w', encoding='utf-8').write('\n'.join(lines))
    print('pages split %d, still too long %d' % (stats['split'], stats['failed']))


if __name__ == '__main__':
    main(*sys.argv[1:4])
