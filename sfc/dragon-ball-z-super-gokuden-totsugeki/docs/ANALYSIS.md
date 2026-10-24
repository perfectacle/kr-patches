# [SFC] Dragon Ball Z: Super Gokuden – Totsugeki-hen ROM analysis (Korean patch v1.2 work notes)

English | [한국어](ANALYSIS.ko.md)

```text
The ROM structure and methods confirmed while working on the Korean patches v1.1 and v1.2.
A record for anyone who analyses this ROM again or continues fixing the patch.
It is best read together with the analysis of Super Gokuden Kakusei-hen, which uses the same engine.
Patch page: https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-totsugeki/
Kakusei-hen page: https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-kakusei/

 - Target ROM: Japanese original, no header, 2,097,152 bytes (LoROM)
   CRC32 D531289B / MD5 8BD89634D1B2205B1E7EF016485C0076
 - v1.0 ROM: Japanese + v1.0/v1.0.ips = CRC32 52FEF8C3
 - v1.1 ROM: CRC32 7405D969 (output of tools/build.sh in the v1.1 tool bundle)
 - v1.2 ROM: output of tools/build.sh = CRC32 A939C4F8
 - Address notation below
   · $XX:YYYY = SFC address (bank:address)
   · file 0xNNNNN = offset in the headerless ROM file
   · LoROM conversion: file offset = (bank & 0x7F) × 0x8000 + (address & 0x7FFF)
 - Markers
   · [verified] checked by reading ROM bytes, disassembling, or running in an emulator
   · [notes]    checked during the work and written in the notes, but not rechecked while writing this document
   · [inferred] guessed from the shape of the code or circumstances. Check it yourself before changing anything.
```

## 0. ROM header and memory

```text
■ ROM header (file 0x7FC0-0x7FFF) [verified]
  0x7FC0  title       "SFX DBZ TOTSUGEKIHEN " (21 bytes)
  0x7FD5  map mode    30   LoROM, FastROM
  0x7FD6  cartridge   02   ROM + RAM + battery
  0x7FD7  ROM size    0B   2^11 KB = 2MB
  0x7FD8  SRAM size   03   2^3 KB = 8KB
  0x7FD9  region      00   Japan
  0x7FDA  maker       33   (marks an extended header)
  0x7FDB  version     00
  0x7FDC  checksum complement / 0x7FDE checksum (little-endian)
          Japanese EF0F / 10F0, v1.1 D498 / 2B67
  reset vector (0x7FFC) $8000, NMI vector (0x7FEA) $818D

■ Memory
  ROM   2MB   banks $80-$BF, $8000-$FFFF in each bank (32KB × 64)
  WRAM  128KB
  VRAM  64KB
  SRAM  8KB   the SRAM size value in the ROM header

■ WRAM variables in this document
  $4D     dialogue ID to show now (read by the dialogue bank dispatch $81:AC4C) [verified]
          The graphics loading routines ($81:A703, $81:A8B0) also use this location briefly. [verified]
  $0200   character code the renderer is drawing (stored at $B7:9767) [verified]
  $0208   x position (px) where this character starts on the current line [verified]
  $020A   window width (px) = $020E × 8 (stored at $B7:9737) [verified]
  $020E   window width (in 8px cells) [verified]
  $0210   window height (in 8px rows). 6 for dialogue windows = 3 lines of text [verified]
  $32     current line position (in 8px rows, +2 per line) [verified]
  $7E:0263  ADV (scenario) number of the debug menu, 1 byte [notes]
  $011C   when 0, START while dialogue waits opens the story status [notes]
  $0119   save slot number [notes]
```

## 1. Boot and debug menu

```text
■ Where the debug menu is skipped [verified]
The loop that runs after reset ($80:805E-$80:8078) contains these bytes.

  $80:8061 (file 0x61)  80 04        BRA $8067    always skips 4 bytes
  $80:8063 (file 0x63)  22 B0 86 82  JSL $8286B0  debug menu routine
  $80:8067 (file 0x67)  22 00 80 82  JSL $828000  the retail game goes straight here

 - Changing 80 04 at file 0x61 to EA EA (NOP NOP) opens the debug menu.
 - Menu: TITLE / FMAP / BATTLE / ADVENTURE / DATA / VOICE / ADVSE / BTLSE
 - ADVENTURE: MESS CHECK / FLAG ON/OFF / SCENARIO SELECT / SCENARIO START / AREAMAP PICTURE
   · Pick an ADV number ($7E:0263) in SCENARIO SELECT and confirm with A
     → SCENARIO START starts that scenario as in real play. [verified]
   · Numbers 0x00-0xFF are all valid. [notes]
   · It starts with the scene progress flags reset, so dialogue scenes come out as in real play. [notes]
 - The fifth item of DATA (ENDING) shows the ending from the start. [verified]
 - The released v1.1 IPS does not change this byte. The debug menu opens only in a separately modified ROM.
```

