"""Check a retranslation output file against its input chunk.

usage: trcheck.py in.txt out.txt
Reports blocks whose control codes differ from the input KR line, characters outside the
allowed set, missing blocks, and text that ends with … right before a page/choice code.
"""
import re, sys

ALLOWED = re.compile(r'[가-힣 0-9A-Z.,?!…「」『』“”():~弟切草]')
CODES = re.compile(r'\{[^}]*\}')


def blocks(path, key):
    out = {}
    for b in open(path, encoding='utf-8').read().split('@@ ')[1:]:
        n = int(b.split('\n')[0])
        for l in b.split('\n'):
            if l.startswith(key):
                out[n] = l[len(key):]
    return out


def main(inp, outp):
    src, dst = blocks(inp, 'KR: '), blocks(outp, 'KR: ')
    bad = 0
    for n, kr in src.items():
        new = dst.get(n)
        if new is None:
            print(n, 'missing'); bad += 1; continue
        if CODES.findall(new) != CODES.findall(kr):
            print(n, 'codes differ'); bad += 1
        text = CODES.sub('', new)
        odd = sorted(set(c for c in text if not ALLOWED.match(c)))
        if odd:
            print(n, 'characters not allowed:', ''.join(odd)); bad += 1
        if re.search(r'…\s*\{(25|26|27|19|1A)[:}]', new):
            print(n, 'ends with … before a page/choice code'); bad += 1
    print('%d blocks, %d problems' % (len(src), bad))
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(*sys.argv[1:3]) else 0)
