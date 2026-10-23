"""Before/after screenshots for the patch notes.

usage: patchnote_shots.py [scene ...]     (default: all scenes)
Runs every scene on the V1.0 ROM and on build/smrpg_kr_item.sfc with the same
inputs and saves each screen separately at native size, <scene>_v1.png and
<scene>_new.png. Patch-note shots must look like real play, so scenes that poke
RAM (forced drops, raised EXP, extra items, learned specials) are VERIFY-only
and go to test/out/verify_shots instead of docs/patchnotes/shots.
"""
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/patchnotes/shots'
VERIFY_OUT = ROOT / 'test/out/verify_shots'
# Scenes with RAM pokes or derived states: not real play, never in the patch notes.
VERIFY = {'field_items', 'field_equip', 'result_long', 'levelup_10', 'levelup_12',
          'levelup_skill_ext'} | {f'result_len{n}' for n in range(2, 9)}
WORK = ROOT / 'test/out/patchnotes'
ROMS = {'before': ROOT / 'rom/smrpg_kr_v1.sfc', 'after': ROOT / 'build/smrpg_kr_item.sfc', 'jp': ROOT / 'rom/smrpg_jp.sfc'}
# Scenes also shot on the Japanese original (<scene>_jp.png): layouts that the
# English names of V1.0 hide.
JP = {'result_short', 'result_honey', 'result_long_juice', 'special_field', 'special_hint_mario'}
# Scenes compared against this patch with one change switched off instead of
# V1.0 (tools/make_harness.sh builds them); saved as <scene>_before.png.
BEFORE_ROM = {'result_short_ui': ROOT / 'build/noresui.sfc', 'result_honey_ui': ROOT / 'build/noresui.sfc'}
# Scenes reached through a redirected room exit (tools/py/scene_rom.py): (V1.0, this patch).
SCENE_ROMS = {name: (ROOT / f'build/scene_{rom}_v1.sfc', ROOT / f'build/scene_{rom}.sfc') for name, rom in {
    'frog_coin_restore': 'molev', 'typo_moleville_song': 'molev_n5', 'typo_moleville_peach': 'molev_n0',
    'mistrans_iga_valley': 'molev_n4', 'typo_castle_toad': 'castle_toad'}.items()}



def seq(*parts):
    return ','.join(parts)


def rep(n, step):
    return ','.join([step] * n)


def poke_list(base, ids):
    return ';'.join(f'7FF8{base + i:02X}={v}' for i, v in enumerate(ids))


ITEM_SEQ = 'x:3,wait:60,a:3,wait:60'
EQUIP_SEQ = 'x:3,wait:60,down:3,wait:10,down:3,wait:10,down:3,wait:10,a:3,wait:60,a:3,wait:60'
ITEMS = [f'{0x60 + i:02X}' for i in range(30)]
EQUIP = [f'{0x05 + i:02X}' for i in range(30)]
BATTLE_WIN = seq('wait:7', rep(6, 'a:3,wait:12'))
# Mario defends (B, B), Mallow casts his third special (Y ... Y) on the enemy and
# the timed Y press succeeds. State from tools/make_states.sh.
THOUGHT_PEEK = ('up:90,wait:260,b:3,wait:40,b:3,wait:150,y:3,wait:90,down:4,wait:25,down:4,wait:25,'
                'y:3,wait:60,y:3,wait:230,y:3,wait:300')
# Pre-battle state with Mario's and Mallow's EXP raised (tools/make_states.sh).
LEVEL_UPS = seq('up:90,wait:260,a:3,wait:40,a:3,wait:400', rep(160, 'a:3,wait:50'))
# Bandit's Way 5: the chase cutscene, then the third catch (catch counter $7032
# is incremented before the check against 3) runs the boss-fight cutscene.
CROCO_CAUGHT = seq('left:20,down:120,wait:200', rep(8, 'a:3,wait:60'), 'wait:200', rep(14, 'a:3,wait:60'))
# Arrive in front of a Moleville NPC (scene_rom.py molev_nX) and talk.
MOLE_TALK = seq('left:20,down:120,wait:120,a:3,wait:80', rep(6, 'a:3,wait:80'))
# One win from tools/make_states.sh lvup_next: Mario reaches level 3 and
# learns Fire Orb, Mallow reaches level 4.
LEVEL_NEXT = seq('up:90,wait:260,a:3,wait:40,a:3,wait:400', rep(60, 'a:3,wait:50'))
LEVEL_UP = seq('wait:5', rep(10, 'a:3,wait:12'), 'wait:300', rep(8, 'a:3,wait:60'))