## 2. Dialogue

```text
■ IDs and banks [verified]
 - IDs 0x000-0x14F9 (5,370 lines). For the last bank ($8E), the table is taken to run up to the first pointer.
 - Dispatch routine $81:AC4C: compares the ID in $4D with CMP #$14AD, #$121F … #$025C in that order
   to pick the bank, then reads the pointer from that bank's table, as in LDA $A88000,X.

     ID range       bank  pointer table  v1.1 string area use
     000-25B        A8    $A8:8000      27,164 / 31,520 bytes
     25C-570        A9    $A9:87D6      25,284 / 29,144
     571-81B        AB    $AB:8000      27,742 / 31,328
     81C-A64        9D    $9D:8000      28,376 / 31,484
     A65-CC6        9E    $9E:8000      27,582 / 31,512
     CC7-F57        B2    $B2:8000      27,452 / 31,380
     F58-121E       B4    $B4:8000      27,184 / 31,312
     121F-14AC      B5    $B5:8000      28,058 / 31,430
     14AD-14F9      8E    $8E:B67A       4,284 /  4,774 (including 7 battle shouts)

   The denominator is the area the Japanese strings occupied (build log).
   $A9:8000-$A9:87D5 holds the choice table and strings.

 - Pointers are 2 bytes, addresses within the same bank. Dialogue cannot leave its bank.
 - v1.1 refilled each bank's whole Japanese string area from the start.
   Identical strings are stored once and shared by several pointers.
   So fixing one string in place can change other IDs too.

■ String format [verified]
 - One character = 16-bit little-endian code
 - 0x000A = line break, 0x0000 = end
 - Codes with the top bit (0x8000) set are drawn as small characters (8px/12px wide).
 - Space is 0x02C5, 「‥」 0x016B, 「！」 0x016C (per the v1.0/v1.1 character table)

■ Example: dialogue 0x006 「어떻게/잡아 볼까‥」 (v1.1) [verified]
  1) 0x006 is in range 000-25B → bank $A8, table $A8:8000
  2) $A8:8000 + 0x006 × 2 = $A8:800C (file 0x14000C) → FE 85 → $85FE
  3) the string starts at $A8:85FE (file 0x1405FE)
       F3 08  어      B5 06  떻      27 05  게      0A 00  line break
       A1 09  잡      C6 08  아      C5 02  space   E5 07  볼
       85 05  까      6B 01  ‥      00 00  end
  4) window info: $8E:C9BA + 0x006 × 2 = $8E:C9C6 (file 0x749C6) → 19 06

■ Window info and window width
 - Each dialogue has 2 bytes of window info at $8E:C9BA + ID × 2. [verified]
 - Code that sets the window size: $81:AD51-$81:ADDD [verified]
   It branches on the first byte of the window info (stored in $0239).
     FF          narration window  $020E = 0x16 (22 cells = 176px), $0210 = 6
     FE          $020E = 0x10 (16 cells = 128px), $0210 = 6. Unlike the face window it
                 skips the calls to $81:B004, $81:D046 and $81:D047 (screen not checked)
     FD          ends without opening a window ($81:AE07)
     other       face window   $020E = 0x10 (128px), $0210 = 6. The second byte goes to $023F
   Of the 5,370 Japanese dialogue lines, 38 are FF, 347 FE, 0 FD and 4,985 other.
   Then $B7:9621 → $B7:9729 sets $020A = $020E × 8 and clears $0208 and $32.
 - The same code in Kakusei-hen is at $80:B879 (narration 0x15 cells, face 0x10 cells).
   The Totsugeki-hen narration window is one cell (8px) wider than Kakusei-hen's.
 - Character widths are set by comparisons inside the renderer, not by a table. ($B7:97DC-$B7:9846) [verified]
     codes 0xBE4 / 0xBE5 / 0xBE6 / 0xBE7  2 / 4 / 6 / 7px
     small characters with 0x8000 set     8px below 0x500, 12px from 0x500
     0x500 and above                      13px (kanji slots = Hangul)
     0x2C7, 0x2A2                         5px
     0x2C6                                4px
     other (0x100-0x4FF, kana slots)      9px
   tools/width1.py follows the same rules.
 - Automatic line breaks [verified]
     $B7:9846  CLC / ADC $0208     this character's width + current x = right edge of this character
     $B7:984A  CMP $020A           compare with the window width
     $B7:984D  BEQ / BCC $B79890   if equal or less, draw it as is
     $B7:9851  INC $32 ×2          if greater, go to the next line ($32 += 2)
     $B7:9857  CMP $0210           if $32 is $0210 or more, page wait ($B7:985E) then a new page
   So a line holds characters until the sum of their widths equals the window width.
   The limits are 176px for narration and 128px for the face window; 1px over and the last character moves to the next line.
 - Checked in Mesen 2: dialogue 0x000 (narration) of the v1.1 ROM was replaced with test lines and shown in a new game.
     「어」×8 + 「！」×8 = 176px   fits on one line
     「어」×6 + 「！」×11 = 177px  the last 「！」 moves to the third line ($B7:9851 runs)
   In a ROM with the window info changed to 19 00 (face window), 128px fit and 129px wrapped.
   When a line exceeds the width, its last characters are pushed to the next line,
   and if that is the fourth line they appear alone on the next page. [verified: screen of dialogue 0x1022]
 - The longest lines in the v1.1 ROM are 174px for narration, 128px for the face window and 127px for FE windows.
   In the Japanese ROM, the first line of narration dialogue 0x000 is exactly 176px. [verified]
 - Counting the v1.0 ROM with the rules above (first window info byte FF = 176px, otherwise 128px),
   13 dialogue lines exceeded the width (IDs 033A 05C1 0D62-0D69 0EA6 0F3F 1022). [verified]
   v1.1 has 0 (tools/layout1.py).
```

