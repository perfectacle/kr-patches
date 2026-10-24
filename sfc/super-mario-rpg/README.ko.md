# 슈퍼 마리오 RPG(SFC) 한글패치 v1.3

[English](README.md) | 한국어

일본판 슈퍼 패미콤 *슈퍼 마리오 RPG* 한글패치 v1.3 의 소스입니다. v1.3 은 한글판
v1.0 패치 위에 빌드합니다. 아이템·스페셜·적 이름을 바꾸고, v1.0 대사에 남아
있던 영어 아이템 이름을 다시 쓰고, 전투 결과 창과 그 밖의 메뉴를 고칩니다(v1.2 까지).
v1.3 은 이름 입력 화면을 자모를 골라 조합하는 한 페이지 화면으로 바꿨습니다.

패치 페이지: <https://perfectacle.github.io/games/kr-patches/sfc/super-mario-rpg/>

롬 배치, 메모리, 텍스트·폰트 형식, 훅, 사용한 빈 공간, 디버그 기능은
[docs/ANALYSIS.ko.md](docs/ANALYSIS.ko.md) 에 정리했습니다.

## 원본 롬

롬은 들어 있지 않습니다. 직접 덤프한 일본판 카트리지 롬을 쓰세요.

| | |
| --- | --- |
| 헤더 제목 | `SUPER MARIO RPG`(SA-1, 4,194,304바이트, 카피어 헤더 없음) |
| CRC32 | `5527071E` |
| SHA-1 | `a9cd97041c4f8acf135d1ffb0a172748b5b976de` |

빌드는 이 롬에 v1.0 패치(`v1.0/Super Mario RPG (K) (V1.0).ips`)를 적용한
롬에서 시작합니다.

| | |
| --- | --- |
| 헤더 제목 | `SUPER MARIO RPG (K)` |
| CRC32 | `F4305A06` |
| SHA-1 | `271370449e0f5910684172d1bf6aa4c5671822dd` |

## 빌드

