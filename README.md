# kr-patches

English | [한국어](README.ko.md)

Source of perfectacle's Korean translation patches. Each game folder holds
what is specific to that game (assembly, script and name data, code tables,
build scripts, emulator test scripts) and the ROM analysis notes; the shared
tools come from [kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit)
(`krpatch` command, `kr_patch` package).

No ROM data is included. Every build starts from your own dump of the
Japanese cartridge, identified in each game's README by its header title,
CRC32 and SHA-1.

| Game | Patch | Base ROM (header title, CRC32) |
| --- | --- | --- |
| [Super Mario RPG](snes/super-mario-rpg/) | v1.2 | `SUPER MARIO RPG`, `5527071E` |
| [Otogirisou](snes/otogirisou/) | v1.2 | `OTOGIRISOU`, `8E4BEFD0` |
| [Dragon Ball Z: Super Gokuden – Totsugeki-hen](snes/dragon-ball-z-super-gokuden-totsugeki/) | v1.2 | `SFX DBZ TOTSUGEKIHEN`, `D531289B` |
| [Dragon Ball Z: Super Gokuden – Kakusei-hen](snes/dragon-ball-z-super-gokuden-kakusei/) | v1.3 | `ｽｰﾊﾟｰｺﾞｸｳﾃﾞﾝ ｶｸｾｲﾍﾝ`, `3172CD4F` |

Games are grouped by platform (`snes/`); other platforms will get their own
folder. Patch pages and downloads: <https://perfectacle.github.io/games/kr-patches/>.

## Setup

Python 3.15 (`.python-version`) and the toolkit pinned in `requirements.txt`:

```sh
uv venv -p 3.15.0 .venv
uv pip install -p .venv -r requirements.txt
```

The game build scripts use `.venv/bin/python` and `.venv/bin/krpatch` at the
repository root; set `PYTHON` and `KRPATCH` to use another environment. Some
builds also need [asar](https://github.com/RPGHacker/asar) 1.91, zsh, or the
macOS system fonts; see each game's README.

The toolkit is pinned to a release tag so that every build stays byte-identical to
the released patches. When moving the pin, rebuild each game and compare its
IPS with the released one before committing.

## Checks

`.github/workflows/ci.yml` runs what needs no ROM: Lua and shell syntax,
Python compilation, the `kr_patch` imports used by the game scripts, and the
Totsugeki-hen dialogue layout check. Builds and IPS comparisons need the base
ROMs and run locally.

## License

The code (assembly, Python, shell and Lua sources and build and test scripts)
is under the MIT license, see [LICENSE](LICENSE).

The translation data is separate from the code and not covered by the MIT
license: Korean scripts, dialogue and name tables, character code tables,
glyphs, graphics, and the patches of earlier versions that the builds start
from. It is fan translation data for copyrighted games, distributed
non-commercially for use with a cartridge you own. Do not sell it or
distribute it together with ROM images.

The Galmuri fonts in `snes/*/tools/fonts/` are under the SIL Open Font License
1.1 (`LICENSE.txt` next to each copy).
