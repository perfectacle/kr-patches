"""Encode Korean text with a code table ('/' = newline)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dialogue1 import load_table  # noqa: E402

NARROW_HANGUL = [(0x100, 0x167), (0x180, 0x1E7), (0x200, 0x262)]
# Syllables that exist only as 8 px kana-slot glyphs (name entry, password). They look
# half-width between 16 px glyphs, so outside narrow mode they count as missing and
# text_patch1 draws 16 px glyphs for them.
WIDE_ONLY = "플딩렉"


def is_narrow(c):
    return any(lo <= c < hi for lo, hi in NARROW_HANGUL)


class Encoder:
    def __init__(self, table, narrow=False):
        """narrow: prefer the 8 px Hangul in the kana slots (menus) over 16 px glyphs."""
        self.table = dict(table)
        self.enc = {}
        for c in sorted(self.table):
            v = self.table[c]
            if not v or v.startswith("〓"):
                continue
            prev = self.enc.get(v)
            if prev is None or (is_narrow(prev) and not narrow and c >= 0x500) or (narrow and is_narrow(c) and not is_narrow(prev)):
                self.enc[v] = c
        if not narrow:
            for ch in WIDE_ONLY:
                if is_narrow(self.enc.get(ch, 0)):
                    del self.enc[ch]
        self.maxlen = max(len(k) for k in self.enc)

    def tokens(self, text):
        out, k = [], 0
        while k < len(text):
            if text[k] == "/":
                out.append("/")
                k += 1
                continue
            if text[k] == "{" and "}" in text[k:]:
                e = text.index("}", k) + 1
                out.append(text[k:e])
                k = e
                continue
            for n in range(self.maxlen, 0, -1):
                if text[k:k + n] in self.enc:
                    out.append(text[k:k + n])
                    k += n
                    break
            else:
                out.append(text[k])
                k += 1
        return out

    def code(self, t):
        """code for one token: table entry, {s:X} small-font variant, or raw {XXXX}"""
        if t in self.enc:
            return self.enc[t]
        if t.startswith("{s:") and t.endswith("}"):
            return self.enc[t[3:-1]] | 0x8000
        if len(t) == 6 and t[0] == "{" and t[-1] == "}":
            return int(t[1:5], 16)
        raise KeyError(t)

    def encode(self, text):
        """list of codes; unknown characters raise KeyError"""
        return [0x0A if t == "/" else self.code(t) for t in self.tokens(text)]

    def missing(self, text):
        out = []
        for t in self.tokens(text):
            if t != "/":
                try:
                    self.code(t)
                except (KeyError, ValueError):
                    out.append(t)
        return out


def table(path=None):
    """kr-v1.0.txt with the slots v1.2 redraws (kr-v1.2-glyphs.txt) renamed"""
    root = os.path.join(os.path.dirname(__file__), "..", "tables")
    t = load_table(path or os.path.join(root, "kr-v1.0.txt"))
    if path is None:
        t.update(load_table(os.path.join(root, "kr-v1.2-glyphs.txt")))
    return t


def default(path=None):
    return Encoder(table(path))