준비물: 저장소의 Python 환경(최상위 README 참고),
[asar](https://github.com/RPGHacker/asar) 1.91, zsh.

1. 일본판 롬을 `rom/smrpg_jp.sfc` 에 두고 v1.0 롬을 만듭니다.

   ```sh
   ../../.venv/bin/krpatch ips apply rom/smrpg_jp.sfc "v1.0/Super Mario RPG (K) (V1.0).ips" rom/smrpg_kr_v1.sfc
   ```

2. asar 실행 파일을 `tools/asar` 에 둡니다.
3. `build/test.sfc`(CRC32 `50F235C2`)를 빌드합니다.

   ```sh
   zsh tools/make.sh
   ```

4. 일본판 롬을 기준으로 IPS 를 만듭니다. 배포한 패치는 레코드 gap 7 로
   만들었으므로, 결과가 바이트 단위로 같도록 그 값을 그대로 씁니다.

   ```sh
   ../../.venv/bin/krpatch ips make --gap 7 rom/smrpg_jp.sfc build/test.sfc v1.3.ips --headered v1.3_headered.ips
   ```

`tools/make.sh` 가 돌리는 것:

- `tools/build.py`: 이름 표, 동적 글리프, 다시 쓰는 대사 폰트 코드, 레벨업·
  스페셜 화면 문자열, 이름 입력 화면의 글리프·표(`tools/py/name_entry.py`)(`build/`).
- `tools/py/dlg_rewrite.py`: 다시 쓴 대사를 담은 `build/dialogue.asm`.
- v1.0 롬 사본에 asar `--fix-checksum=on src/main.asm`.
- `tools/py/check_menu_names.py`: 모든 이름을 메뉴가 그리는 글리프와
  대조합니다. 맞지 않으면 빌드가 실패합니다.

다른 환경을 쓰려면 `PYTHON`(테스트 스크립트는 `KRPATCH` 도)을 지정하세요.

## 구성

| 경로 | 내용 |
| --- | --- |
| `src/main.asm`, `src/name_entry.asm` | 패치(asar), 이름 입력·파일 선택 화면 |
| `data/` | 이름, 대사 수정, 코드표(`data/tbl/korTBL*.tbl` 은 v1.0 코드표) |
| `tools/build.py`, `tools/py/` | 빌드 단계, 텍스트 덤프·검증, 패치 노트 스크린샷 |
| `tools/*.sh` | 빌드, 테스트 롬, MesenCE 테스트 실행 |
| `test/` | 테스트 전용 asar 훅(`test/harness/`), 이 게임용 MesenCE 스크립트, 픽스처 |
| `compat/` | 여러 에뮬레이터에 같은 입력 재생(`compat/run_all.sh`) |
| `v1.0/` | 빌드의 출발점인 v1.0 패치 |
| `tools/fonts/galmuri/` | Galmuri 글꼴(SIL Open Font License 1.1, `LICENSE.txt`) |

## 테스트

- `tools/make.sh` 가 `check_menu_names.py` 를 돌립니다. 에뮬레이터는 필요
  없습니다.
- `tools/test_menu.sh`, `tools/run_seq.sh`, `tools/make_states.sh` 와 패치 노트
  스크립트는 `tools/Mesen.app` 의 MesenCE 와 `test/states/*.mss` 세이브
  스테이트가 필요하며, 이것들은 들어 있지 않습니다.
- 범용 MesenCE 스크립트(`lib.lua`, `seq.lua`, `poke_state.lua`, `script.lua`,
  `dumpsrm.lua`)는 툴킷에서 가져옵니다.
  `LIBDIR=$(../../.venv/bin/krpatch sfc lua)` 로 실행하세요. `test/` 에 있는 이
  게임용 스크립트(`probe.lua`, `banner_ids.lua`, `warp_seq.lua`)도 같은
  `LIBDIR` 을 씁니다.
- `compat/run_all.sh` 는 `compat/cores/` 에 libretro 코어, `compat/roms/` 에 롬과
  `save_cookie.srm` 이 있어야 합니다(docs/ANALYSIS.ko.md 8장).

예전에 이 폴더에 있었고 이제 [kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit)
에서 가져오는 도구:

| 예전 파일 | 대신 쓸 것 |
| --- | --- |
| `tools/py/make_ips.py` | `krpatch ips make --gap 7 ... --headered ...` |
| `tools/py/dis65816.py` | `krpatch sfc dis ROM ADDR COUNT`(블록 이동은 `MVN src,dst` 로 출력) |
| `tools/py/tiles.py`, `glyphs.py`, `vramchr.py` | `krpatch sfc tiles`(`--rows`, `--stride`, `--tall`) |
| `tools/py/bgrender.py`, `vramrefs.py` | `krpatch sfc bg`, `krpatch sfc bgrefs` |
| `tools/py/shotcmp.py`, `contact.py`, `diffr.py` | `krpatch shotcmp`, `krpatch contact`, `krpatch diff` |
| `compat/lr.py`, `compat/mesen_run.lua` | `krpatch sfc run ... --watch 7E0052:3`, `script.lua` 에 `WATCH_WRAM=7E0052:3` |
| `test/lib.lua`, `seq.lua`, `poke_state.lua`, `compat/dumpsrm.lua` | `krpatch sfc lua` 의 같은 스크립트 |

docs/ANALYSIS.ko.md 는 무언가를 어떻게 찾았는지 설명하는 대목에서 예전 파일
이름을 그대로 씁니다.

## 라이선스

코드(asm, Python, 셸, Lua): MIT, 최상위 `LICENSE` 참고. 한글 텍스트, 이름 표,
그래픽은 비상업으로 배포하는 팬 번역 데이터이며 MIT 라이선스 대상이 아닙니다.
Galmuri 는 SIL Open Font License 1.1 을 따릅니다.
