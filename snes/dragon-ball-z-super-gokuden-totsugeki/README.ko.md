# 드래곤볼 Z 초오공전: 돌격편(SFC) 한글패치 v1.2

[English](README.md) | 한국어

일본판 슈퍼패미컴 *드래곤볼 Z 초오공전 돌격편* 한글패치 v1.2 의 소스입니다.
일본판 롬에 한글패치 v1.0 을 적용한 롬에서 시작해, 타이틀 화면을 바꾸고 대사와
메뉴를 다시 쓰고, 서로 헷갈리는 암호 글자를 다시 그리고, 엔딩에 고정 암호를
보여 줍니다.

패치 페이지: <https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-totsugeki/>

롬 헤더, 메모리, 텍스트·폰트 형식, 훅, 사용한 빈 공간, 디버그 메뉴는
[docs/ANALYSIS.ko.md](docs/ANALYSIS.ko.md) 에 정리했습니다.

## 원본 롬

롬은 들어 있지 않습니다. 직접 덤프한 일본판 카트리지 롬을 이 폴더에
`super-gokuden-jp.smc` 로 두세요.

| | |
| --- | --- |
| 헤더 제목 | `SFX DBZ TOTSUGEKIHEN`(LoROM, 2,097,152바이트, 카피어 헤더 없음) |
| CRC32 | `D531289B` |
| SHA-1 | `926b861734cdeef9e70cd436be62c73481e7392f` |

`v1.0/v1.0.ips` 가 v1.0 패치이며, 빌드가 가장 먼저 적용합니다.

## 빌드

준비물: 저장소의 Python 환경(최상위 README 참고), zsh, macOS.
`tools/title.py` 는 macOS 시스템 글꼴 애셋의 BM영성체(`TITLE_FONT`)로
「초오공전」을 그립니다. 다른 시스템에서는 `tools/build.sh` 의 `title.py` 줄에
`--font PATH` 를 더하세요.

```sh
zsh tools/build.sh
```

결과물: `super-gokuden-kr-v1.2.smc`(CRC32 `A939C4F8`)와 `release/v1.2/*.ips`
(헤더 없는 롬용과 512바이트 카피어 헤더용). 배포한 패치와 같습니다.
`tables/kr-v1.2.txt`(v1.2 코드표)는 빌드가 씁니다. 다른 환경을 쓰려면
`PYTHON` 과 `KRPATCH` 를 지정하세요.

단계: `krpatch ips apply`(v1.0) → `tools/title.py` → `tools/text_patch1.py`
(대사, 그 밖의 텍스트 묶음, 메뉴 수정) → `tools/statusmenu1.py`(상태 화면
목록의 습득·완료 표시) → `tools/pwglyph1.py`(암호 글리프, 표와 대조) →
`tools/endpw1.py`(엔딩 암호) → `krpatch snes checksum --fix` →
`krpatch ips make --headered`.

## 구성

| 경로 | 내용 |
| --- | --- |
| `tools/` | 빌드·분석 스크립트(사용법은 각 파일 첫 줄들에) |
| `tables/v1.1/` | v1.1 텍스트(id, 창 정보, 텍스트) |
| `tables/ui-fixes.tsv` | 포인터 테이블 밖의 메뉴 문자열(상태 화면, 성적표, 엔딩 크레딧 포함) |
| `tables/*-v1.0.tsv` | 일본어 텍스트와 v1.0 번역을 나란히 |
| `tables/jp-verified.txt`, `kr-v1.0.txt` | 일본어 / v1.0 코드표 |
| `tables/kr-v1.2-glyphs.txt` | v1.2 가 (`kr-v1.0.txt` 위에) 다시 그린 8px 암호 글리프 다섯 개의 이름 |
| `tables/password.tsv` | 엔딩 암호 글자 163개(코드, 가나, v1.1·v1.2 화면) |
| `v1.0/` | 빌드의 출발점인 v1.0 패치 |
| `lua/` | 이 게임용 Mesen 2 스크립트 |
| `compat/` | 여러 libretro 코어에 같은 입력 재생(`compat/run_all.sh`) |
| `tools/fonts/` | Galmuri 글꼴(SIL Open Font License 1.1, `LICENSE.txt`) |

## 테스트

에뮬레이터 없이:

```sh
../../.venv/bin/python tools/layout1.py tables/v1.1/dialogue.tsv   # 창별 픽셀 폭, 3줄 페이지
../../.venv/bin/python tools/textdump1.py super-gokuden-kr-v1.2.smc out.tsv
```

`tools/pages1.py` 는 numpy 도 필요합니다.

Mesen 2(디버그 메뉴: 파일 오프셋 0x61 을 `80 04` 에서 `EA EA` 로 바꿉니다).
게임 스크립트는 `LIBDIR` 에서 툴킷의 `lib.lua` 를 불러옵니다.

```sh
export LIBDIR=$(../../.venv/bin/krpatch snes lua)
TARGET=10 SHOTS=1 SHOT_DIR=out Mesen --testrunner debug.smc lua/scenario.lua
TARGET=c0 SHOT_DIR=out Mesen --testrunner debug.smc lua/eventlist.lua
NAME=12C,142,14C,14D,1C8 ST=ending.mss SHOT_DIR=out Mesen --testrunner debug.smc lua/ending.lua
```

`python3 tools/pages1.py out 0142` 는 대사 0142 의 페이지마다 완성된 프레임을
나열하고, `python3 tools/rgcmp1.py runs_jp runs_kr` 는 두 묶음을 비교합니다.

예전에 이 폴더에 있었고 이제 [kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit)
에서 가져오는 파일:

| 예전 파일 | 대신 쓸 것 |
| --- | --- |
| `tools/ips.py` | `krpatch ips make`, `krpatch ips apply` |
| `tools/fixsum.py` | `krpatch snes checksum --fix --mapper lorom` |
| `tools/lz.py` | `kr_patch.lzss`, `kr_patch.snes.tiles.planar_to_snes`/`snes_to_planar`, `krpatch lzss` |
| `tools/dis65816.py` | `krpatch snes dis ROM ADDR COUNT --mapper lorom`(블록 이동은 `MVN src,dst` 로 출력) |
| `lua/lib.lua` | `krpatch snes lua` 의 `lib.lua` |
| `compat/lr.py` | `krpatch snes run ... --watch 7E004D:2` |
| `compat/mesen.lua` | `krpatch snes lua` 의 `script.lua` 에 `WATCH_WRAM=7E004D:2` |

docs/ANALYSIS.ko.md 는 무언가를 어떻게 찾았는지 설명하는 대목에서 예전 파일
이름을 그대로 씁니다.

## 라이선스

코드(Python, 셸, Lua): MIT, 최상위 `LICENSE` 참고. 한글 텍스트, 코드표,
그래픽은 비상업으로 배포하는 팬 번역 데이터이며 MIT 라이선스 대상이 아닙니다.
Galmuri 는 SIL Open Font License 1.1 을 따릅니다.
