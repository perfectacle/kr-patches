"""Fix key-wait problems in the script in place (see waits.py for the rules), only where
the JP line waits at the same point.

- The n-th page clear ({25}/{26}/{27}) or choice ({19}/{1A}) of a line gets a {16} in front
  when it follows text with no wait in KR but not in JP.
- A {16} that directly follows an automatic wait is removed when the JP line has no such
  double wait.
Jumps ({03}) are left alone because the page may continue at the target.

usage: fixwaits.py script.txt script-jp.txt kr.tbl jp.tbl
"""
import re, sys
from dump import load_table
from waits import AUTO, events, problems, inverse

TOKEN = re.compile(r'(#[0-9A-F]{6}\n)|(\{([0-9A-F]{2})(?::[^}]*)?\})|(<\d{4}>)|(\n)|(.)', re.S)


def fix_line(line, inv, want_wait, allow_double):
    out, last, suppress = [], None, False   # last: 'c' char, 'w' wait
    added = removed = 0
    for m in TOKEN.finditer(line):
        label, ctl, code, raw, nl, ch = m.groups()
        tok = m.group(0)
        if ctl:
            c = int(code, 16)
            if c == 0x13:
                suppress = True
            elif c == 0x16:
                if last == 'w' and not allow_double:
                    removed += 1
                    continue
                last = 'w'
            elif c in (0x25, 0x26, 0x27, 0x19, 0x1A):
                w = want_wait.pop(0) if want_wait else False
                if last == 'c' and w:
                    out.append('{16}')
                    added += 1
                last = None
            elif c == 0x03:
                last = None
        elif raw or ch:
            k = inv.get(ch) if ch else int(raw[1:-1])
            last = 'c'
            if k in AUTO:
                if suppress:
                    suppress = False
                else:
                    last = 'w'
        out.append(tok)
    return ''.join(out), added, removed


PAGE_END = re.compile(r'\{(25|26|27|19|1A)(?::[^}]*)?\}')


def jp_waits(line, inv):
    """For each page clear/choice of a JP line, whether a wait precedes it."""
    out, last = [], None
    for e in events(line, inv, ends=(0x25, 0x26, 0x27, 0x19, 0x1A)):
        if e == 'e':
            out.append(last == 'w')
            last = None
        else:
            last = e
    return out


def main(path, jpath, tbl, jtbl):
    inv, jinv = inverse(tbl), inverse(jtbl)
    lines = open(path, encoding='utf-8').read().split('\n')
    jl = open(jpath, encoding='utf-8').read().split('\n')
    A = R = 0
    for i, (l, j) in enumerate(zip(lines, jl)):
        want = jp_waits(j, jinv)
        if len(want) != len(PAGE_END.findall(l)):
            want = []           # structure differs; leave page ends alone
        jd, _ = problems(events(j, jinv))
        lines[i], a, r = fix_line(l, inv, want, jd > 0)
        A += a
        R += r
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('waits added %d, removed %d' % (A, R))


if __name__ == '__main__':
    main(*sys.argv[1:5])
