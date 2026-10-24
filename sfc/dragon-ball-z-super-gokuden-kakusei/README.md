# Dragon Ball Z: Super Gokuden – Kakusei-hen (SFC) Korean patch v1.3

Source of the Korean translation patch v1.3 for the Japanese *Dragon Ball Z:
Super Gokuden – Kakusei-hen* (Super Famicom). The build starts from the
Japanese ROM with the Korean v1.1 patch applied, undoes v1.1 text that
overwrote live data, then replaces the title screen, dialogue, battle speech
bubbles and ending credits and makes passwords from the Korean Totsugeki-hen
readable on the password screen.

Patch page: <https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-kakusei/>

ROM map, text and font formats, the v1.1 progression bug, title, credits,
debug menu, save RAM, Mesen 2 usage and the Totsugeki-hen password are
documented in [docs/ANALYSIS.md](docs/ANALYSIS.md) (Korean; it was the
README.txt of the published tool zip).

## Base ROM

No ROM is included. Put your own dump of the Japanese cartridge in this folder
as `super-gokuden-jp.smc`:

| | |
| --- | --- |
| Header title | `ｽｰﾊﾟｰｺﾞｸｳﾃﾞﾝ ｶｸｾｲﾍﾝ` (half-width katakana; LoROM, 2,097,152 bytes, no copier header) |
| CRC32 | `3172CD4F` |
| SHA-1 | `3b7278a54f8d470dcb1bd92060d744380325f30b` |

`v1.1/v1.1.ips` is the v1.1 patch; the build applies it first.

## Build

Requirements: the repository's Python environment (see the top-level README),
zsh, macOS. `tools/title.py` draws the title with the BM YeongSung font from
the macOS system font assets; on other systems change `TITLE_FONT` in
`tools/title.py`.

```sh
zsh tools/build.sh
```

Output: `super-gokuden-kr-v1.3.smc` (CRC32 `B9F14962`) and
`release/v1.3/*.ips` (plain and 512-byte copier header), identical to the
released patches. The build also rewrites `tables/kr-v1.3.txt` (the v1.3 code
table, including new glyphs); a clean build leaves it unchanged. Set `PYTHON`
and `KRPATCH` to use another environment.

Steps: `krpatch ips apply` (v1.1) → `fix_overwrites.py` → `title.py` →
`dialogue_patch.py` → `bubble_patch.py` → `password.py` → `credits.py` →
`check_width.py` (fails the build when a line is wider than its window) →
`krpatch sfc checksum --fix` → `krpatch ips make --headered`.

## Layout

| Path | Contents |
| --- | --- |
| `tools/` | build and analysis scripts (usage in each file's first lines) |
| `tables/dialogue-v1.3.tsv`, `bubbles-v1.3.tsv` | corrected dialogue and battle speech bubbles (`/` = line break) |
| `tables/jp.txt`, `kr.txt`, `kr-v1.3.txt` | Japanese, v1.1 and v1.3 code tables |
| `tables/totsugeki-password.tsv` | Totsugeki-hen password glyphs and pair table |
| `v1.1/` | the v1.1 patch the build starts from |
| `lua/` | Mesen 2 scripts for this game (`dbgscene.lua`, `crjump.lua`) |
| `compat/` | the same input on Mesen 2 and libretro cores (`compat/run_all.sh`) |
| `tools/fonts/` | Galmuri fonts (SIL Open Font License 1.1, `LICENSE.txt`) |

## Tests

`tools/check_width.py` runs inside the build. Mesen 2 scripts (debug menu
needed, see docs/ANALYSIS.md section 9) load the toolkit's `lib.lua` from
`LIBDIR`:

```sh
LIBDIR=$(../../.venv/bin/krpatch sfc lua) TARGET=50 SHOT_DIR=out Mesen --testrunner debug.smc lua/dbgscene.lua
```

`compat/run_all.sh` plays `compat/s_*.txt` on Mesen 2 (toolkit `script.lua`)
and libretro cores (`krpatch sfc run`), logging the scene word `$7E029C`.

Files that used to ship in this folder and now come from
[kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit):

| Old file | Use instead |
| --- | --- |
| `tools/ips.py` | `krpatch ips make`, `krpatch ips apply` |
| `tools/fixsum.py` | `krpatch sfc checksum --fix --mapper lorom` |
| `tools/lz.py` | `kr_patch.lzss`, `kr_patch.sfc.tiles.planar_to_sfc`/`sfc_to_planar`, `krpatch lzss` |
| `lua/lib.lua` | `lib.lua` in `krpatch sfc lua` |
| `lua/compat.lua` | `script.lua` in `krpatch sfc lua` with `WATCH_WRAM=7E029C:2 WATCH_FMT=%03x` (`LUA_DIR` is now `LIBDIR`) |
| `compat/lr.py` | `krpatch sfc run ... --watch 7E029C:2 --watch-fmt 03x` |

docs/ANALYSIS.md still names the old files where it describes how something
was found.

## License

Code (Python, shell, Lua): MIT, see the top-level `LICENSE`. The Korean text,
code tables and graphics are fan translation data, distributed
non-commercially and not covered by the MIT license. Galmuri is under the SIL
Open Font License 1.1.

## 한국어 요약

드래곤볼 Z 초오공전 각성편(일본판) 한글패치 v1.3의 소스입니다. 일본판에 v1.1 패치를 적용한 롬에서 시작해 v1.1이 덮어쓴 데이터를 되돌리고 타이틀, 대사, 전투 말풍선, 엔딩 크레딧, 돌격편 암호 입력을 고칩니다.

- 준비물: 일본판 롬(헤더 제목 `ｽｰﾊﾟｰｺﾞｸｳﾃﾞﾝ ｶｸｾｲﾍﾝ`, CRC32 `3172CD4F`)을 이 폴더에 `super-gokuden-jp.smc` 로 둡니다. 타이틀 글꼴 BM영성체는 macOS 시스템 글꼴에서 읽습니다.
- `zsh tools/build.sh` 를 실행하면 `super-gokuden-kr-v1.3.smc`(CRC32 `B9F14962`)와 배포한 것과 같은 IPS 두 개가 `release/v1.3/` 에 나옵니다.
- 롬 분석 노트(배포 zip의 README.txt)는 [docs/ANALYSIS.md](docs/ANALYSIS.md) 로 옮겼습니다.
- 코드는 MIT, 한글 대사·코드표·그래픽은 비상업 배포하는 번역 데이터로 MIT와 별개입니다.
