"""Patch-note images in the style of the Super Gokuden 2 release notes: one
image per topic, a row per version (labels on the left), a column per scene,
2x scale. For text fixes the changed area is boxed in red on both rows (taken
from the pixels that differ between the two screens).

usage: patchnote_compose.py        (reads docs/patchnotes/shots/*_v1|_before|_new.png)
Writes docs/patchnotes/<topic>.png and docs/patchnotes/preview.md.
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / 'docs/patchnotes/shots'
OUT = ROOT / 'docs/patchnotes'
FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'

# topic: (title, [scenes], highlight changes, labels, explanation)
TOPICS = [
    ('names-shop', '아이템 이름 한글화 (상점)', ['shop_buy', 'shop_sell'], False, ('v1.0', 'v1.1'),
     '상점 구매·판매 목록의 영문 아이템명(MUSHROOM, PICK ME UP …)이 한글(버섯, 부활드링크 …)로 나옵니다.'),
    ('names-battle', '아이템·적 이름 한글화 (전투)', ['battle_weapon', 'battle_item_list', 'battle_item_target'], False,
     ('v1.0', 'v1.1'), '공격 대상 창의 적 이름·무기(GOOMBA/HAMMER → 굼바/해머), 전투 아이템 목록과 사용 대상 창이 한글로 나옵니다.'),
    ('specials', '필살기 이름 한글화', ['special_battle', 'special_field'], False, ('v1.0', 'v1.1'),
     '전투와 필드 메뉴의 필살기 목록이 영문(THUNDER, HP RAIN)에서 한글(번개찌리릿, 회복샤워)로 나옵니다.'),
    ('result-window', '전투 결과 창 한글화', ['result_short', 'result_honey', 'result_long_juice'], False, ('v1.0', 'v1.1'),
     '획득 아이템 이름이 영문(MUSHROOM, HONEYSYRUP, ABLE JUICE)에서 한글로 나옵니다.'),
    ('particles-levelup', '조사 자동 선택 (레벨업)', ['levelup_level', 'levelup_level_ga', 'levelup_skill', 'levelup_skill_eul'],
     True, ('v1.0', 'v1.1'), '"레벨3(이)가", "(을)를 배웠습니다" 대신 숫자·이름에 맞는 조사가 붙습니다: 레벨3이 / 레벨4가 / 회복샤워를 / 파이어볼을. '
     '기술 이름도 한글로 나옵니다.'),
    ('particles-shop', '조사 자동 선택 (대사 속 아이템명)', ['dlg_F0C_item60_1', 'dlg_F0C_item66_1'], True, ('v1.0', 'v1.1'),
     '대사에 들어가는 아이템 이름이 한글로 나오고, 받침에 따라 을/를이 바뀝니다: 「버섯」을 / 「부활드링크」를.'),
    ('honorific', '호칭 정리', ['toad_tutorial'], True, ('v1.0', 'v1.1'),
     '존댓말 화자의 "마리오에게" → "마리오 님에게". 들고 있는 아이템 이름(MUSHROOM → 버섯)도 한글로 나옵니다.'),
    ('typo', '오타 수정', ['croco_bw3', 'typo_castle_toad'], True, ('v1.0', 'v1.1'),
     '여기까리 → 여기까지 / 기운이 느져요 → 기운이 느껴져요 (빨간 상자가 바뀐 곳)'),
    ('spelling', '맞춤법 수정', ['typo_moleville_song', 'typo_moleville_peach'], True, ('v1.0', 'v1.1'),
     '잘 못 들었나 → 잘못 들었나 / 라던지 → 라든지 (사진). 그 밖에 79곳: 거에요 → 거예요, 모자르다 → 모자라다, '
     '잠궈 → 잠가, 안되요 → 안돼요, 숨바꼭찔 → 숨바꼭질, 갯수 → 개수, 악세사리 → 액세서리, 헤메다 → 헤매다, '
     '줏어 → 주워, 혼자말 → 혼잣말, 케릭터 → 캐릭터 등.'),
    ('mistranslation', '오역 수정 (일본판 대조)', ['mistrans_iga_valley'], True, ('v1.0', 'v1.1'),
     '이가 언덕 → 이가 계곡 (일본판 イガ谷, 谷 = 골짜기)'),
    ('banner', '획득 메시지 가운데 정렬', ['item_banner_static', 'item_banner_dynamic'], ('centre',), ('일본판', 'v1.0', 'v1.1'),
     '노란 선이 화면 가운데, 빨간 상자가 문구입니다. 왼쪽: 일본판은 가운데였는데 v1.0은 영문 MUSHROOM으로 바꾸면서 오른쪽으로 '
     '밀렸습니다. 오른쪽: 이름이 바뀌어 들어가는 문구는 일본판·v1.0 모두 왼쪽으로 치우쳐 있었습니다. v1.1은 둘 다 가운데입니다.'),
    ('restored', 'V1.0에서 빠진 대사 복구', ['frog_coin_restore'], False, ('v1.0', 'v1.1'),
     '두더지 마을 양동이 소녀에게 카보쿠키를 주면 V1.0은 아무 메시지 없이 넘어갔습니다. 이제 "개구리 코인 획득!"이 나옵니다.'),
]

# Fixes for things the Japanese original already did (compared with it).
ORIGINAL = [
    ('result-jp', '전투 결과 창 배치 (일본 원판과 비교)', ['result_short', 'result_honey', 'result_long_juice'], ('box', 68, 93, 197, 130),
     ('일본판', 'v1.1'),
     '일본 원판은 이름 길이와 관계없이 "아이템" 다음 줄 왼쪽에 둡니다. v1.1은 숫자 끝에 맞춰 오른쪽 정렬하고, '
     '5자 이하는 같은 줄에 놓아 창을 한 줄 줄입니다. 6자 이상(리프레시주스)은 다음 줄에 놓아 창이 4줄 그대로입니다.'),
    ('special-hint', '필살기 화면 다음 기술 안내 문구', ['special_field', 'special_hint_mario'], ('box', 10, 155, 122, 206),
     ('일본판', 'v1.1'), '일본 원판부터 이름 칸 길이 때문에 "マロ　　が…"처럼 이름 뒤에 빈칸이 생겼습니다(v1.0도 "마로   가"). '
     '이제 "마로는 / 레벨 6이 되면 / 새로운 기술을 배웁니다"처럼 자연스러운 문장으로 나오고, 레벨에 따라 이/가가 바뀝니다(레벨 14가).'),
]

SCALE = 2
GAP = 8
LABEL_W = 110
BG = (24, 24, 28)


TAG = {'일본판': 'jp', 'v1.1': 'new'}


def shot(scene, label):
    if label in TAG:
        return SHOTS / f'{scene}_{TAG[label]}.png'
    return before_file(scene)


def before_file(scene):
    for tag in ('v1', 'before'):
        p = SHOTS / f'{scene}_{tag}.png'
        if p.exists():
            return p
    raise FileNotFoundError(scene)


def is_text(p):
    """Glyph pixels: dark dialogue text, white banner text, navy level-up text."""
    r, g, b = p
    return r + g + b < 140 or min(p) > 215 or (b > 100 and r < 70 and g < 70)


def text_mask(img):
    m = Image.new('1', img.size)
    m.putdata([is_text(p) for p in img.getdata()])
    return m


def changed_boxes(a, b, min_w):
    """Boxes around the words whose text differs between the screens. Only
    glyph-coloured pixels count, so animated backgrounds are ignored; a box
    is widened to the word around the change (a gap of 6 px or more ends a
    word); min_w drops narrower changes (the level-up screen's bobbing sprite)."""
    ma, mb = text_mask(a), text_mask(b)
    diff = ImageChops.logical_xor(ma, mb)
    w, h = diff.size
    px = diff.load()
    rows = [y for y in range(h) if any(px[x, y] for x in range(w))]
    raw, start, prev = [], None, None
    for y in rows + [None]:
        if start is not None and (y is None or y - prev > 4):
            xs = [x for yy in range(start, prev + 1) for x in range(w) if px[x, yy]]
            if max(xs) - min(xs) >= min_w:
                raw.append((min(xs), start, max(xs), prev))
            start = None
        if y is not None:
            if start is None:
                start = y
            prev = y
    boxes = []
    for x0, y0, x1, y1 in raw:
        # word extent from the changed rows only: the rows above or below can
        # hold a window border that would join every word on the line
        ink = [False] * w
        for img in (a, b):
            band = img.crop((0, y0, w, y1 + 1))
            bg = max(band.getcolors(w * (y1 - y0 + 1)))[1]     # the band's background colour
            bp = band.load()
            for x in range(w):
                ink[x] = ink[x] or any(bp[x, y] != bg and is_text(bp[x, y]) for y in range(y1 - y0 + 1))
        y0, y1 = max(0, y0 - 6), min(h - 1, y1 + 4)        # box the whole glyph row

        def edge(x, step):
            gap = 0
            while 0 <= x + step < w and gap < 6:
                x += step
                gap = 0 if ink[x] else gap + 1
            return x - step * gap

        boxes.append((edge(x0, -1) - 3, y0 - 1, edge(x1, 1) + 3, y1 + 1))
    return boxes


def banner_box(img):
    """Extent of the white banner text in the lower part of the screen."""
    xs, ys = [], []
    for y in range(150, 224):
        for x in range(256):
            if min(img.getpixel((x, y))) > 200:
                xs.append(x)
                ys.append(y)
    return min(xs) - 3, min(ys) - 3, max(xs) + 3, max(ys) + 3


def compose(title, scenes, highlight, labels):
    font = ImageFont.truetype(FONT, 30)
    cols, rows = len(scenes), len(labels)
    w, h = 256 * SCALE, 224 * SCALE
    img = Image.new('RGB', (LABEL_W + cols * (w + GAP), rows * (h + GAP) + GAP), BG)
    d = ImageDraw.Draw(img)
    for r, label in enumerate(labels):
        d.text((14, GAP + r * (h + GAP) + h // 2 - 18), label, fill=(235, 235, 235), font=font)
    for c, scene in enumerate(scenes):
        shots = [Image.open(shot(scene, label)).convert('RGB') for label in labels]
        centre = isinstance(highlight, tuple) and highlight[0] == 'centre'
        if centre:
            boxes = []
        elif isinstance(highlight, tuple) and highlight[0] == 'box':
            boxes = [highlight[1:]]      # fixed box: rows differ everywhere (different languages)
        else:
            boxes = changed_boxes(shots[-2], shots[-1], 30 if 'levelup' in scene else 2) if highlight else []
        if isinstance(highlight, tuple) and highlight[0] not in ('box', 'centre'):
            rx0, ry0, rx1, ry1 = highlight
            # inside the region only, widened to its left edge so the name is boxed too
            boxes = [(rx0, b[1], b[2], b[3]) for b in boxes if b[0] >= rx0 - 8 and b[1] >= ry0 and b[2] <= rx1 and b[3] <= ry1]
        for r, im in enumerate(shots):
            big = im.resize((w, h), Image.NEAREST)
            bd = ImageDraw.Draw(big)
            for x0, y0, x1, y1 in (banner_box(im),) if centre else boxes:
                bd.rectangle((x0 * SCALE, y0 * SCALE, x1 * SCALE, y1 * SCALE), outline=(255, 40, 40), width=4)
            if centre:
                for y in range(0, h, 12):
                    bd.line((w // 2, y, w // 2, y + 6), fill=(255, 220, 0), width=2)
            img.paste(big, (LABEL_W + c * (w + GAP), GAP + r * (h + GAP)))
    return img


def main():
    md = ['# 슈퍼 마리오 RPG 한글패치 v1.1 패치노트 이미지', '',
          '행마다 왼쪽에 버전 표시(일본판 / v1.0 / v1.1). 빨간 상자는 글자가 바뀐 곳.', '']
    for part, topics in (('v1.0 대비 개선', TOPICS), ('일본 원판부터 있던 부분 개선', ORIGINAL)):
        md += [f'# {part}', '']
        for name, title, scenes, highlight, labels, text in topics:
            compose(title, scenes, highlight, labels).save(OUT / f'{name}.png')
            md += [f'## {title}', '', text, '', f'![{name}]({name}.png)', '']
            print(name)
    (OUT / 'preview.md').write_text('\n'.join(md), encoding='utf-8')


if __name__ == '__main__':
    main()
