# [NDS] Ghost Trick ROM analysis (Korean patch v1.2 work notes)

English | [한국어](ANALYSIS.ko.md)

```text
The ROM structure and methods confirmed while working on the Korean patch v1.2.
A record for anyone who analyses this ROM again or continues fixing the patch.
Patch page: https://perfectacle.github.io/games/kr-patches/nds/ghost-trick/

 - Target ROM: Japanese original, 134,217,728 bytes, game code BGTJ
   CRC32 105DDD9E / SHA-1 323901c81e6e9300e2221e5cc42289cc5be73dce
 - v1.1 ROM: Japanese + v1.1/v1.1.xdelta = 119,459,746 bytes, CRC32 D366A4D9
 - v1.2 ROM: output of tools/build.sh = 119,462,534 bytes, CRC32 EA51D7F3
 - Markers
   · [verified] checked by reading ROM bytes or running in an emulator
   · [inferred] guessed from the shape of the data or circumstances. Check it yourself before changing anything.
```

## 0. The v1.1 patch

```text
■ Format [verified]
xdelta3 (VCDIFF), 3,174,051 bytes, CRC32 66A7E057.
The header names the source "5017 - Ghost Trick (J).nds" and the output "고스트 트릭 (K)2.nds" (CP949).
The output ROM has the free space at the end cut off: 119,459,746 bytes.

■ What changed [verified]
arm9, arm7 and the overlays are unchanged. No code was changed, only data.
The ROM was repacked by another tool, so the FNT order changed and the same file has a different
number than in the Japanese ROM (fonts2bpp_new.imb: 16 in Japanese, 14 in v1.1). Always compare
and replace files by path.
150 of the 221 data files changed:

  stNN/*_Expand.xml.lz (138)   dialogue scripts (LZ11). Same unpacked size, only the lines moved
  system/database_0000_Expand.xml.bin, system/system_0000.msg.xml.bin
                               system messages and the notebook (uncompressed, same size)
  fonts2bpp_new.imb            dialogue font, 129,600 → 307,488 bytes (1,350 → 3,203 glyphs)
  font_db.imb                  16×16 4bpp (low nibble first), 128 bytes per glyph, 256 → 3,203 glyphs
  balloon_font.imb             speech balloon font, same format as font_db, 3,203 glyphs
  cpac_2d.bin                  2D graphics, 2,695 of the 16,508 entries in section 3
  cpac_3d.bin                  3D and texture graphics, 147 entries in section 0, 26 in section 3
```

## 1. Character table

```text
■ Glyph numbers [verified]
A line is a sequence of u16 glyph numbers. 0xFFxx is a control code (u16 arguments follow), 0x00FF is a space.
v1.1 gave all three fonts 3,203 glyphs so that they share the glyph numbers.
  0x000–0x12B  the same characters as Japanese (digits, Latin letters, kana, symbols). tables/low.tsv
  0x12C–0xA59  2,350 Hangul syllables in KS X 1001 order (가 = 0x12C … 힝 = 0xA59)
  0xA5A on     553 glyphs, not used by the v1.2 script

■ Japanese table (tables/jp.tsv) [verified]
The 1,350 glyphs of the Japanese dialogue font were read several times with macOS Vision OCR and
decided by majority, then characters that did not fit the context of the script were fixed by hand.
tools/dump.py uses it for the Japanese column.

■ Dialogue font fonts2bpp_new.imb [verified]
16×24, 2bpp, 96 bytes per glyph (4 bytes per row). One byte holds four pixels at bit positions
4, 6, 0, 2 in pixel order (the high nibble holds the first two pixels, low two bits first inside a nibble).
Found by drawing all 24 orders and taking the one where neighbouring pixels join most smoothly. tools/font_store.py
```

## 2. Scripts (1LMG)

