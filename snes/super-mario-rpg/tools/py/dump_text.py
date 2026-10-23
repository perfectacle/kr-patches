"""Dump all Korean V1.0 text as readable lines for review.

usage: dump_text.py ROM DLG_TBL_JSON OUT_DIR
Writes OUT_DIR/dialogue.txt (one dialogue per line, "ID<TAB>text") and
OUT_DIR/other.txt (battle dialogue, battle messages, item descriptions, menu texts,
enemy attack names). Control codes are shown as {XX}; line breaks as " / ".
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dialogue  # noqa: E402
import dlg_rewrite  # noqa: E402

READABLE = {'00': ' ▶ ', '01': ' / ', '02': ' ▶/ ', '03': ' ▶▶ ', '04': ' ▶▶ ', '05': ' ▶ ', '06': ''}


def text(data, rev):
    out = []
    for t in dlg_rewrite.tokens(data):
        k = t.hex().upper()
        if k in READABLE:
            out.append(READABLE[k])
        elif k in rev and len(rev[k]) == 1:
            out.append(rev[k])
        else:
            out.append('{%s}' % k)
    return ''.join(out).strip()


def until(data, terms):
    for i, t in enumerate(dlg_rewrite.tokens(data)):
        if t[0] in terms and len(t) == 1:
            return b''.join(dlg_rewrite.tokens(data)[:i])
    return data


def main():
    rom = Path(sys.argv[1]).read_bytes()
    enc = {k: bytes.fromhex(v) for k, v in json.loads(Path(sys.argv[2]).read_text()).items()}
    rev = {v.hex().upper(): k for k, v in enc.items()}
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)

    ad = dialogue.all_addresses(rom)
    seen = {}
    lines = []
    for i, a in enumerate(ad):
        if a in seen:
            continue
        seen[a] = i
        g = i >> 9
        same = sorted({x for k, x in enumerate(ad) if k >> 9 == g})
        k = same.index(a)
        end = same[k + 1] if k + 1 < len(same) else a + 400
        t = text(until(rom[a:end], (0x06,)), rev)
        if t.replace('▶', '').strip():
            lines.append(f'{i:03X}\t{t}')
    (out / 'dialogue.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    other = []
    ptr = lambda tab, n, base: [base | int.from_bytes(rom[tab + i * 2:tab + i * 2 + 2], 'little') for i in range(n)]
    for i, a in enumerate(ptr(0x396554, 256, 0x390000)):
        other.append(f'battle_dialogue {i:02X}\t{text(until(rom[a:a + 300], (0x00,)), rev)}')
    for i, a in enumerate(ptr(0x3A26F1, 46, 0x3A0000)):
        other.append(f'battle_message {i:02X}\t{text(until(rom[a:a + 200], (0x00,)), rev)}')
    for i, a in enumerate(ptr(0x3A2F20, 0xB1, 0x3A0000)):
        other.append(f'item_description {i:02X}\t{text(until(rom[a:a + 200], (0x00,)), rev)}')
    for i in range(118):
        a = 0x3EF000 + int.from_bytes(rom[0x3EEF00 + i * 2:0x3EEF02 + i * 2], 'little')
        other.append(f'menu_text {i:02X}\t{text(until(rom[a:a + 200], (0x00,)), rev)}')
    psy = [0x390000 | int.from_bytes(rom[0x399411 + i * 2:0x399413 + i * 2], 'little') for i in range(256)]
    for i, a in enumerate(psy):
        if 0x39961E <= a < 0x39A581:
            other.append(f'psychopath {i:02X}\t{text(until(rom[a:a + 200], (0x00,)), rev)}')
    for i in range(0x40, 0x68):
        other.append(f'enemy_attack {i:02X}\t{text(rom[0x3A137F + i * 15 + 1:0x3A137F + i * 15 + 11], rev)}')
    (out / 'other.txt').write_text('\n'.join(other) + '\n', encoding='utf-8')
    print(f'{len(lines)} dialogues, {len(other)} other lines')


if __name__ == '__main__':
    main()
