"""대사 u16 열 <-> 사람이 읽는 문자열. 무손실: encode(decode(x)) == x.

- 글자: 글자표의 문자. 같은 문자가 둘 이상이면 낮은 번호만 문자로 쓰고 나머지는 [hex].
- 제어 코드 FFxx: {XX} 또는 인수가 있으면 {XX:a,b} (인수는 16진). 인수 개수는 ARGS.
- 표에 없는 값: [hex].
- 0x00FF(한국어판 공백)는 ' ', 줄바꿈 코드 FF01 은 {01} 그대로 둔다.
"""
import re
from pathlib import Path

# 대사 블록 안에서 확인한 인수 개수(일본판·한국어판 같은 대사의 값 비교)
ARGS = {0x2D: 2, 0x05: 1, 0x08: 1, 0x0C: 1, 0x0D: 1, 0x0E: 1, 0x10: 2, 0x15: 1, 0x19: 1, 0x1B: 1,
        0x1C: 1, 0x1D: 3, 0x1E: 1, 0x20: 1, 0x22: 1, 0x24: 1, 0x25: 1, 0x27: 2, 0x28: 2, 0x2B: 1,
        0x2C: 1, 0x2E: 1}

TOKEN = re.compile(r"\{([0-9A-F]{2})(?::([0-9a-f,]+))?\}|\[([0-9a-f]+)\]|(.)", re.S)


def load_table(path):
    tab = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        k, _, c = line.partition("\t")
        if c:
            tab[int(k, 16)] = c
    return tab


def ko_table(low_path):
    tab = load_table(low_path)
    tab[0xFF] = " "
    for i, (a, b) in enumerate((a, b) for a in range(0xB0, 0xC9) for b in range(0xA1, 0xFF)):
        tab[0x12C + i] = bytes([a, b]).decode("euc-kr")
    return tab


class Codec:
    def __init__(self, table):
        self.dec = {}
        self.enc = {}
        for k in sorted(table):
            c = table[k]
            if len(c) == 1 and c not in self.enc and c not in "{}[]":
                self.enc[c] = k
                self.dec[k] = c

    def decode(self, words):
        out = []
        i = 0
        while i < len(words):
            x = words[i]
            if x >= 0xFF00:
                n = ARGS.get(x & 0xFF, 0)
                args = words[i + 1:i + 1 + n]
                if len(args) == n and all(a < 0xFF00 for a in args):
                    out.append(f"{{{x & 0xFF:02X}" + (":" + ",".join(f"{a:x}" for a in args) if n else "") + "}")
                    i += 1 + n
                    continue
                out.append(f"{{{x & 0xFF:02X}}}")
            else:
                out.append(self.dec.get(x, f"[{x:x}]"))
            i += 1
        return "".join(out)

    def encode(self, text):
        words = []
        pos = 0
        for m in TOKEN.finditer(text):
            if m.start() != pos:
                raise ValueError(f"cannot parse at {pos}: {text[pos:pos + 10]!r}")
            pos = m.end()
            code, args, raw, ch = m.groups()
            if code:
                words.append(0xFF00 | int(code, 16))
                if args:
                    words += [int(a, 16) for a in args.split(",")]
            elif raw:
                words.append(int(raw, 16))
            elif ch in self.enc:
                words.append(self.enc[ch])
            else:
                raise ValueError(f"{ch!r} is not in the table")
        return tuple(words)
