# Dragon Ball Z: Super Gokuden – Totsugeki-hen (SFC) Korean patch v1.3

English | [한국어](README.ko.md)

Source of the Korean translation patch v1.3 for the Japanese *Dragon Ball Z:
Super Gokuden – Totsugeki-hen* (Super Famicom). The build starts from the
Japanese ROM with the Korean v1.0 patch applied, then replaces the title
screen, rewrites the dialogue and menus, redraws look-alike password glyphs
and shows a fixed ending password (v1.2). v1.3 redraws the 8px Hangul of
names, adds all 11,172 syllables and turns the name entry into a jamo
keyboard; the ROM grows to 4 MB.

Patch page: <https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-totsugeki/>

ROM header, memory, text and font formats, hooks, free space used and the
debug menu are documented in [docs/ANALYSIS.md](docs/ANALYSIS.md).

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
zsh, macOS, and for v1.3 [asar](https://github.com/RPGHacker/asar) 1.91 at
`tools/asar`. `tools/title.py` draws 「초오공전」 with the BM YeongSung font from
the macOS system font assets (`TITLE_FONT`); on other systems add
`--font PATH` to the `title.py` line of `tools/build.sh`.

```sh
zsh tools/build-v1.3.sh
```

Output: `super-gokuden-kr-v1.3.smc` (CRC32 `FC7FB902`) and
`release/v1.3/*.ips` (plain and 512-byte copier header), identical to the
released patches. The v1.3 build runs `tools/build.sh` first, which writes
`super-gokuden-kr-v1.2.smc` (CRC32 `A939C4F8`) and `release/v1.2/*.ips`. `tables/kr-v1.2.txt` (the v1.2 code table) is written by the
build. Set `PYTHON` and `KRPATCH` to use another environment.

Steps: `krpatch ips apply` (v1.0) → `tools/title.py` → `tools/text_patch1.py`
(dialogue, other text sets, menu fixes) → `tools/statusmenu1.py` (learned and
cleared marks in the status screen lists) → `tools/pwglyph1.py` (password
glyphs, checked against the table) → `tools/endpw1.py` (ending password) →
`krpatch sfc checksum --fix` → `krpatch ips make --headered` gives v1.2;
then `tools/font8.py` (redrawn and new 8px glyphs, 4 MB ROM, jamo board and
the tables `work/font8_*.asm`) → asar `asm/v13.asm` (renderer and name entry
hooks) → `krpatch sfc checksum --fix` → `krpatch ips make --headered --rle`.

## Layout

| Path | Contents |
| --- | --- |
| `tools/` | build and analysis scripts (usage in each file's first lines) |
| `asm/v13.asm` | v1.3 renderer and name entry code (asar) |
| `tables/v1.1/` | v1.1 text (id, window info, text) |
| `tables/ui-fixes.tsv` | menu strings outside the pointer tables (status screen, results screen, ending credits included) |
| `tables/*-v1.0.tsv` | Japanese text next to the v1.0 translation |
| `tables/jp-verified.txt`, `kr-v1.0.txt` | Japanese / v1.0 code tables |
| `tables/kr-v1.2-glyphs.txt` | names of the five 8px password glyphs v1.2 redraws (over `kr-v1.0.txt`) |
| `tables/password.tsv` | the 163 ending-password characters (code, kana, v1.1 and v1.2 screens) |
| `v1.0/` | the v1.0 patch the build starts from |
| `lua/` | Mesen 2 scripts for this game |
| `compat/` | the same input on several libretro cores (`compat/run_all.sh`; `SCENARIOS="new13 cont"` for v1.3) |
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

Code (Python, shell, Lua, assembly): MIT, see the top-level `LICENSE`. The Korean text,
code tables and graphics are fan translation data, distributed
non-commercially and not covered by the MIT license. Galmuri is under the SIL
Open Font License 1.1.