# name: (state, input sequence, frame to keep ('end' or qNNNNN), env, caption)
# A state saved inside a menu keeps the glyphs of the ROM it was saved with.
SHOP_OPEN = 'wait:5,a:3,wait:40,a:3,wait:40,a:3,wait:40,a:3,wait:40'

SCENES = {
    'field_items': ('keep_control', ITEM_SEQ, 'end', {'POKE': '003112=FF;' + poke_list(0x82, ITEMS)},
                    '필드 아이템 메뉴: 아이템 이름 한글화'),
    'field_equip': ('keep_control', EQUIP_SEQ, 'end', {'POKE': '003112=FF;' + poke_list(0x64, EQUIP)},
                    '필드 장비 메뉴: 장비 이름 한글화'),
    'shop_buy': ('shop', SHOP_OPEN + ',a:3,wait:60', 'end', {}, '상점 구매 목록'),
    'shop_sell': ('shop', SHOP_OPEN + ',down:3,wait:15,a:3,wait:80', 'end', {}, '상점 판매 목록'),
    'toad_tutorial': ('user_4', seq('a:3', rep(6, 'wait:30,a:3'), 'wait:40,x:3', rep(30, 'wait:35,a:3')), 'q01215', {},
                      '키노피오 메뉴 튜토리얼: 들고 있는 아이템 이름, "마리오 님에게"'),
    'battle_weapon': ('user_1e', 'wait:5,a:3,wait:40', 'end', {}, '전투 공격 대상 창: 적 이름과 무기 아이콘·이름'),
    'item_banner_dynamic': ('user_1d', seq('wait:3', rep(12, 'a:3,wait:40')), 'best:60-260', {},
                            '아이템 획득 배너: 이름 길이에 맞춘 가운데 정렬'),
    'item_banner_static': ('item_get', seq('wait:3', rep(8, 'a:3,wait:40')), 'best:45-200', {},
                           '아이템 획득 배너 (고정 문구) 가운데 정렬'),
    'result_short': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {},
                     '전투 결과: 짧은 아이템 이름은 같은 줄 오른쪽 정렬, 창 한 줄 축소'),
    'result_honey': ('user_1h', seq('wait:5', rep(10, 'a:3,wait:12'), 'wait:350'), 'end', {},
                     '전투 결과: 허니시럽'),
    'result_long': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=06;7EFA07=00'},
                    '전투 결과: 긴 아이템 이름은 다음 줄 (드롭 아이템을 강제로 바꿔 촬영)'),
    'result_len2': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=05;7EFA07=00'},
                     '전투 결과: 2글자 이름 (해머, 드롭 아이템을 강제로 바꿔 촬영)'),
    'result_len3': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=09;7EFA07=00'},
                     '전투 결과: 3글자 이름 (핑거샷, 드롭 아이템을 강제로 바꿔 촬영)'),
    'result_len4': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=0D;7EFA07=00'},
                     '전투 결과: 4글자 이름 (왕왕허물, 드롭 아이템을 강제로 바꿔 촬영)'),
    'result_len5': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=08;7EFA07=00'},
                     '전투 결과: 5글자 이름 (펀치글러브, 드롭 아이템을 강제로 바꿔 촬영)'),
    'result_len6': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=15;7EFA07=00'},
                     '전투 결과: 6글자 이름 (슈퍼더블펀치, 드롭 아이템을 강제로 바꿔 촬영)'),
    'result_len7': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=06;7EFA07=00'},
                     '전투 결과: 7글자 이름 (개굴개굴지팡이, 드롭 아이템을 강제로 바꿔 촬영)'),
    'result_len8': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=50;7EFA07=00'},
                     '전투 결과: 8글자 이름 (당신을넘고싶어서, 드롭 아이템을 강제로 바꿔 촬영)'),
    'result_long_juice': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {'POKE': '7EFA06=67;7EFA07=00'},
                          '전투 결과: 긴 이름(6자 이상)은 다음 줄 오른쪽 정렬 (리프레시주스: 잡몹이 흔히 떨어뜨리는 아이템으로 드롭만 지정)'),
    'result_short_ui': ('user_1f', seq(BATTLE_WIN, 'wait:400'), 'end', {},
                        '전투 결과 창 배치 개선 전/후 (둘 다 한글 이름): 버섯'),
    'result_honey_ui': ('user_1h', seq('wait:5', rep(10, 'a:3,wait:12'), 'wait:350'), 'end', {},
                        '전투 결과 창 배치 개선 전/후 (둘 다 한글 이름): 허니시럽'),
    'croco_bw3': ('derived/croco_bw3_unseen', 'left:20,down:120,wait:300', 'end', {'ROOM': '004D'},
                  '오타 수정: 크로코 "여기까리 → 여기까지" (산적의 길, 구역에 다시 들어와 컷신 재생)'),
    'typo_moleville_song': ('prebattle', MOLE_TALK, 'q00660', {'RUNNER': 'warp'},
                            '오타 수정: 두더지 마을 "잘 못 들었나?" → "잘못 들었나?"'),
    'typo_moleville_peach': ('prebattle', MOLE_TALK, 'q00580', {'RUNNER': 'warp'},
                             '오타 수정: 두더지 마을 "피치 공주라던지" → "피치 공주라든지"'),
    'mistrans_iga_valley': ('derived/molev_secret_open', MOLE_TALK, 'q00420', {'RUNNER': 'warp'},
                            '오역 수정: "이가 언덕" → "이가 계곡" (일본판 イガ谷)'),
    'typo_castle_toad': ('derived/castle_after_mack', 'left:20,down:120,wait:120,a:3,wait:80,a:3,wait:80', 'q00400',
                         {'RUNNER': 'warp'}, '오타 수정: 버섯성 공주 방 키노피오 "기운이 느져요" → "느껴져요"'),
    'frog_coin_restore': ('derived/molev_cookie', seq('left:20,down:120,wait:120,a:3,wait:90', rep(4, 'a:3,wait:70')),
                          'best:540-600', {'RUNNER': 'warp'},
                          '빈 대사 복구: 두더지 마을 양동이 소녀에게 카보쿠키를 주면 "개구리 코인 획득!" (V1.0은 아무것도 안 나옴)'),
    'special_battle': ('prebattle', 'up:90,wait:260,b:3,wait:40,b:3,wait:150,y:3,wait:90', 'end', {},
                       '전투 필살기 목록: 기술 이름 한글화'),
    'special_field': ('prebattle', 'wait:10,x:3,wait:60,down:3,wait:10,down:3,wait:10,a:3,wait:60,down:3,wait:20,a:3,wait:60',
                      'end', {}, '필드 메뉴 필살기 목록: 기술 이름 한글화'),
    'special_hint_mario': ('prebattle', 'wait:10,x:3,wait:60,down:3,wait:10,down:3,wait:10,a:3,wait:60', 'end', {},
                           '필드 필살기 화면: "마리오가 기술을 배우는"'),
    'battle_item_list': ('user_1h', 'wait:50,x:3,wait:80,x:3,wait:60,x:3,wait:200', 'q00120', {},
                         '전투 아이템 목록 (battle list items are confirmed with the button that opened them)'),
    'battle_item_target': ('user_1h', 'wait:50,x:3,wait:80,x:3,wait:60,x:3,wait:200', 'q00180', {},
                           '전투 아이템 사용 대상 창'),
    'thought_peek': ('derived/thought_peek', THOUGHT_PEEK, 'q01260', {},
                     '무슨 생각하니(사이코패스): "캐릭터" 맞춤법 (타임드 히트 성공 시 표시)'),
    'levelup_10': ('derived/lvup_many', LEVEL_UPS, 'q03425', {}, '레벨업: "레벨10이" (여러 번 연속 레벨업)'),
    'levelup_12': ('derived/lvup_many', LEVEL_UPS, 'q03900', {}, '레벨업: "레벨12가"'),
    'levelup_skill_ext': ('derived/lvup_many', LEVEL_UPS, 'q06300', {},
                          '레벨업: "천둥콰르릉을 배웠습니다" (폰트에 없던 "릉"은 확장 글리프)'),
    'levelup_level_ga': ('derived/lvup_next', LEVEL_NEXT, 'q02175', {}, '레벨업: "마로가 레벨4가 됐습니다" (숫자에 맞는 조사)'),
    'levelup_skill_eul': ('derived/lvup_next', LEVEL_NEXT, 'q01950', {}, '레벨업: "파이어볼을 배웠습니다" (받침에 맞는 을/를)'),
    'levelup_level': ('user_1h', LEVEL_UP, 'q00640', {}, '레벨업: "레벨3이 됐습니다" (숫자에 맞는 조사)'),
    'levelup_skill': ('user_1h', LEVEL_UP, 'q00740', {}, '레벨업: 기술 이름 한글화와 을/를'),
}