## 3. Other text (pointer tables)

```text
 Collected in tools/textsets.py. All are 16-bit pointers, addresses within the bank. [verified]

     name        bank  table         count   v1.1 use          contents
     battle      B1    $B1:9C34      769   15,338 / 19,820   battle dialogue
     event       AD    $AD:8000      204    4,706 /  8,770   event list in the story status
     choice      A9    $A9:8000      117    1,826 /  5,632   choices
     minigame    98    $98:8000       56    1,422 /  3,456   mini-games
     place       87    $87:8000      100    1,210 /  3,166   place names
     map         82    $82:B306       54        -            map names (unchanged in v1.1)
     tech        84    $84:B605     (auto)  1,394 /  6,053   technique names
     advice      9F    $9F:8000     (auto)  8,704 / 11,642   ally comments (232 entries, 132 unique)
     enemy       AE    $AE:C910       55      462 /  2,108   enemy names in battle
     save        81    (12 LDA # operands)    544 /    840   save scene dialogue

 (auto) = the table is taken to run up to the address of the first string.
 save has no table; the LDA #$xxxx operands in bank $81 code are the pointers.
 Operand locations (file): D85A D860 D8C1 D86E D874 D882 D6AE D6BF D6D0 D6E1 D6F2 DA23
 The 7 battle shouts are in $8E; their pointers are LDA # operands in $81.
 Operand locations (file): E300 E380 E43F E573 E69B EB14 EB80 [verified]

 The ally comment window is 128px, and the name is attached to the first line. [notes]
```

## 4. Font (variable width)

