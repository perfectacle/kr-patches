# 드래곤볼 Z 초오공전: 각성편(SFC) 한글패치 v1.4

[English](README.md) | 한국어

일본판 슈퍼 패미콤 *드래곤볼 Z 초오공전 각성편* 한글패치 v1.4 의 소스입니다.
일본판 롬에 한글패치 v1.1 을 적용한 롬에서 시작해, v1.1 이 살아 있는 데이터를
덮어쓴 텍스트를 되돌린 뒤 타이틀 화면, 대사, 전투 말풍선, 엔딩 크레딧을 바꾸고,
한글판 돌격편의 암호를 암호 입력 화면에서 읽을 수 있게 합니다(v1.3).
v1.4 는 이름 입력을 자모 조합으로 바꾸고 타이틀 메뉴를 가운데에 맞추며, 이름에 한글 11,172자를 모두 쓸 수
있게 대사 폰트에 없는 글자를 새로 넣습니다. 롬은 4MB 로 늘어납니다.

패치 페이지: <https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-kakusei/>

롬 지도, 텍스트·폰트 형식, v1.1 진행 불가 버그, 타이틀, 크레딧, 디버그 메뉴,
세이브 RAM, Mesen 2 사용법, 돌격편 암호, v1.4 이름 입력은
[docs/ANALYSIS.ko.md](docs/ANALYSIS.ko.md)(배포한 도구 zip 의 README.txt 였던
문서)에 정리했습니다.

## 원본 롬

롬은 들어 있지 않습니다. 직접 덤프한 일본판 카트리지 롬을 이 폴더에
`super-gokuden-jp.smc` 로 두세요.

| | |
| --- | --- |
| 헤더 제목 | `ｽｰﾊﾟｰｺﾞｸｳﾃﾞﾝ ｶｸｾｲﾍﾝ`(반각 가타카나, LoROM, 2,097,152바이트, 카피어 헤더 없음) |
| CRC32 | `3172CD4F` |
| SHA-1 | `3b7278a54f8d470dcb1bd92060d744380325f30b` |

`v1.1/v1.1.ips` 가 v1.1 패치이며, 빌드가 가장 먼저 적용합니다.

## 빌드

준비물: 저장소의 Python 환경(최상위 README 참고), zsh, macOS, v1.4 는
`tools/asar` 에 둔 [asar](https://github.com/RPGHacker/asar) 1.91.
`tools/title.py` 는 macOS 시스템 글꼴 애셋의 BM영성체로 타이틀을 그립니다.
다른 시스템에서는 `tools/title.py` 의 `TITLE_FONT` 를 바꾸세요.

```sh
zsh tools/build-v1.4.sh
```

결과물: `super-gokuden-kr-v1.4.smc`(CRC32 `8AA3123E`)와 `release/v1.4/*.ips`
(헤더 없는 롬용과 512바이트 카피어 헤더용). 배포한 패치와 같습니다. v1.4
빌드는 먼저 `tools/build.sh` 를 돌리고, 이것이 `super-gokuden-kr-v1.3.smc`
(CRC32 `B9F14962`)와 `release/v1.3/*.ips` 를 씁니다. 빌드는
`tables/kr-v1.3.txt`(새 글리프를 포함한 v1.3 코드표)도 다시 쓰며, 깨끗한
빌드에서는 내용이 바뀌지 않습니다. 다른 환경을 쓰려면 `PYTHON` 과 `KRPATCH`
를 지정하세요.

단계: `krpatch ips apply`(v1.1) → `fix_overwrites.py` → `title.py` →
`dialogue_patch.py` → `bubble_patch.py` → `password.py` → `credits.py` →
`check_width.py`(줄이 창보다 넓으면 빌드 실패) →
`krpatch sfc checksum --fix` → `krpatch ips make --headered` 까지가 v1.3 이고,
이어서 `tools/font16.py`(새 16px 글자, 4MB 롬, 자모 글자판, 표
`work/font16_*.asm`) → asar `asm/v14.asm`(렌더러·이름 입력 훅) →
`krpatch sfc checksum --fix` → `krpatch ips make --headered --rle`.

## 구성

| 경로 | 내용 |
| --- | --- |
| `tools/` | 빌드·분석 스크립트(사용법은 각 파일 첫 줄들에) |
| `asm/v14.asm` | v1.4 렌더러·이름 입력 코드(asar) |
| `tables/dialogue-v1.3.tsv`, `bubbles-v1.3.tsv` | 고친 대사와 전투 말풍선(`/` = 줄바꿈) |
| `tables/jp.txt`, `kr.txt`, `kr-v1.3.txt` | 일본어, v1.1, v1.3 코드표 |
| `tables/totsugeki-password.tsv` | 돌격편 암호 글리프와 짝 표 |
| `v1.1/` | 빌드의 출발점인 v1.1 패치 |
| `lua/` | 이 게임용 Mesen 2 스크립트(`dbgscene.lua`, `crjump.lua`) |
| `compat/` | Mesen 2 와 libretro 코어에 같은 입력 재생(`compat/run_all.sh`, `SCENARIOS="new14 cont"` 처럼 골라 돌림) |
| `tools/fonts/` | Galmuri 글꼴(SIL Open Font License 1.1, `LICENSE.txt`) |

## 테스트

`tools/check_width.py` 는 빌드 안에서 돕니다. Mesen 2 스크립트(디버그 메뉴가
필요합니다. docs/ANALYSIS.ko.md 9장 참고)는 `LIBDIR` 에서 툴킷의 `lib.lua` 를
불러옵니다.

```sh
LIBDIR=$(../../.venv/bin/krpatch sfc lua) TARGET=50 SHOT_DIR=out Mesen --testrunner debug.smc lua/dbgscene.lua
```

`compat/run_all.sh` 는 `compat/s_*.txt` 를 Mesen 2(툴킷의 `script.lua`)와
libretro 코어(`krpatch sfc run`)에서 재생하며 장면 워드 `$7E029C` 를
기록합니다.

예전에 이 폴더에 있었고 이제 [kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit)
에서 가져오는 파일:

| 예전 파일 | 대신 쓸 것 |
| --- | --- |
| `tools/ips.py` | `krpatch ips make`, `krpatch ips apply` |
| `tools/fixsum.py` | `krpatch sfc checksum --fix --mapper lorom` |
| `tools/lz.py` | `kr_patch.lzss`, `kr_patch.sfc.tiles.planar_to_sfc`/`sfc_to_planar`, `krpatch lzss` |
| `lua/lib.lua` | `krpatch sfc lua` 의 `lib.lua` |
| `lua/compat.lua` | `krpatch sfc lua` 의 `script.lua` 에 `WATCH_WRAM=7E029C:2 WATCH_FMT=%03x`(`LUA_DIR` 은 이제 `LIBDIR`) |
| `compat/lr.py` | `krpatch sfc run ... --watch 7E029C:2 --watch-fmt 03x` |

docs/ANALYSIS.ko.md 는 무언가를 어떻게 찾았는지 설명하는 대목에서 예전 파일
이름을 그대로 씁니다.

## 라이선스

코드(Python, 셸, Lua, 어셈블리): MIT, 최상위 `LICENSE` 참고. 한글 텍스트, 코드표,
그래픽은 비상업으로 배포하는 팬 번역 데이터이며 MIT 라이선스 대상이 아닙니다.
Galmuri 는 SIL Open Font License 1.1 을 따릅니다.