```text
■ File layout [verified]
0x34-byte header: '1LMG', then u32 values. +0x08 is the code section size, +0x0C the name string size.
Code section (u16 words) → name strings → label table (u32 count, (name offset, file offset) pairs).

■ Lines [verified]
A line is an FF2D window number … FFFE block. Consecutive lines form a run; between runs are
bytecode and FFFD … FFFE event blocks, which stay in place.
Control codes inside lines (argument count):
  0  01 new line, 02 next window, 03, 0F, 16, 17, 21, 23
  1  05 text colour, 08 speaker, 0C, 0D, 0E, 15, 19, 1B speaker, 1C, 1E, 20, 22, 24, 25, 2B, 2C, 2E
  2  10, 27, 28, 2D (line head)
  3  1D
The argument counts come from comparing the same lines in the Japanese ROM and v1.1 (ARGS in tools/textcodec.py).

■ How the game finds lines [verified]
The game finds lines by pointer. A pointer is a u32 file offset after a u16 tag; the tags are
37, 51, 4C, 40, 5D, DB, 5C, 45, 3C, 0, 1, 2, FFFD, FFF4 and 228 (collected where v1.1 changed pointers).
The label table can point to lines as well. Swapping the numbers (FF2D arguments) of two lines in the
first scene left the screen the same.
Only system/database_0000 (the notebook) finds entries by number. An entry with a wrong number does not show.

■ Writing lines back [verified]
v1.1 kept the file size and the event block positions, wrote the lines of each run one after another
and fixed the pointers. repack in tools/lmg.py follows the same rule: it writes the new lines of each
run in order, fills the rest with zeros and fixes the pointers and labels of lines that moved. A run
that overflows is an error. Putting the v1.1 lines into the Japanese scripts gives 170 of 176 files
byte-identical to v1.1 (the other 6 are the v1.1 problems below).

■ Finding the v1.1 lines [verified]
v1.1 mostly kept the Japanese order, but some untranslated lines stayed in place, some numbers changed
and some runs keep copies of old lines in the leftover space. locate in tools/lmg.py finds each line by:
the position its pointer gives → the block after the previous line → the same (window, number) →
the same number → the first FF2D after the previous line.
Dumping the 3,503 story lines of v1.1 with tools/dump.py, writing them back and dumping again gives
the same lines and heads.
```

## 3. Problems found in v1.1 and what v1.2 does

```text
■ Scripts [verified]
 - Lines with an FFFE in the middle, so the rest never shows, and lines with spaces after FFFE.
   v1.2 writes every line again, so these are gone.
 - Two files whose label table was written one byte off: st07_game004, st15_demo060. Rebuilding from the
   Japanese scripts fixes them.
 - 28 lines whose FF2D window or number changed. v1.2 uses the Japanese values.
 - Notebook (database) entries that never showed because of a wrong number:
   268 「운명에 사로잡힌 사람」 and 512 「과거 카논의 집」.
 - Lines left in Japanese or garbled (st01_demo101, st06 27-4).
 - Colour arguments written as codes (FF05 FF06 where Japanese has FF05 0006), which breaks the
   highlight colour, and missing {05:f} that returns to the default colour.
 - Missing or swapped speaker codes, and lines without the notebook name link codes {29}…{2A}.
 - One joke line by the translators that is not in the original (st14).

■ The v1.2 script
All 4,048 v1.1 lines were reviewed against the Japanese (mistranslations, missing sentences, spelling,
consistent terms, line breaks). Names of people and places follow v1.1.
```

## 4. Dialogue window width

```text
■ Measured [verified] (desmume, one line replaced with test text by tools/probe.py)
Every glyph advances 14px, whatever the character (Hangul, kana, Latin, space). Narrowing the glyph
bitmap does not change the advance.
The window type decides how many characters fit on a line; characters past it are not drawn.
  windows with the portrait inside on the left (dialogue in the living world, Sissel alone)  x = 58–250, 13 characters
  full width windows with a large portrait above (dialogue in the ghost world)               x = 16 on, 16 characters
  narration on a black screen                                                                 checked up to 17 characters
The scene decides the window type, not the speaker code. tools/check.py guesses from the Japanese line:
13 characters when every Japanese line has 13 or fewer, otherwise 16 (or the Japanese length if longer).
```

## 5. Graphics

```text
■ cpac_3d.bin [inferred] (from the 2015 graphics analysis, not changed in v1.2)
0x20 header + 4 groups (start offsets aligned to 0x100). Each group has a fixed part
18 00 00 00 02 00 00 00 … 'YEKB' … 'TADB', a base (the header size, e.g. 0x1000) and then
(relative offset, size) pairs. A 0x80 top byte in a size has an unknown meaning.
An entry starting with 0x11 is LZ11. The zero fill between groups is kept as it is when repacking.
Image header (u32 ×9): fixed value, image count?, ?, header size, image size, palette offset, ?, width, height.

■ cpac_2d.bin [inferred]
Same structure (6 top-level groups, section 3 is KEYB/BDAT). Many 2D entries do not start with 0x11,
so they use another compression or none.
```

## 6. Emulator

```text
■ Automation [verified]
A desmume core built from libretro/desmume commit 95b4d79 (2026-09-20) runs through the toolkit's
libretro callbacks (tools/play.py). Touches go through the pointer device with the core variables
desmume_pointer_mouse=enabled and desmume_pointer_type=touch. Pointer coordinates span the whole
256×384 frame of both screens; the bottom screen starts at y 192.
The melonDS DS v1.4.0 core stops after loading the ROM.

■ Later scenes [verified]
tools/stage_rom.py changes the start path st01/st01_root.xml in route.xml to another stage and the
first scene file that stage's root loads, so "new game" starts in that scene. Earlier scenes are
skipped, so items and flags can differ from a real playthrough.
```