```text
■ Location [verified]
 - Renderer $B7:9763. It picks a sheet by code range and continues drawing at $B7:97D6.

     code          size    location                      where the sheet is picked
     0x100-0x4FF   8x16    $83:DE00 + (code-0x100)*16    $B7:9785
     0x500-0x7EF   16x16   $83:8000 + (code-0x500)*32    $B7:97A0
     0x7F0-0xBEF   16x16   $BF:8000 + (code-0x7F0)*32    $B7:97BC
     0xC00-0xFFF   16x16   blocks added in v1.1 (below)  $B7:FA00

 - One sheet row = 0x100 bytes. 8 16x16 glyphs per 0x200 bytes, the lower half at +0x100.
   Only codes where (code - start code) ÷ 8 is even start a glyph.
 - 2bpp: one tile row is 2 bytes (plane 0, plane 1).
   Glyph pixel = only plane 0 set (colour 1), shadow pixel = both planes set (colour 3).
   The shadow is whichever of the right, lower and lower-right neighbours of a glyph pixel is not itself a glyph pixel.
   Every glyph v1.1 drew follows this rule (draw_glyph in tools/text_patch1.py).

■ Slots used by v1.0 [notes]
 - It replaced 850 kanji slots and 160 kana slots with Hangul (1,010 characters).
 - Of the kana slots, 0x100-0x166, 0x180-0x1E6 and 0x200-0x261 are 8px-wide Hangul
   (for menus, NARROW_HANGUL in tools/kr1.py).

■ Glyphs added in v1.1 (tools/fontext1.py) [verified]
 - Hook: $B7:97BC (file 0x1B97BC)
     Japanese  38 E9 F0 07   SEC / SBC #$07F0
     v1.1      5C 00 FA B7   JML $B7FA00
 - New code: $B7:FA00-$B7:FA77 (file 0x1BFA00, 0x78 bytes, 0xFF in the Japanese ROM)
     +0x00  CMP #$0C00 / BCS ext, otherwise the original $BF handling then JML $B797D6
     +0x23  ext: subtract 0xC00, divide by 0x80 for the block number, remainder × 32 = position in the block
     +0x60  block address table (2 bytes × 8)
     +0x70  block bank table (1 byte × 8)
 - One block is 4KB = 128 codes (64 glyphs); 8 blocks = 512 glyphs
     block code         location    file       v1.1
     0     C00-C7F      $81:EF00    0x0EF00    used
     1     C80-CFF      $84:EE00    0x26E00    used
     2     D00-D7F      $86:E000    0x36000    used (v1.1 up to D57, v1.2 up to D63)
     3     D80-DFF      $86:F000    0x37000    empty
     4     E00-E7F      $A6:E600    0x136600   empty
     5     E80-EFF      $AE:EA00    0x176A00   empty
     6     F00-F7F      $B1:E500    0x18E500   empty
     7     F80-FFF      $B6:E600    0x1B6600   empty
   All 8 locations were 0xFF for the full 4KB in the Japanese ROM and v1.0.
 - The width calculation already treats everything from 0x500 as 13px, so it needed no change.
 - 213 glyphs newly drawn by v1.1
   · 37 slots that fell out of use (0x587, 0x6F5 … 0xBE3. "new glyph" in the build log)
   · 176 in the new blocks (0xC00-0xD57)
   v1.2 drew 「펴」 (0xD60) and 「플」, 「딩」 and 「렉」 (0xD61-0xD63) (section 11).
   「플」, 「딩」 and 「렉」 had no 16px glyph and were written with the 8px glyphs in kana slots (0x24B, 0x148, 0x14D),
   which looked half-width between 16px glyphs (WIDE_ONLY in tools/text_patch1.py).
   The 8px glyphs stay in use for name entry and the ending password.
   New glyphs were drawn with Galmuri11 at 12px, with the shadow added by the rule above.
 - Example: 「쫓」 = 0xCE5
     0xCE5 - 0xC00 = 0xE5 → block 1 ($84:EE00), 0x65 within the block
     $84:EE00 + 0x65 × 32 = $84:FAA0 (file 0x27AA0)
     upper tiles 0x27AA0 and 0x27AB0, lower tiles 0x27BA0 and 0x27BB0
```

## 5. Title screen

```text
 - Compression: LZSS, the same format as Kakusei-hen (tools/lz.py) [verified]
   The format is explained in the "Compressed title graphics" section of the Kakusei-hen page.
 - Decompression routines [verified]
     $81:DF4F   A = compressed data address, X (8-bit) = bank. Decompresses to $7E:8000 and leaves the size in $F0
     $81:DFE7   calls $81:DF4F, then at $81:DFEB swaps the plane order of every 16-byte tile
   In the Japanese ROM, JSL $81DF4F appears 15 times (excluding the 1 inside $81:DFE7) and JSL $81DFE7 26 times.
   The title is loaded by the two loading routines below.
     $81:A703   entry A of table $81:A743 (5-byte entries) → $81:DF4F → JSL $81DFEB (tiles)
     $81:A8B0   entry A of table $81:A8EC (5-byte entries) → $81:DF4F (tilemaps etc.)
   Order recorded in Mesen 2 after boot (same in the Japanese ROM and v1.1):
     frame 114  $81:A703 #4 → $B7:ACCF     frame 126  $81:A703 #3 → $B7:9EB1 (title tiles)
     frames 135, 137, 139  $81:A8B0 → $B7:BAB9, $B7:BD47, $B7:B94F
     frame 536  $81:A8B0 #39 → $B7:BE7F (title tilemap)
 - $80:9CFA and $80:9DA7 in the header comment of lz.py are the Kakusei-hen decompression routine addresses.
   In Totsugeki-hen, $80:9CFA is in the middle of menu cursor code. The format is the same, so lz.py works as is.
 - Two BG3 data sets for the title, 5-byte entries (address low, address high, bank, size low, size high) [verified]
     data              entry (file)      data         compressed size Japanese → v1.1
     2bpp tiles        0xA752            $B7:9EB1     0xE1D → 0xCA5 (3,613 → 3,237 bytes)
     32x32 tilemap     0xA9AF            $B7:BE7F     0x30D → 0x30B (781 → 779 bytes)
 - v1.1 recompressed both and put them back in place. The entries are unchanged from the Japanese ROM. [verified]
   If they grow, title.py moves them to free space (file 0x13F300 = $A7:F300, 0x17FB40 = $AF:FB40)
   and fixes the entries. Both locations are 0xFF in the Japanese ROM and still empty in v1.1.
 - The cell layout is identical to Kakusei-hen, so the Kakusei-hen v1.2 tool was reused with only the addresses changed.
 - The "DRAGON BALL Z" logo and "(c) BANDAI 1995" are left as in the original.
   This (c) tile is shared with the first copyright line, so do not touch it. [notes]
```

