# Super Mario RPG (SFC) Korean patch v1.2

Source of the Korean translation patch v1.2 for the Japanese *Super Mario RPG*
(Super Famicom). v1.2 is built on top of the Korean v1.0 patch: it
replaces the item, special and enemy names, rewrites the English item names
left in v1.0's dialogue, and fixes the battle result window and other menus.

Patch page: <https://perfectacle.github.io/games/kr-patches/sfc/super-mario-rpg/>

ROM layout, memory, text and font formats, hooks, free space used and debug
features are documented in [docs/ANALYSIS.md](docs/ANALYSIS.md) (Korean).

## Base ROM

No ROM is included. Use your own dump of the Japanese cartridge:

| | |
| --- | --- |
| Header title | `SUPER MARIO RPG` (SA-1, 4,194,304 bytes, no copier header) |
| CRC32 | `5527071E` |
| SHA-1 | `a9cd97041c4f8acf135d1ffb0a172748b5b976de` |

The build starts from that ROM with the v1.0 patch applied
(`v1.0/Super Mario RPG (K) (V1.0).ips`):

| | |
| --- | --- |
| Header title | `SUPER MARIO RPG (K)` |
| CRC32 | `F4305A06` |
| SHA-1 | `271370449e0f5910684172d1bf6aa4c5671822dd` |

## Build

Requirements: the repository's Python environment (see the top-level README),
[asar](https://github.com/RPGHacker/asar) 1.91, zsh.

1. Put the Japanese ROM at `rom/smrpg_jp.sfc` and make the v1.0 ROM:

   ```sh
   ../../.venv/bin/krpatch ips apply rom/smrpg_jp.sfc "v1.0/Super Mario RPG (K) (V1.0).ips" rom/smrpg_kr_v1.sfc
   ```

2. Put the asar executable at `tools/asar`.
3. Build `build/test.sfc` (CRC32 `05DBCBE6`):

   ```sh
   zsh tools/make.sh
   ```

4. Make the IPS against the Japanese ROM. The released patch was written with
   a record gap of 7; keep it so the output stays byte-identical:

   ```sh
   ../../.venv/bin/krpatch ips make --gap 7 rom/smrpg_jp.sfc build/test.sfc v1.2.ips --headered v1.2_headered.ips
   ```

`tools/make.sh` runs:

- `tools/build.py`: name tables, dynamic glyphs, reused dialogue-font codes and
  the level-up/special screen strings (`build/`).
- `tools/py/dlg_rewrite.py`: `build/dialogue.asm` with the rewritten dialogue.
- asar `--fix-checksum=on src/main.asm` on a copy of the v1.0 ROM.
- `tools/py/check_menu_names.py`: checks every name against the glyphs the menus
  draw; the build fails on a mismatch.

Set `PYTHON` (and `KRPATCH` for the test scripts) to use another environment.

## Layout

| Path | Contents |
| --- | --- |
| `src/main.asm` | the patch (asar) |
| `data/` | names, dialogue fixes, code tables (`data/tbl/korTBL*.tbl` are the v1.0 tables) |
| `tools/build.py`, `tools/py/` | build steps, text dump/verification, patch-note screenshots |
| `tools/*.sh` | build, test ROMs, Mesen 2 test runs |
| `test/` | test-only asar hooks (`test/harness/`), game-specific Mesen 2 scripts, fixtures |
| `compat/` | the same input on several emulators (`compat/run_all.sh`) |
| `v1.0/` | the v1.0 patch the build starts from |
| `tools/fonts/galmuri/` | Galmuri font (SIL Open Font License 1.1, `LICENSE.txt`) |

## Tests

- `tools/make.sh` runs `check_menu_names.py`; no emulator needed.
- `tools/test_menu.sh`, `tools/run_seq.sh`, `tools/make_states.sh` and the
  patch-note scripts need Mesen 2 at `tools/Mesen.app` and save states under
  `test/states/*.mss`, which are not included.
- Generic Mesen 2 scripts (`lib.lua`, `seq.lua`, `poke_state.lua`, `script.lua`,
  `dumpsrm.lua`) come from the toolkit: run them with
  `LIBDIR=$(../../.venv/bin/krpatch snes lua)`. The game's own scripts in `test/`
  (`probe.lua`, `banner_ids.lua`, `warp_seq.lua`) take the same `LIBDIR`.
- `compat/run_all.sh` expects libretro cores in `compat/cores/` and ROMs and
  `save_cookie.srm` in `compat/roms/` (docs/ANALYSIS.md section 8).

Tools that used to ship in this folder and now come from
[kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit):

| Old file | Use instead |
| --- | --- |
| `tools/py/make_ips.py` | `krpatch ips make --gap 7 ... --headered ...` |
| `tools/py/dis65816.py` | `krpatch snes dis ROM ADDR COUNT` (block moves print as `MVN src,dst`) |
| `tools/py/tiles.py`, `glyphs.py`, `vramchr.py` | `krpatch snes tiles` (`--rows`, `--stride`, `--tall`) |
| `tools/py/bgrender.py`, `vramrefs.py` | `krpatch snes bg`, `krpatch snes bgrefs` |
| `tools/py/shotcmp.py`, `contact.py`, `diffr.py` | `krpatch shotcmp`, `krpatch contact`, `krpatch diff` |
| `compat/lr.py`, `compat/mesen_run.lua` | `krpatch snes run ... --watch 7E0052:3`, `script.lua` with `WATCH_WRAM=7E0052:3` |
| `test/lib.lua`, `seq.lua`, `poke_state.lua`, `compat/dumpsrm.lua` | the same scripts in `krpatch snes lua` |

docs/ANALYSIS.md still names the old files where it describes how something
was found.

## License

Code (asm, Python, shell, Lua): MIT, see the top-level `LICENSE`. The Korean
text, name tables and graphics are fan translation data, distributed
non-commercially and not covered by the MIT license. Galmuri is under the SIL
Open Font License 1.1.

## 한국어 요약

슈퍼 마리오 RPG(일본판) 한글패치 v1.2의 소스입니다. v1.0 한글판 롬 위에 덧씌워 빌드합니다.

- 준비물: 일본판 롬(헤더 제목 `SUPER MARIO RPG`, CRC32 `5527071E`)을 `rom/smrpg_jp.sfc`로, asar 1.91을 `tools/asar`로 둡니다.
- `v1.0/` 의 IPS로 v1.0 롬(CRC32 `F4305A06`)을 `rom/smrpg_kr_v1.sfc`로 만들고 `zsh tools/make.sh` 를 실행하면 `build/test.sfc`(CRC32 `05DBCBE6`)가 나옵니다.
- IPS는 `krpatch ips make --gap 7` 로 만듭니다. 배포한 IPS와 바이트 단위로 같습니다.
- 롬 분석 노트는 [docs/ANALYSIS.md](docs/ANALYSIS.md) 에 있습니다.
- 코드는 MIT, 한글 대사·이름표·그래픽은 비상업 배포하는 번역 데이터로 MIT와 별개입니다.
