# 제절초(SFC) 한글패치 v1.2

[English](README.md) | 한국어

일본판 슈퍼 패미콤 *제절초* 한글패치의 소스입니다. v1.1 은 한글판
v1.0 패치 위에 대본과 폰트를 다시 만들고, v1.2 는 v1.1 롬에 장 선택과 엔딩
목록을 더합니다.

패치 페이지: <https://perfectacle.github.io/games/kr-patches/sfc/otogirisou/>

롬 배치, 메모리, 대본·폰트 형식, 훅, 세이브 형식, 빈 공간은
[docs/ANALYSIS.ko.md](docs/ANALYSIS.ko.md) 에 정리했습니다.

## 원본 롬

롬은 들어 있지 않습니다. 직접 덤프한 일본판 카트리지 롬을 이 폴더에
`Otogirisou (Japan).sfc` 라는 이름으로 두세요.

| | |
| --- | --- |
| 헤더 제목 | `OTOGIRISOU`(LoROM, 1,048,576바이트, 카피어 헤더 없음) |
| CRC32 | `8E4BEFD0` |
| SHA-1 | `2c27b89a244abe941b6a9fceb1a674dbefd1f734` |

`Otogirisou(K).ips` 가 v1.0 패치이며, 빌드가 가장 먼저 적용합니다.

## 빌드

준비물: 저장소의 Python 환경(최상위 README 참고), `tools/asar` 에 둔
[asar](https://github.com/RPGHacker/asar) 1.91, zsh.

| 명령 | 결과물 |
| --- | --- |
| `zsh tools/build.sh` | `build/otogirisou-kr-v1.1.sfc` |
| `zsh tools/release.sh` | v1.1 빌드와 `release/v1.1/*.ips`(헤더 없는 롬용과 512바이트 헤더용) |
| `zsh tools/build-v1.2.sh` | v1.1 빌드 위에 `build/otogirisou-kr-v1.2.sfc` |
| `zsh tools/release-v1.2.sh` | `release/v1.2/*.ips`(헤더 없는 롬용과 512바이트 헤더용), CRC32 `2C31A0B2` |

배포한 v1.2 패치를 그대로 다시 만들려면:

```sh
zsh tools/build.sh && zsh tools/release-v1.2.sh
```

첫 빌드는 가진 롬에서 일본어 대본을 `tables/script-jp.txt`(`tables/script.txt`
와 줄 번호가 같음)로 뽑습니다. 이 파일은 저장소에 없습니다. 빌드할 때마다
`build/waits.tsv`(일본어 대본과 다른 키 입력 대기)와 `build/overflow.tsv`
(9줄을 넘는 페이지)도 씁니다. 긴 페이지는 `tools/splitpages.py` 로 나눕니다.

다른 환경을 쓰려면 `PYTHON` 과 `KRPATCH` 를 지정하세요.

## 고치기

- 대본: `tables/script.txt` 를 고치고 다시 빌드합니다.
- 새 글자: v1.0 폰트에 없는 글자는 경고가 나옵니다. `tables/newglyphs.json` 에
  그려 넣으세요. `tools/glyph_workbench.py` 는 v1.0 글리프를 보여 주고 다른
  글리프의 부분을 모아 새 글리프를 만듭니다(`build/v1.0.sfc` 필요).
- v1.2 추가 기능: 장은 `tables/qol-chapters.tsv`, 엔딩은
  `tables/qol-endings.tsv` 에 있습니다. 데이터는 `tools/qol.py`(뱅크 $1B)와
  `tools/flow.py`(뱅크 $1C), 코드는 `asm/qol.asm` 과 `asm/flow.asm` 에 있습니다.

## 테스트(Mesen 2, 선택)

범용 스크립트(`lib.lua`, `boot.lua`, 프로브)는 툴킷에서 가져옵니다. 그
디렉터리를 `LIBDIR` 로 넘기세요.

```sh
LIBDIR=$(../../.venv/bin/krpatch sfc lua) LAP=1 STABLE=18 PERIOD=40 SHOT_DIR=out Mesen --testrunner rom.sfc lua/pages.lua
MESEN=/path/to/Mesen zsh lua/qol/menujump.sh rom.sfc template.srm outdir
```

`lua/` 와 `lua/qol/` 에는 이 게임을 아는 스크립트(`pages.lua`, `lap.lua`,
`name.lua`, `waitdemo.lua`, `qol/jumpto.lua`, `qol/dump.lua`, `qol/pcs.lua`,
`qol/pagescont.lua`)가 남아 있습니다. `compat/run_all.sh` 는 `compat/` 의
시나리오를 `krpatch sfc run` 으로 libretro 코어에서 재생합니다.

예전에 이 폴더에 있었고 이제 [kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit)
에서 가져오는 파일:

| 예전 파일 | 대신 쓸 것 |
| --- | --- |
| `tools/ips.py` | `krpatch ips make`, `krpatch ips apply` |
| `tools/fixsum.py` | `krpatch sfc checksum --fix --mapper lorom` |
| `tools/dis65816.py` | `krpatch sfc dis ROM ADDR COUNT --mapper lorom`(블록 이동은 `MVN src,dst` 로 출력) |
| `tools/ocr/glyph_ocr.py`, `fix_mo.py`, `ocr.swift` | `tools/fontjson.py` 다음에 `krpatch ocr ... --fix-mo` |
| `lua/lib.lua`, `lua/boot.lua` | `krpatch sfc lua` 의 같은 스크립트 |
| `lua/qol/cgram`, `peek`, `swatch`, `watch`, `wdump`, `wrange`, `wtrace` | `krpatch sfc lua` 의 `probe/<이름>.lua` |
| `lua/qol/ppu.lua` | `probe/ppu.lua` 에 `SHADOW=0A00-0A24` |
| `lua/qol/trace.lua` | `probe/trace.lua` 에 `LOG=00CC,1A95`(레지스터는 A/X/Y/D/DB 로 기록) |
| `compat/lr.py` | `krpatch sfc run ... --watch 7E0052:3` |

docs/ANALYSIS.ko.md 는 무언가를 어떻게 찾았는지 설명하는 대목에서 예전 파일
이름을 그대로 씁니다.

## 라이선스

코드(asm, Python, 셸, Lua): MIT, 최상위 `LICENSE` 참고. 한글 대본, 코드표,
글리프는 비상업으로 배포하는 팬 번역 데이터이며 MIT 라이선스 대상이 아닙니다.
Galmuri(`tools/fonts/`)는 SIL Open Font License 1.1 을 따릅니다.