## 6. Menu strings (outside the pointer tables) [notes]

```text
 tables/ui-fixes.tsv: file offset, current string, new string[, maximum code count]
 - Title menu: file 0x6F17 (NEW GAME / OPTION), 0x6F3D (CONTINUE / NEW GAME / OPTION)
   The selection highlight follows the text position, so only the cells need to line up.
 - Event list header $80:F530 (location v1.0 moved it to), first footer string $80:BE3A
   v1.0 code reads the second footer string from $80:F54A+X,
   so the length of the first string (8 codes) must not change.
 - Ending credits: a fixed slot in bank B7 per line (cast from file 0x1BDE83, staff from 0x1BE5F1)
   The slot sizes are set by the Japanese line lengths, so a line cannot be longer.
   Cast column centres: 3 columns 48/128/208px, 2 columns 88/168px (tools/credits1.py)
 - Status screen (story status) and the screens under it [verified]
   v1.0 wrote 「기술」, 「습득」, 「완료」 and 「클리」 with glyphs that squeeze two syllables into one 16px cell
   (0xB97, 0xBA0, 0xBA1, 0xBA2). v1.2 no longer uses them.
   · Right-hand menu $80:C947: window size table $80:EEEB entry 9 = 6 cells (48px). Four 16px glyphs take 52px,
     so all three lines use small glyphs with 0x8000 set (the same 16px glyph, 12px apart; the Japanese ROM used 12px kanji).
     The selection highlight (red) is $80:C833 changing the palette of 6 tilemap cells.
   · Technique-menu category window $80:B599 (entry 6, 48px): same method. The string may run to 0x35C7, the end of the Japanese area.
     $80:D803 LDA #$B5A3, which reads the same string, still had the Japanese address after v1.0 moved it; v1.2 sets it to $B599.
   · Categories in the technique list rows, $80:F317/F321/F32D/F339 (odd addresses): 4 codes per slot, written as four 16px glyphs.
   · Marks in the technique list and the event list: $80:40BC and $80:3D83 write one code to the row buffer ($0A00,Y),
     0xBA0/0xBA1 when learned/cleared, otherwise the blank glyph 0xAD5. v1.2 turns both into a JSL to routines at
     $B7:FB00 and $B7:FB32 that write two 16px glyphs (or two blanks) and the space after them (tools/statusmenu1.py).
     So that the mark reads with its number rather than the next word, the space after the number (9px) becomes {sp4}
     and the space after the mark is 9px in the technique list and 12px in the event list.
     Both lists are 224px (28 cells) wide; the longest rows are 224px (techniques) and 223px (events).
   · Some screens that join strings in WRAM read the next string right after the previous one, so code counts must not change:
     the achievement label $80:BAB2 (19 codes) and the first label of the status screen bottom line $80:C9C5 (5 codes; v1.0 code
     reads the second label from $80:F56C+X). The bottom line fills its 224px window, so the second label became 「총 시간」.
```

## 7. Clear table event list problem (fixed in v1.1)

```text
 - How to get there: START while dialogue is shown → story status ($80:C218)
   → 「클리어 표」 (clear table) in the right-hand menu → B on the technique table → event list
   (START in the dialogue wait loop $81:BE6F, when $011C is 0) [notes]
 - The scroll-down condition is CMP #$00CD (205) at $80:BC8A. There are 204 events (0-203). [verified]
 - At the bottom it draws a hidden 205th row (number 204);
   the pointer slot for this row ($AD:8198, file 0x168198) holds the character code of the first event name.
   It is read as an address, and the WRAM value at that address is printed as a string.
     Japanese A5 05 → $05A5,  v1.0 86 06 → $0686,  v1.1 FA 93 → $AD:93FA (00 00, empty string) [verified]
 - If the end marker comes late at that address, the row overflows and B can no longer close the list.
   Pressing A then goes to the technique setup screen.
   In v1.0 the list actually failed to close at 0xC0 among debug scenarios 0x00-0xF8 (every 8),
   and in v1.1 two presses of B return to the game in the same scene. [verified, lua/eventlist.lua]
 - Event names must fit in the 160px left after the number prefix (64px). [notes]
```

## 8. Regression tests (Mesen 2)

