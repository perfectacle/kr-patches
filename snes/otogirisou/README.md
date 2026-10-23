# Otogirisou (SFC) Korean patch v1.2

Source of the Korean translation patch for the Japanese *Otogirisou*
(Super Famicom). v1.1 rebuilds the script and font on top of the Korean v1.0
patch; v1.2 adds a chapter select and an ending list to the v1.1 ROM.

Patch page: <https://perfectacle.github.io/games/kr-patches/sfc/otogirisou/>

ROM layout, memory, script and font formats, hooks, save format and free space
are documented in [docs/ANALYSIS.md](docs/ANALYSIS.md) (Korean).

## Base ROM

No ROM is included. Use your own dump of the Japanese cartridge, named
`Otogirisou (Japan).sfc` in this folder:

| | |
| --- | --- |
| Header title | `OTOGIRISOU` (LoROM, 1,048,576 bytes, no copier header) |
| CRC32 | `8E4BEFD0` |
| SHA-1 | `2c27b89a244abe941b6a9fceb1a674dbefd1f734` |

`Otogirisou(K).ips` is the v1.0 patch; the build applies it first.

## Build

Requirements: the repository's Python environment (see the top-level README),
[asar](https://github.com/RPGHacker/asar) 1.91 at `tools/asar`, zsh.

| Command | Output |
| --- | --- |
| `zsh tools/build.sh` | `build/otogirisou-kr-v1.1.sfc` |
| `zsh tools/release.sh` | v1.1 build plus `release/v1.1/*.ips` (plain and 512-byte header) |
| `zsh tools/build-v1.2.sh` | `build/otogirisou-kr-v1.2.sfc`, on top of the v1.1 build |
| `zsh tools/release-v1.2.sh` | `release/v1.2/*.ips` (plain and 512-byte header), CRC32 `2C31A0B2` |

To reproduce the released v1.2 patch:

```sh
zsh tools/build.sh && zsh tools/release-v1.2.sh
```

The first build dumps the Japanese script from your ROM to
`tables/script-jp.txt` (same line numbers as `tables/script.txt`). It is not
part of the repository. Each build also writes `build/waits.tsv` (key waits
that differ from the Japanese script) and `build/overflow.tsv` (pages over nine
lines); `tools/splitpages.py` splits long pages.

Set `PYTHON` and `KRPATCH` to use another environment.

## Editing

- Script: edit `tables/script.txt` and rebuild.
- New characters: characters missing from the v1.0 font produce a warning; draw
  them in `tables/newglyphs.json`. `tools/glyph_workbench.py` shows v1.0 glyphs
  and builds new ones from parts of others (needs `build/v1.0.sfc`).
- v1.2 extras: chapters in `tables/qol-chapters.tsv`, endings in
  `tables/qol-endings.tsv`; data from `tools/qol.py` (bank $1B) and
  `tools/flow.py` (bank $1C), code in `asm/qol.asm` and `asm/flow.asm`.

## Tests (Mesen 2, optional)

The generic scripts (`lib.lua`, `boot.lua` and the probes) come from the
toolkit; pass their directory as `LIBDIR`:

```sh
LIBDIR=$(../../.venv/bin/krpatch snes lua) LAP=1 STABLE=18 PERIOD=40 SHOT_DIR=out Mesen --testrunner rom.sfc lua/pages.lua
MESEN=/path/to/Mesen zsh lua/qol/menujump.sh rom.sfc template.srm outdir
```

`lua/` and `lua/qol/` keep the scripts that know this game (`pages.lua`,
`lap.lua`, `name.lua`, `waitdemo.lua`, `qol/jumpto.lua`, `qol/dump.lua`,
`qol/pcs.lua`, `qol/pagescont.lua`). `compat/run_all.sh` plays the scenarios in
`compat/` on libretro cores through `krpatch snes run`.

Files that used to ship in this folder and now come from
[kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit):

| Old file | Use instead |
| --- | --- |
| `tools/ips.py` | `krpatch ips make`, `krpatch ips apply` |
| `tools/fixsum.py` | `krpatch snes checksum --fix --mapper lorom` |
| `tools/dis65816.py` | `krpatch snes dis ROM ADDR COUNT --mapper lorom` (block moves print as `MVN src,dst`) |
| `tools/ocr/glyph_ocr.py`, `fix_mo.py`, `ocr.swift` | `tools/fontjson.py` then `krpatch ocr ... --fix-mo` |
| `lua/lib.lua`, `lua/boot.lua` | the same scripts in `krpatch snes lua` |
| `lua/qol/cgram`, `peek`, `swatch`, `watch`, `wdump`, `wrange`, `wtrace` | `probe/<name>.lua` in `krpatch snes lua` |
| `lua/qol/ppu.lua` | `probe/ppu.lua` with `SHADOW=0A00-0A24` |
| `lua/qol/trace.lua` | `probe/trace.lua` with `LOG=00CC,1A95` (registers are logged as A/X/Y/D/DB) |
| `compat/lr.py` | `krpatch snes run ... --watch 7E0052:3` |

docs/ANALYSIS.md still names the old files where it describes how something
was found.

## License

Code (asm, Python, shell, Lua): MIT, see the top-level `LICENSE`. The Korean
script, code tables and glyphs are fan translation data, distributed
non-commercially and not covered by the MIT license. Galmuri
(`tools/fonts/`) is under the SIL Open Font License 1.1.

## 한국어 요약

제절초(오토기리소우, 일본판) 한글패치 소스입니다. v1.1은 v1.0 한글판 위에 대본과 폰트를 다시 만들고, v1.2는 그 위에 장 선택과 엔딩 목록을 더합니다.

- 준비물: 일본판 롬(헤더 제목 `OTOGIRISOU`, CRC32 `8E4BEFD0`)을 이 폴더에 `Otogirisou (Japan).sfc` 로, asar 1.91을 `tools/asar` 로 둡니다.
- `zsh tools/build.sh && zsh tools/release-v1.2.sh` 를 실행하면 `release/v1.2/` 에 배포한 것과 같은 IPS가 나옵니다(롬 CRC32 `2C31A0B2`).
- 일본어 대본(`tables/script-jp.txt`)은 저장소에 없고, 첫 빌드 때 가진 롬에서 뽑습니다.
- 롬 분석 노트는 [docs/ANALYSIS.md](docs/ANALYSIS.md) 에 있습니다.
- 코드는 MIT, 한글 대본·코드표·글리프는 비상업 배포하는 번역 데이터로 MIT와 별개입니다.
