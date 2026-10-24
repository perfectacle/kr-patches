"""Compose Hangul glyphs missing from the v1.0 font out of v1.0 glyphs.

The v1.0 font draws each jamo in a fixed place for a given vowel and final, so a syllable
T = (cho, jung, jong) can be built from three existing glyphs of equal size:
  Q = (cho', jung, jong)   same vowel and final as T, another initial
  P = (cho, jung, jong2)   T's initial with the same vowel, another final
  R = (cho', jung, jong2)  Q's initial with P's final
P and R differ only in the initial, so P & ~R is T's initial and R & ~P is Q's initial.
T = (Q minus Q's initial) plus T's initial. A swap of the final works the same way.

usage: compose.py rom.sfc table.tbl --test     (rebuild existing glyphs, report accuracy)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from font import glyph, groups
from dump import load_table


def split(ch):
    n = ord(ch) - 0xAC00
    return n // 588, (n // 28) % 21, n % 28


def join(c, v, j):
    return chr(0xAC00 + c * 588 + v * 28 + j)


class Composer:
    def __init__(self, rom, table):
        gs = groups(rom)
        self.g = {}
        for code, ch in table.items():
            if len(ch) == 1 and '가' <= ch <= '힣' and code <= 1246:
                self.g[ch] = glyph(rom, code, gs)

    @staticmethod
    def same_size(*gl):
        return len({(len(x[0]), len(x)) for x in gl}) == 1

    @staticmethod
    def apply(base, minus, plus):
        """base with the pixels of `minus` removed and those of `plus` added."""
        return [[(b and not m) or p for b, m, p in zip(rb, rm, rp)] for rb, rm, rp in zip(base, minus, plus)]

    def candidates(self, target, exclude=()):
        c, v, j = split(target)
        have = {k: g for k, g in self.g.items() if k not in exclude}
        out = []
        # swap the initial: Q=(c2,v,j), P=(c,v,j2), R=(c2,v,j2); j2 keeps "has a final" the same
        for c2 in range(19):
            q = join(c2, v, j)
            if c2 == c or q not in have:
                continue
            for j2 in range(28):
                if j2 == j or (j2 == 0) != (j == 0):
                    continue
                p, r = join(c, v, j2), join(c2, v, j2)
                if p in have and r in have and self.same_size(have[q], have[p], have[r]):
                    P, R = have[p], have[r]
                    ini_t = [[a and not b for a, b in zip(x, y)] for x, y in zip(P, R)]
                    ini_q = [[b and not a for a, b in zip(x, y)] for x, y in zip(P, R)]
                    out.append(('cho', q, p, r, self.apply(have[q], ini_q, ini_t)))
        # swap the final: Q=(c,v,j2), P=(c2,v,j), R=(c2,v,j2)
        if j:
            for j2 in range(1, 28):
                q = join(c, v, j2)
                if j2 == j or q not in have:
                    continue
                for c2 in range(19):
                    p, r = join(c2, v, j), join(c2, v, j2)
                    if c2 != c and p in have and r in have and self.same_size(have[q], have[p], have[r]):
                        P, R = have[p], have[r]
                        fin_t = [[a and not b for a, b in zip(x, y)] for x, y in zip(P, R)]
                        fin_q = [[b and not a for a, b in zip(x, y)] for x, y in zip(P, R)]
                        out.append(('jong', q, p, r, self.apply(have[q], fin_q, fin_t)))
        return out

    def compose(self, target, exclude=()):
        """Most common result among all candidate triples (they usually agree)."""
        cands = self.candidates(target, exclude)
        if not cands:
            return None
        votes = {}
        for *_, g in cands:
            key = tuple(tuple(int(p) for p in r) for r in g)
            votes[key] = votes.get(key, 0) + 1
        best = max(votes.items(), key=lambda kv: kv[1])[0]
        return [list(r) for r in best]


def test(rom, table):
    comp = Composer(rom, table)
    chars = sorted(comp.g)
    exact = near = none = 0
    worst = []
    for ch in chars:
        g = comp.compose(ch, exclude={ch})
        if g is None:
            none += 1
            continue
        diff = sum(a != b for ra, rb in zip(g, comp.g[ch]) for a, b in zip(ra, rb))
        if diff == 0:
            exact += 1
        elif diff <= 2:
            near += 1
        else:
            worst.append((diff, ch))
    print('%d glyphs: exact %d, 1-2 px off %d, worse %d, no source %d'
          % (len(chars), exact, near, len(worst), none))
    print('worst:', sorted(worst, reverse=True)[:20])


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    table = load_table(sys.argv[2])
    if '--test' in sys.argv:
        test(rom, table)