```text
 - Every dialogue reads its window info ($8E:C9BA + ID*2), so watching reads of this area records the dialogue IDs.
 - All 256 scenarios were played for 8000 frames each with A mashing on the Japanese ROM and v1.1,
   and the sequences of dialogue IDs compared. (lua/scenario.lua, tools/rgcmp1.py) [verified]
   No scenario had a different order or stopped earlier on v1.1.
   (The only differences were cases where v1.1 got further in the same time because the Korean lines are shorter)
 - Holding A for several frames finishes the text output and turns the page at once,
   so the page is never fully shown. Captures used single-frame presses.
 - Screenshots were taken every 3 frames, and the frame just before the white text in the lower half is erased
   was picked as the finished page. (tools/pages1.py)
 - Checking the line width limit: build test ROMs with tools/wintest1.py and run a new game with lua/wintest.lua.
     python3 tools/wintest1.py super-gokuden-kr-v1.1.smc wt
     SHOT_DIR=wt/narr Mesen --testrunner wt/narr.smc lua/wintest.lua
   wt/narr/log.txt records WINSET (window size), chk (the value compared at $B7:984A) and WRAP (line wrap).

■ Emulator compatibility [verified]
 - compat/lr.py: a small program that loads libretro cores directly and feeds them the same input.
   compat/run_all.sh runs a new game (s_new.txt) and a continue (s_cont.txt, v1.0 save) on each core.
   Mesen 2 plays the same input file with compat/mesen.lua.
     SCRIPT=compat/s_cont.txt SRM=roms/save.srm SHOT_DIR=out Mesen --testrunner v11.sfc compat/mesen.lua
 - ROMs: Japanese, v1.0, v1.1, v1.2, and headered v1.1 and v1.2 (512 bytes). 16,000 frames.
   Apart from five different cells of the character board on the name entry screen (frames 2,000-4,000),
   v1.2 gave the same screens and the same dialogue ID order as v1.1 on every core.
     Mesen 2.1.1              OK. Continue dialogue ID ($4D) order identical on all six ROMs
     bsnes, bsnes-hd beta     OK (bsnes-hd beta outputs 216 lines)
     snes9x, snes9x2010       OK. snes9x2010 also has the same continue dialogue ID order on all six ROMs
     Beetle Supafaust         OK. The new game drifts by a few frames and takes a different path on the field
                              (the Japanese ROM diverges by the same amount between cores)
     Mesen-S core             undetermined. Even the Japanese original exits immediately in lr.py (exit 139)
 - On five libretro cores, headered and headerless v1.1 gave pixel-identical screens.
 - In the continue run, a black screen follows after the dialogue ends (about 4,700 frames).
   The Japanese ROM shows the same screen at the same point on every emulator, so it is unrelated to the patch.
   At that point the CPU is at $80:8147 (frame wait loop).
 - The bsnes, bsnes-hd beta and Supafaust cores do not expose WRAM to lr.py, so wram.log is empty
   and only the screens were compared.
```

## 9. Saves (SRAM)

```text
 - SRAM 8KB (ROM header 0x7FD8 = 03) [verified]
 - Save routine $81:D210 (slot number $0119), load $81:D3A9 [notes]
   JSLs calling both addresses are in the ROM ($81:D8B2, $B7:90E4). [verified]
 - v1.1 did not change the save structure.
   A save made in v1.0 was loaded in v1.1 and play continued. [verified]
```

## 10. Free space used by v1.1 and banks changed

```text
 - Do not assume "a run of 0xFF = free space".
   Check that it is 0xFF in the original ROM too, and that no data right before it uses 0xFFFF as an end marker.
   (Kakusei-hen v1.1 missed this and caused a bug where the spaceship flies off the map.)
 - Free space newly used by v1.1 [verified]
     $B7:FA00-$B7:FA77   glyph block lookup code and tables
     $81:EF00-$81:FEFF   glyph block 0
     $84:EE00-$84:FDFF   glyph block 1
     $86:E000-$86:EBFF   glyph block 2 (only 3KB used)
     $86:EC00-$86:EC7F, $86:ED00-$86:ED7F   v1.2's 「펴」, 「플」, 「딩」 and 「렉」 (0xD60-0xD63, upper and lower halves)
     $B7:FB00-$B7:FB6B   v1.2's technique/event list mark routines (section 6)
   Dialogue and text were refilled only within each bank's original string area.
 - Banks whose bytes changed between the v1.0 and v1.1 ROMs [verified]
     80 menu strings, checksum     81 save dialogue, battle shout pointers, glyph block 0
     83 font (slots out of use)    84 technique names, glyph block 1    86 glyph block 2
     87 place names                8E dialogue              98 mini-games
     9D 9E A8 A9 AB B2 B4 B5 dialogue (A9 also choices)     9F ally comments
     AD event list, pointer 204    AE enemy names           B1 battle dialogue
     B7 hooks, new code, title graphics, ending credits     BF font (slots out of use)
 - ROM header checksum: file 0x7FDC-0x7FDF (2-byte complement + 2-byte checksum)
   Recomputed after changing the ROM. (tools/fixsum.py)
```

