# Dragon Ball Z: Super Gokuden – Totsugeki-hen (SFC) Korean patch v1.2

Source of the Korean translation patch v1.2 for the Japanese *Dragon Ball Z:
Super Gokuden – Totsugeki-hen* (Super Famicom). The build starts from the
Japanese ROM with the Korean v1.0 patch applied, then replaces the title
screen, rewrites the dialogue and menus, redraws look-alike password glyphs
and shows a fixed ending password.

Patch page: <https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-totsugeki/>

ROM header, memory, text and font formats, hooks, free space used and the
debug menu are documented in [docs/ANALYSIS.md](docs/ANALYSIS.md) (Korean).

## Base ROM

No ROM is included. Put your own dump of the Japanese cartridge in this folder
as `super-gokuden-jp.smc`:

| | |
| --- | --- |
| Header title | `SFX DBZ TOTSUGEKIHEN` (LoROM, 2,097,152 bytes, no copier header) |
| CRC32 | `D531289B` |
| SHA-1 | `926b861734cdeef9e70cd436be62c73481e7392f` |

`v1.0/v1.0.ips` is the v1.0 patch; the build applies it first.

## Build

Requirements: the repository's Python environment (see the top-level README),
zsh, macOS. `tools/title.py` draws 「초오공전」 with the BM YeongSung font from
the macOS system font assets (`TITLE_FONT`); on other systems add
`--font PATH` to the `title.py` line of `tools/build.sh`.

```sh
zsh tools/build.sh
```

Output: `super-gokuden-kr-v1.2.smc` (CRC32 `81DAD733`) and
`release/v1.2/*.ips` (plain and 512-byte copier header), identical to the
released patches. `tables/kr-v1.2.txt` (the v1.2 code table) is written by the
build. Set `PYTHON` and `KRPATCH` to use another environment.

Steps: `krpatch ips apply` (v1.0) → `tools/title.py` → `tools/text_patch1.py`
(dialogue, other text sets, menu fixes) → `tools/pwglyph1.py` (password glyphs,
checked against the table) → `tools/endpw1.py` (ending password) →
`krpatch sfc checksum --fix` → `krpatch ips make --headered`.

## Layout

| Path | Contents |
| --- | --- |
| `tools/` | build and analysis scripts (usage in each file's first lines) |
| `tables/v1.1/` | v1.1 text (id, window info, text) |
| `tables/ui-fixes.tsv` | menu strings outside the pointer tables |
| `tables/*-v1.0.tsv` | Japanese text next to the v1.0 translation |
| `tables/jp-verified.txt`, `kr-v1.0.txt` | Japanese / v1.0 code tables |
| `tables/kr-v1.2-glyphs.txt` | names of the five glyphs v1.2 redraws (over `kr-v1.0.txt`) |
| `tables/password.tsv` | the 163 ending-password characters (code, kana, v1.1 and v1.2 screens) |
| `v1.0/` | the v1.0 patch the build starts from |
| `lua/` | Mesen 2 scripts for this game |
| `compat/` | the same input on several libretro cores (`compat/run_all.sh`) |
| `tools/fonts/` | Galmuri fonts (SIL Open Font License 1.1, `LICENSE.txt`) |

## Tests

Without an emulator:

```sh
../../.venv/bin/python tools/layout1.py tables/v1.1/dialogue.tsv   # pixel width per window, 3-line pages
../../.venv/bin/python tools/textdump1.py super-gokuden-kr-v1.2.smc out.tsv
```

`tools/pages1.py` also needs numpy.

Mesen 2 (debug menu: change file offset 0x61 from `80 04` to `EA EA`). The game
scripts load the toolkit's `lib.lua` from `LIBDIR`:

```sh
export LIBDIR=$(../../.venv/bin/krpatch sfc lua)
TARGET=10 SHOTS=1 SHOT_DIR=out Mesen --testrunner debug.smc lua/scenario.lua
TARGET=c0 SHOT_DIR=out Mesen --testrunner debug.smc lua/eventlist.lua
NAME=12C,142,14C,14D,1C8 ST=ending.mss SHOT_DIR=out Mesen --testrunner debug.smc lua/ending.lua
```

`python3 tools/pages1.py out 0142` lists the frames of each finished page of
dialogue 0142; `python3 tools/rgcmp1.py runs_jp runs_kr` compares two batches.

Files that used to ship in this folder and now come from
[kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit):

| Old file | Use instead |
| --- | --- |
| `tools/ips.py` | `krpatch ips make`, `krpatch ips apply` |
| `tools/fixsum.py` | `krpatch sfc checksum --fix --mapper lorom` |
| `tools/lz.py` | `kr_patch.lzss`, `kr_patch.sfc.tiles.planar_to_sfc`/`sfc_to_planar`, `krpatch lzss` |
| `tools/dis65816.py` | `krpatch sfc dis ROM ADDR COUNT --mapper lorom` (block moves print as `MVN src,dst`) |
| `lua/lib.lua` | `lib.lua` in `krpatch sfc lua` |
| `compat/lr.py` | `krpatch sfc run ... --watch 7E004D:2` |
| `compat/mesen.lua` | `script.lua` in `krpatch sfc lua` with `WATCH_WRAM=7E004D:2` |

docs/ANALYSIS.md still names the old files where it describes how something
was found.

## License

Code (Python, shell, Lua): MIT, see the top-level `LICENSE`. The Korean text,
code tables and graphics are fan translation data, distributed
non-commercially and not covered by the MIT license. Galmuri is under the SIL
Open Font License 1.1.

## 한국어 요약

드래곤볼 Z 초오공전 돌격편(일본판) 한글패치 v1.2의 소스입니다. 일본판에 v1.0 패치를 적용한 롬에서 시작해 타이틀, 대사·메뉴, 암호 글자, 엔딩 암호를 고칩니다.

- 준비물: 일본판 롬(헤더 제목 `SFX DBZ TOTSUGEKIHEN`, CRC32 `D531289B`)을 이 폴더에 `super-gokuden-jp.smc` 로 둡니다. 타이틀 글꼴 BM영성체는 macOS 시스템 글꼴에서 읽습니다.
- `zsh tools/build.sh` 를 실행하면 `super-gokuden-kr-v1.2.smc`(CRC32 `81DAD733`)와 배포한 것과 같은 IPS 두 개가 `release/v1.2/` 에 나옵니다.
- Lua 스크립트는 `LIBDIR=$(krpatch sfc lua)` 로 툴킷의 `lib.lua` 를 씁니다.
- 롬 분석 노트는 [docs/ANALYSIS.md](docs/ANALYSIS.md) 에 있습니다.
- 코드는 MIT, 한글 대사·코드표·그래픽은 비상업 배포하는 번역 데이터로 MIT와 별개입니다.
