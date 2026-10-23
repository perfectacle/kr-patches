"""Compare every dialogue between V1.0 and the build: only bracketed names may differ.
Also lists uppercase English words left in dialogues.
usage: verify_dialogue.py OLD_ROM NEW_ROM DLG_TBL_JSON"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dialogue  # noqa: E402
import dlg_rewrite  # noqa: E402


def spans(rom, rev, bank_end):
    ad = dialogue.all_addresses(rom)
    starts = {}
    for i, a in enumerate(ad):
        starts.setdefault(i >> 9, set()).add(a)
    gstart = {g: (lambda b: (b[0] << 16) | b[1])(dialogue.group_base(rom, g)) for g in starts}
    out = []
    for i, a in enumerate(ad):
        g = i >> 9
        same = sorted(starts[g])
        k = same.index(a)
        if k + 1 < len(same):
            end = same[k + 1]
        else:
            later = [gstart[h] for h in gstart if h > g and gstart[h] >> 16 == a >> 16]
            end = min(later) if later else bank_end[a >> 16]
        out.append(dlg_rewrite.decode(rom[a:end], rev))
    return out


def main():
    old = Path(sys.argv[1]).read_bytes()
    new = Path(sys.argv[2]).read_bytes()
    enc = {k: bytes.fromhex(v) for k, v in json.loads(Path(sys.argv[3]).read_text()).items()}
    rev = {v.hex().upper(): k for k, v in enc.items()}
    so = spans(old, rev, dlg_rewrite.BANK_END)
    new_end = {b: e for b, e in dlg_rewrite.BANK_END.items()}
    for line in (Path(__file__).resolve().parents[2] / 'build/dialogue_report.txt').read_text().splitlines():
        m = re.match(r'bank (\w\w): end \w+ -> (\w+)', line)
        if m:
            new_end[int(m.group(1), 16)] = int(m.group(2), 16)
    sn = spans(new, rev, new_end)
    bare = json.loads((Path(__file__).resolve().parents[2] / 'data/dialogue_names.json').read_text())['bare']

    def norm(s):
        s = s.split('{00}')[0]                                    # nothing after the end code is shown
        for en, ko in bare.items():
            s = s.replace(ko, en)
        s = re.sub(r'(\{0[89A]\})* *「\{1A\}」(을|를|\(을\)를)?', '{NAME}', s)
        s = re.sub(r'\{1B0[1-7]\}', '{NAME}', s)                  # item-name code with brackets/centring/particle
        s = re.sub(r'(\{0[89A]\}|\{0B[0-9A-F]{2}\})+ *([「『])', r'{TAB}\2', s)   # banner lines are re-centred
        s = re.sub(r'([가-힣]) ([님씨])', r'\1\2', s)              # 마리오 님 / 마리오 씨
        return re.sub(r'([「『])[^」』]*([」』])', r'\1\2', s)
    diff = [i for i in range(len(so)) if so[i] != sn[i]]
    ad = dialogue.all_addresses(old)
    fixes = json.loads((Path(__file__).resolve().parents[2] / 'data/dialogue_fixes.json').read_text())
    fixed_addr = {ad[int(f['id'], 16)] for f in fixes if f['where'] == 'dialogue'}
    bad = [i for i in diff if norm(so[i]) != norm(sn[i]) and ad[i] not in fixed_addr]
    print(f'dialogues changed: {len(diff)}, outside brackets: {len(bad)}')
    for i in bad[:5]:
        print(f'  {i:03X} old: {so[i][:80]}\n      new: {sn[i][:80]}')
    left = {}
    for i, s in enumerate(sn):
        for m in re.finditer(r'([A-Z][A-Z ]{2,}[A-Z])', s):
            left.setdefault(m.group(1), []).append(f'{i:03X}')
    print('English words left:', ', '.join(f'{w}({len(v)})' for w, v in sorted(left.items())))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