## 11. Password carried over to Kakusei-hen (fixed in v1.2)

```text
 - The v1.2 ending shows the fixed password 「손오공은사이어인」 ("Son Goku is a Saiyan") instead of the data password (tools/endpw1.py). [verified]
   Entering these eight characters in Kakusei-hen v1.3 (CRC32 B9F14962) passes and goes to the name screen.
   No name is carried over, so it is Kakusei-hen's default name 「엑소버드」 (Mesen 2). [verified]
   · $81:D169-$81:D1C4 (pair swapping $81:D169-$81:D19B, moving five characters at a time $81:D19C-$81:D1C4) was replaced
     with a copy loop (LDX #0 / LDA $81:D17D,X / BEQ / STA $0A00,X / INX INX / BRA, TXY, BRL $81:D1C5)
     and the string. The leftover bytes are 0xFF.
   · String ($81:D17D): 000A, 82C5×5, 8182 81A7 8106 81AF 8221 81C1 81A2 81C2, 000A 000A, 0000
     The window is 18 cells (144px) × 14 lines. Small characters are 8px, so the eight characters (64px) follow five spaces (40px)
     to be centred, on the second line. The original code at $81:D1C5 appends a line break and " TO BE CONTINUED" on the fifth line.
   · The data bytes and sum at $1F00 are still produced but not shown on screen.
 - What follows is the format of the original data password and results checked with an experimental ROM
   built from v1.2 without tools/endpw1.py.

 - The last screen of the Totsugeki-hen ending (TO BE CONTINUED) shows a 50-kana password (10 groups of 5).
   Kakusei-hen takes it at new game → 「突激編のつづき」 (「암호」 in the Korean version).
   The entry screen is the hiragana board; X switches to the katakana board. [verified]
 - The password string is in WRAM $7E:0A00. It uses small-character codes (kana codes with 0x8000 set),
   with 0x82C5 (space) every 5 characters and 0x000A and 「TO BE CONTINUED」 at the end. [verified]
 - Two characters make one byte. The byte value is the index in the pair table $B7:F09F
   (256 pairs × 2 codes, unchanged from the Japanese ROM). 25 pairs = 23 bytes + 2-byte sum. [verified]
   Bytes 7-16 are the hero's name (five 16-bit character codes).
   Names are stored for 5 characters (hero, rival, henchman, villain, adviser) from WRAM $7E:0B01, 13 bytes apart. [verified]
 - The debug menu DATA → ENDING password (same codes in the Japanese ROM, v1.1 and v1.2) [verified]
     あにあにあ にあにあに あにあにぺ とあにぺと あにぺとあ
     にぺとあに ぺとあにぺ とのれあに リナノレあ にばタあに
   Korean screen:  가녕가녕가 녕가녕가녕 가녕가녕성 너가녕성너 가녕성너가
                   녕성너가녕 성너가녕성 너누똑가녕 잘건와전가 녕브알가녕
   The address of the routine that builds the password was not looked for.
 - Characters on the Korean screen [verified]
   v1.0 drew 8px Hangul into the kana slots (0x100-0x166, 0x180-0x1E6, 0x200-0x261),
   so the Korean version shows the password in Hangul. The mapping read from the pixels is in tables/password.tsv.
   Up to v1.1, five different kana had the same or nearly the same shape as another character.
     へ(0x12C) = つ(0x121) 「나」     も(0x142) = ら(0x146) 「등」   (pixel-identical)
     を(0x14C), ん(0x14D) ≈ わ(0x14B) 「러」     ル(0x1C8) ≈ ォ(0x1E2) 「지」
   The character table (tables/kr-v1.0.txt) names these five slots 다, 동, 레, 렉 and 저,
   so v1.2 redrew the five slots as those characters with tools/pwglyph1.py.
   8px wide, 1px strokes and no shadow plane, the same style as the neighbouring glyphs, with shapes modelled on Galmuri11.
   The name entry character board (file 0x7005, a 16-bit string written by v1.0) uses the same codes,
   so five cells change to 다, 동, 레, 렉 and 저, and the 160-cell board no longer has duplicate shapes.
 - Besides these five, four more slots have pixels different from their name in the character table.
     0x120 깨→께, 0x1A4 언→건, 0x246 티→띠, 0x248 펴→떠
   v1.2 corrected tables/kr-v1.0.txt to match the v1.0 pixels (all nine slots: 12C 나, 142 등, 14C 러, 14D 러,
   1C8 지, 120 께, 1A4 건, 246 띠, 248 떠). tables/kr-v1.2-glyphs.txt overlays the new names of the five redrawn slots
   (table() in tools/kr1.py). The comparison dumps (*-v1.0.tsv) have no lines using these nine codes, so they do not change.
   v1.1 used 0x248 in dialogue 0x5D5 「펴‥평범한」 and 0x101B 「살펴봐」, where it showed as 「떠」;
   v1.2 draws 「펴」 as a new 16px glyph (0xD60) (both lines stay within the window width).
   「디렉터」 (director) in the ending credits used 0x14D and showed as 「디러터」 in v1.1. v1.2 uses a 16px 「렉」 (0xD63) (section 4).
 - Build checks (tools/pwglyph1.py; the build stops if one fails)
   · the five slots match the prepared drawings, and the pixels of the other 158 password characters are unchanged
   · all 163 password characters have distinct shapes
   · the character table names every password character by its on-screen character (or the Japanese kana)
   · no two codes with different names in the character table draw the same picture (plane 0 minus the plane 1 shadow).
     0x280 「0」 and 0x2A8 「O」 are the same picture since the Japanese ROM and are an exception
   · no two cells of the name entry board have the same shape
 - Checked against Kakusei-hen v1.3 (Mesen 2, the experimental ROM above) [verified]
   Finding and pressing the same Hangul from the debug ENDING screen on the Kakusei-hen v1.3 entry board
   passes and goes to the name screen. Passwords made just before the ending with the hero's name ($7E:0B01)
   changed to 다동레렉저 (0x12C 0x142 0x14C 0x14D 0x1C8) and to 녕노제똑고
   (so the redrawn characters appear in the password) also passed, and the name appeared unchanged on the Kakusei-hen name screen.
   The Kakusei-hen side of the fix (entry board, pair table, name conversion table $83:AEB0) is in the Kakusei-hen v1.3 bundle.
 - Between the Japanese versions: entering the debug ENDING password into Japanese Kakusei-hen with hiragana ぺ gives a wrong password.
   The Kakusei-hen work confirmed this is because the same slot of the Kakusei-hen pair table is katakana ペ.
 - Totsugeki-hen also has kana entry screen code: $80:99D6 (called from $82:9D7C, the branch taken when $0216 = 1).
   Changing file 0x61-0x66 to EA EA 22 D6 99 80 calls it right after boot, and the board opens half broken.
   No way to open it in normal play was found. [verified]
```

