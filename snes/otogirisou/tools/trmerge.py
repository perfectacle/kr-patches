"""Merge retranslation outputs into the script, after a control-code check.

usage: trmerge.py script.txt out_*.txt
A block is applied only when its {..} codes equal the current script line exactly.
Glossary fixes that came after some chunks were written are applied here.
"""
import re, sys

CODES = re.compile(r'\{[^}]*\}')
LATE_TERMS = [('섀도', '쉐도우'), ('미이라', '미라')]


def main(script, outs):
    lines = open(script, encoding='utf-8').read().split('\n')
    ok = bad = 0
    for path in outs:
        for b in open(path, encoding='utf-8').read().split('@@ ')[1:]:
            n = int(b.split('\n')[0])
            kr = [l[4:] for l in b.split('\n') if l.startswith('KR: ')][0]
            for a, c in LATE_TERMS:
                kr = kr.replace(a, c)
            if CODES.findall(kr) == CODES.findall(lines[n - 1]):
                lines[n - 1] = kr
                ok += 1
            else:
                print('%s: line %d codes differ, skipped' % (path, n))
                bad += 1
    open(script, 'w', encoding='utf-8').write('\n'.join(lines))
    print('applied %d, skipped %d' % (ok, bad))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
