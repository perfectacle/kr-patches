"""Find key-wait problems by comparing wait points with the JP script line by line.

The engine waits for a key after printing 」 』 . ？ ！ (codes in the $02:A97C list handled
at $00:AC52) unless {13} came before, and at every {16}. {00} is a plain line break.
Reported per line:
  double  - two waits with no character printed between them (the player presses twice)
  nowait  - a page is cleared ({25}/{26}/{27}) or a jump/choice follows text with no wait
            after the last character (the text vanishes without a key press)
Only lines where the KR count differs from JP are printed.

usage: waits.py script.txt script-jp.txt kr.tbl jp.tbl
"""
import re, sys
from dump import load_table
from assemble import normalize_text

AUTO = {1479, 1481, 1482, 1501, 1503}
TOKEN = re.compile(r'#[0-9A-F]{6}\n|#b\d{7}\n|\{([0-9A-F]{2})(?::[^}]*)?\}|<(\d{4})>|\n|(.)', re.S)


def events(line, inv, ends=(0x25, 0x26, 0x27, 0x03, 0x19, 0x1A)):
    """Sequence of 'c' (char), 'w' (wait), 'e' (page end / leave) for one line."""
    out, suppress = [], False
    for m in TOKEN.finditer(line):
        ctl, raw, ch = m.groups()
        if ctl is not None:
            c = int(ctl, 16)
            if c == 0x13:
                suppress = True
            elif c == 0x16:
                out.append('w')
            elif c in ends:
                out.append('e')
        elif raw is not None or ch is not None:
            code = int(raw) if raw else inv.get(ch)
            out.append('c')
            if code in AUTO:
                if suppress:
                    suppress = False
                else:
                    out.append('w')
    return out


def problems(ev):
    dbl = nowait = 0
    last = None  # last of 'c'/'w' seen
    for e in ev:
        if e == 'w':
            if last == 'w':
                dbl += 1
            last = 'w'
        elif e == 'c':
            last = 'c'
        elif e == 'e':
            if last == 'c':
                nowait += 1
            last = None
    return dbl, nowait


def inverse(path):
    inv = {}
    for code, ch in load_table(path).items():
        inv.setdefault(ch, code)
    return inv


def main(kr, jp, krt, jpt):
    K = normalize_text(open(kr, encoding='utf-8').read()).split('\n')
    J = open(jp, encoding='utf-8').read().split('\n')
    ki, ji = inverse(krt), inverse(jpt)
    tot = [0, 0]
    for n, (k, j) in enumerate(zip(K, J), 1):
        kd, kn = problems(events(k, ki))
        jd, jn = problems(events(j, ji))
        if kd > jd or kn > jn:
            tot[0] += max(0, kd - jd)
            tot[1] += max(0, kn - jn)
            print('%d\tdouble %d/%d\tnowait %d/%d\t%s' % (n, kd, jd, kn, jn, k[:160]))
    print('extra double waits %d, extra no-wait page ends %d' % tuple(tot), file=sys.stderr)


if __name__ == '__main__':
    main(*sys.argv[1:5])