## 12. Not checked, and known limits

```text
 - There is no record of running on an actual Super Famicom or a flash cartridge.
   The emulator results are in section 8.
 - Window info first byte FE (347 lines): by the code it is a 128px window that skips the face drawing routine, but the screen was not looked at.
 - Kakusei-hen data password: not checked with the password from an ending reached by playing through (checked with the debug ENDING and name-only changes).
   The v1.2 ending only shows the fixed password, so this path remains for compatibility on the Kakusei-hen side.
 - $80:9CFA and $80:9DA7 in the header comment of tools/lz.py are Kakusei-hen addresses (section 5). The file is left as released.
 - WRAM $4D is also used briefly by the graphics loading routines. Watching reads of the window info table records dialogue more accurately.
 - Five of the new glyph blocks, 3-7 (320 glyphs), are entirely empty. They can be used as is for more glyphs.
 - 16px glyphs that differ by a single pixel [verified]: syllables with a horizontal vowel (ㅗ, ㅜ, ㅡ) and a final consonant
   fit a 3-row initial, the vertical stroke, the bar, a gap and the final (ㄹ takes 5 rows) into 11 rows (rows 3-13),
   so the vertical stroke of ㅗ and ㅜ is 1px and the initials ㄷ and ㅁ differ only by 1px on the right.
   46 pairs of glyphs used in the text differ by one pixel (돌/들/둘/물/몰/틀, 올/울/을, 송/승, 중/증, 볼/불/블 and others).
   Redrawing them with Galmuri11 at 12px gives almost the same shapes, and 41 pairs still differ by 1px.
   Raising the initial by 1px and lengthening the vertical stroke to 2px separates 43 pairs, but those 200 glyphs
   become 1px taller than their neighbours, so v1.2 keeps the v1.0 glyphs.
```

## 13. Tools used

```text
 - Python 3.9.6, Pillow 11.3.0, numpy 2.0.2 (macOS)
   Running tools/build.sh with only this bundle and the Japanese ROM was confirmed to give CRC32 A939C4F8.
 - Mesen 2.1.1 (Lua scripts, --testrunner)
 - libretro cores: bsnes, bsnes-hd beta, snes9x, snes9x2010, Beetle Supafaust, Mesen-S (compat/)
 - New glyph drawing: Galmuri11 2.404 (tools/fonts/)
 - Title font: BM YeongSung (macOS system font, TITLE_FONT in tools/title.py)
 - Disassembly: tools/dis65816.py (a home-made 65c816 disassembler)
```
