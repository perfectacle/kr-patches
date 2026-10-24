# Ghost Trick (NDS) Korean patch v1.2

English | [한국어](README.ko.md)

Source of the Korean translation patch v1.2 for the Japanese *Ghost Trick*
(Nintendo DS). The build starts from the Japanese ROM with the Korean v1.1
patch applied and rebuilds the dialogue scripts from the Japanese scripts.
Fonts and graphics stay as in v1.1.

Patch page: <https://perfectacle.github.io/games/kr-patches/nds/ghost-trick/>

ROM layout, script and font formats, the problems found in v1.1 and the
measured dialogue window widths are documented in
[docs/ANALYSIS.md](docs/ANALYSIS.md).

## Base ROM

No ROM is included. Put your own dump of the Japanese game card in this folder
as `ghost-trick-jp.nds`:

| | |
| --- | --- |
| Header title, game code | `GHOSTTRICK-J`, `BGTJ` (134,217,728 bytes) |
| CRC32 | `105DDD9E` |
| SHA-1 | `323901c81e6e9300e2221e5cc42289cc5be73dce` |

`v1.1/v1.1.xdelta` is the v1.1 patch (xdelta3, VCDIFF); the build applies it
first. The patched v1.1 ROM is 119,459,746 bytes, CRC32 `D366A4D9`.

## Build

Requirements: the repository's Python environment (see the top-level README),
zsh, and `xdelta3` on the PATH (checked with 3.2.2).

```sh
zsh tools/build.sh
```

Output: `ghost-trick-kr-v1.2.nds` (119,462,534 bytes, CRC32 `EA51D7F3`) and
`release/v1.2/Ghost Trick (K) v1.2.xdelta`, identical to the released patch.
The patch bytes can differ between `xdelta3` versions, so compare the ROM
CRC32. Set `PYTHON` and `KRPATCH` to use another environment.

Steps: `krpatch xdelta apply` (v1.1) → `tools/check.py` (stops the build on
any problem) → `tools/build.py` → `krpatch xdelta make`.

For each script file (`stNN/*_Expand.xml.lz`, `system/*.bin`),
`tools/build.py` writes the lines of `tables/v1.2/script.tsv` one after
another into the Japanese script and updates the pointers and labels of the
lines that moved. Line heads (window and number) keep the Japanese values. The
ROM is rebuilt with `kr_patch.nds.rom`.

## Editing the script

`tables/v1.2/script.tsv` has one row per Japanese line. Columns: `file` (path
in the ROM), `run` (block of consecutive lines in the file), `i` (position in
the block), `ko` (the line). Notation in `ko`:

- Characters: Hangul (the 2,350 of KS X 1001) and the low characters of
  `tables/low.tsv` (digits, Latin letters, kana, symbols).
- `{01}` new line, `{02}` next window, `{XX}` and `{XX:a,b}` control codes
  (arguments in hex), `[hex]` values not in the table. Argument counts are
  `ARGS` in `tools/textcodec.py`.
- `{08:xx}` and `{1B:xx}` set the speaker, `{05:xx}` the text colour
  (`{05:f}` is the default colour).

To see the lines next to the Japanese, dump them (the output contains Japanese
text from the ROM, so it stays out of the repository):

```sh
../../.venv/bin/python tools/dump.py ghost-trick-jp.nds ghost-trick-kr-v1.2.nds work/side.tsv
```

After editing, `tools/check.py` looks for characters not in the table, control
code sequences that match neither v1.1 nor the Japanese line, lines wider than
the window (13 characters in windows with the portrait inside, 16 in full
width windows), more lines in one window than the Japanese, and leftover
Japanese.

```sh
../../.venv/bin/python tools/check.py ghost-trick-jp.nds work/build-v1.1.nds tables/v1.2/script.tsv
```

## Layout

| Path | Contents |
| --- | --- |
| `tables/v1.2/script.tsv` | v1.2 script (4,048 lines: 3,503 story, 545 in `system/`) |
| `tables/jp.tsv` | Japanese dialogue font code table (glyph number → character) |
| `tables/low.tsv` | 0x000–0x12B of the Korean code table (Hangul in KS X 1001 order follows) |
| `tools/` | build, check and emulator tools (usage in each file's first lines) |
| `v1.1/` | the v1.1 patch the build starts from |

## Tests

The emulator is the desmume libretro core. Build libretro/desmume at commit
`95b4d79` (2026-09-20) and put it at `compat/cores/desmume_libretro.dylib`
(`make -C desmume/src/frontend/libretro`). The melonDS DS v1.4.0 core stops
after loading the ROM, so it is not used.

```sh
# power on, send buttons and touches, take screenshots (save states carry on between runs)
../../.venv/bin/python tools/play.py ghost-trick-kr-v1.2.nds out --save s1.state --cmd "wait 600; press start; a 20; shot title"
# a test ROM whose "new game" starts at another stage and scene
../../.venv/bin/python tools/stage_rom.py ghost-trick-kr-v1.2.nds work/st06.nds 06 game004
# a ROM with one line replaced by test text (window width experiments)
../../.venv/bin/python tools/probe.py ghost-trick-jp.nds ghost-trick-kr-v1.2.nds work/probe.nds st01/st01_game000_Expand.xml.lz 0 0 "가나다라마바사아자차카타파하"
# a ROM that shows chosen lines in the first scene
../../.venv/bin/python tools/gallery.py ghost-trick-kr-v1.2.nds tables/v1.2/script.tsv work/gallery.nds st06/st06_game002_Expand.xml.lz:0:15
```

`tools/font_store.py` dumps the dialogue font (`fonts2bpp_new.imb`) to a
toolkit glyph store (JSON).

## License

Code (Python, shell): MIT, see the top-level `LICENSE`. The Korean script,
code tables and the v1.1 patch are fan translation data, distributed
non-commercially and not covered by the MIT license.