def capture(scene, which):
    state, inputs, frame, env, _ = SCENES[scene]
    out = WORK / scene / which
    # q frames are saved every N frames; N must divide the wanted frame number.
    # 'best:A-B' keeps the frame in A..B with the most white text: the ROMs
    # show the same banner at different frames.
    if frame.startswith('best:'):
        every = 5
    else:
        every = 1000 if frame == 'end' else next(n for n in (20, 15, 25, 10) if int(frame[1:]) % n == 0)
    rom = BEFORE_ROM.get(scene, ROMS['before']) if which == 'before' else ROMS[which if which == 'jp' else 'after']
    if scene in SCENE_ROMS:
        rom = SCENE_ROMS[scene][0 if which == 'before' else 1]
    if 'ROOM' in env or env.get('RUNNER') == 'warp':
        # Room changes go to ROOM (test/warp_seq.lua): re-enter a room to replay its cutscene.
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(ROOT / 'tools/Mesen.app/Contents/MacOS/Mesen'), '--testrunner', str(rom),
                        str(ROOT / 'test/warp_seq.lua')], cwd=ROOT,
                       env={**os.environ, **env, 'LIBDIR': str(ROOT / 'test'), 'STATE': str(ROOT / f'test/states/{state}.mss'),
                            'SEQ': inputs, 'EVERY': str(every), 'SHOT_DIR': str(out)},
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        for f in out.glob('w*.png'):
            f.rename(out / ('q' + f.name[1:]))
    else:
        subprocess.run(['tools/run_seq.sh', str(rom), str(ROOT / f'test/states/{state}.mss'), str(out),
                        inputs, str(every), '1'],
                       cwd=ROOT, env={**os.environ, **env, 'SHOTS': '0' if frame == 'end' else '1'},
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if frame.startswith('best:'):
        a, b = map(int, frame[5:].split('-'))
        cands = [out / f'q{f:05d}.png' for f in range(a, b + 1, every)]
        cands = [c for c in cands if c.exists()]
        if not cands:
            sys.exit(f'{scene}/{which}: no frames in {frame}')
        return max(cands, key=lambda c: white_text(Image.open(c).convert('RGB'))).read_bytes()
    path = out / ('end.png' if frame == 'end' else f'{frame}.png')
    if not path.exists():
        sys.exit(f'{scene}/{which}: {path.name} not captured')
    return path.read_bytes()


def white_text(img):
    """White banner text near the bottom plus dark text in a dialogue box at the top."""
    white = sum(1 for y in range(100, 224, 2) for x in range(0, 256, 2) if min(img.getpixel((x, y))) > 200)
    dark = sum(1 for y in range(8, 72, 2) for x in range(8, 248, 2) if sum(img.getpixel((x, y))) < 180)
    return white + dark


def main():
    names = sys.argv[1:] or list(SCENES)
    OUT.mkdir(parents=True, exist_ok=True)
    for name in names:
        out = VERIFY_OUT if name in VERIFY else OUT
        out.mkdir(parents=True, exist_ok=True)
        tag = 'before' if name in BEFORE_ROM else 'v1'
        (out / f'{name}_{tag}.png').write_bytes(capture(name, 'before'))
        (out / f'{name}_new.png').write_bytes(capture(name, 'after'))
        if name in JP:
            (out / f'{name}_jp.png').write_bytes(capture(name, 'jp'))
        print(name)
    index = ['# 패치노트 스크린샷', '', '장면마다 V1.0(`_v1`)과 이번 패치(`_new`)를 같은 입력으로 찍은 원본 크기(256x224) 이미지.', '']
    for name, scene in SCENES.items():
        if name not in VERIFY and (OUT / f'{name}_new.png').exists():
            before = f'- 개선 전: `{name}_before.png`' if name in BEFORE_ROM else f'- V1.0: `{name}_v1.png`'
            index += [f'## {scene[4]}', '', before, f'- 이번 패치: `{name}_new.png`', '']
    (OUT / 'index.md').write_text('\n'.join(index), encoding='utf-8')


if __name__ == '__main__':
    main()
