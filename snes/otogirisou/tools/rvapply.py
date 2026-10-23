"""Apply review edits (TSV: line, old, new, perspective, reason) to the script.

An edit is applied only when `old` occurs exactly once in the line, the control codes of
the line stay the same and the new text uses allowed characters. Rejected edits are listed.
usage: rvapply.py script.txt edits.tsv [...]
"""
import re, sys

CODES = re.compile(r'\{[^}]*\}')
ALLOWED = re.compile(r'[가-힣 0-9A-Z.,?!…「」『』“”():~弟切草]')


def main(script, paths):
    lines = open(script, encoding='utf-8').read().split('\n')
    ok = bad = 0
    for p in paths:
        for row in open(p, encoding='utf-8').read().splitlines():
            f = row.split('\t')
            if len(f) < 3 or not f[0].strip().isdigit():
                continue
            n, old, new = int(f[0]), f[1], f[2]
            line = lines[n - 1]
            why = None
            if line.count(old) != 1:
                why = 'old text not unique/absent'
            elif '{' in old or '{' in new:
                why = 'touches a control code'
            elif any(not ALLOWED.match(c) for c in new):
                why = 'disallowed character'
            if why is None:
                upd = line.replace(old, new)
                if CODES.findall(upd) != CODES.findall(line):
                    why = 'codes changed'
            if why:
                bad += 1
                print('%s:%d rejected (%s): %s -> %s' % (p, n, why, old, new))
                continue
            lines[n - 1] = upd
            ok += 1
    open(script, 'w', encoding='utf-8').write('\n'.join(lines))
    print('applied %d, rejected %d' % (ok, bad))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
