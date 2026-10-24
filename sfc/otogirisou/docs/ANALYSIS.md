# Otogirisou (弟切草) ROM analysis (Korean v1.0 / v1.1 / v1.2 / v1.3)

English | [한국어](ANALYSIS.ko.md)

```text
A record for anyone who analyses this ROM again or continues fixing the Korean version.
Build instructions are in tools/README.txt; the work process and figures are in the "ROM analysis notes" on the page below.
 https://perfectacle.github.io/games/kr-patches/sfc/otogirisou/#making

Markers
 [verified]  checked directly by reading ROM bytes, running the included tools, or in an emulator (Mesen 2)
 [inferred]  guessed from reading code, or only circumstantial. Not checked directly.
 A line without a marker follows the marker of the item right above it.

Address notation
 $XX:YYYY   SFC address (bank:address)
 file 0xN   offset in the headerless ROM file
 LoROM conversion: file offset = (bank & 0x7F) × 0x8000 + (address & 0x7FFF)
   e.g. $15:E401 = file 0xAE401, $20:8000 = file 0x100000, $00:F4AC = file 0x74AC
```

## 1. ROM

```text
■ Files [verified]
  ROM                           size        CRC32
  Japanese original (no header) 1MB         8E4BEFD0  (MD5 AE1E9C92D0B7E6DBA6C6007D99C9C3F4)
  v1.0 (Japanese + v1.0 IPS)    2MB         C70A8E66
  v1.1                          2MB         27EE014E  (MD5 F45317CFAAAB68CCA5D8984AF8452535)
  v1.2                          2MB         2C31A0B2  (MD5 CD48C59B3B80D6C9E3C648E8BDD5A4E0)
  v1.3                          2MB         3258FDFC  (MD5 84A82E0A88BF2EC9FAAA243C823D90E9)

 - Rebuilding v1.2 with the included tools gives the same CRC32.

■ Header $00:FFC0 (file 0x7FC0) [verified]
  offset   value              meaning
  0x7FC0   "OTOGIRISOU"       game title (21 bytes, rest is spaces)
  0x7FD5   20                 LoROM
  0x7FD6   02                 ROM + SRAM + battery
  0x7FD7   0A → 0B            ROM size. 0A (1MB) in the Japanese ROM and v1.0, 0B (2MB) from v1.1
  0x7FD8   03                 SRAM 8KB
  0x7FDC   2-byte complement + 2-byte checksum (recomputed with tools/fixsum.py)

 - v1.0 grew the ROM to 2MB without fixing the size byte. v1.1 set it to 0B. (tools/fixes.py)

■ ROM map (one bank = 32KB) [verified: comparing the Japanese, v1.0 and v1.2 ROMs]
  bank          Japanese              v1.0                         v1.1 / v1.2
  $00-$14       program, graphics etc. read routine and part of    hook points and glue code (section 5)
                                      the font table changed
  $15:E401-     Huffman script starts most of the script area      v1.1/v1.2 code and tables in the same area
                                      zeroed
  $16-$1E       Huffman script                                     (section 7 "Space used")
  $1F           script font           Korean font                  v1.1 font (rewritten)
  $20-$35       (none)                v1.0 script $20:8000-$35:9AD2  v1.1 script $20:8000-$35:AF66
  $36-$3F       (none)                0                            0

 - v1.0 emptied most of the Japanese script area from $15:E401 with zeros. The zero run is between $15:E530-$1F:95A8.
   Inside it, only $16:806A-$16:AE4E was filled by v1.0 with bytes different from the Japanese ROM: graphics and code v1.0 added. (section 5 "v1.0 hooks")
```

## 2. Memory

```text
■ Sizes [verified: header, hardware specs]
  ROM 1MB (Japanese) / 2MB (Korean), WRAM 128KB, SRAM 8KB, VRAM 64KB

■ WRAM used by the game (work notes, checked with Mesen 2) [verified]
  address           meaning
  $0A25             raw pad 1 value (16-bit). high: B Y Select Start Up Down Left Right, low: A X L R
  $CC               game buttons: bit7 = A or L, bit6 = B or Y, bit0-5 = Select, Start, D-pad
  $CD               bit7 = X, bit6 = Y
  $52-$54, $55      script position (24-bit) + bit number within the byte in the Japanese ROM
  $5D, $5F-         state and contents of the inserted-symbol buffer (hero name, automatic input-wait code)
  $195B             copy of the text position
  $1972             copy of the layout read-ahead position
  $1989             position copy of task 1 (sound command read-ahead). $1989-$198C (section 5)
  $19A0             copy of the scene read-ahead position
  $1A55             current scene (background) number
  $1A93/$1A95       input wait ($FE = waiting)
  $1A97/$1A99       pause frame count
  $1AF4, $1B08, $1AE0   scene being prepared by read-ahead, its stage, ready (2)
  $1BBD             しおり (bookmark) stage (0 → 4 → 6 → 7)
  $1BBF             backlog page count
  $1BC1             number of choices made
  $1BC3             playthrough count
  $1BC5             page count
  $1BEF + variable  script variables (1 byte each, 0x1A4 of them). low 3 bits = value, high 5 bits = choices picked
  $0C99-            CGRAM copy. $0C9B = text colour 1
  $7F:0010-         text layer (BG3, 2bpp) bitmap, 32×32 tiles
 - Write-watching while playing 6,000 frames showed the game uses $7F:0000-$B6FF and $7F:FF00- in bank $7F. [verified]
   v1.2 uses the space in between.
 - Rechecked with the final v1.2 [verified: Mesen 2 write watch, 51 runs × 12,000 frames]
   saves: 30 chapter starts, 18 points three lines before an ending (bookmark stage 7 so hidden choices show) + 3 new games for scenarios 0/1/2
   input: at chapter starts, Select, D-pad, X, Y and A mixed to move between the flowchart and menus; elsewhere A mashing
   watched ranges: $7F:C000-$7F:D8FF, $7F:FFE0-$7F:FFEF, $7E:1FF2-$7E:1FF3 (all mirror banks included)
   result: the only writes outside the patch code (banks $18 $1A $1E, $00:FAB0-$00:FB07) came from the loop ($00:8030)
         that clears $0000-$1FFF at power-on. 0 writes addressed through the WRAM port $2181-$2183. No execution of
         $00:0000-$00:08FF in any of the 51 runs
   A scene the watch did not cover may still write to those ranges.

■ WRAM used by the patch [verified: asm sources]
  address               source            meaning
  $7F:C000-$7F:C7FF     qol.asm           menu script buffer A
  $7F:C800-             qol.asm           menu script buffer B
  $7F:CF00-$7F:CFEF     qol.asm           chapter list working values
  $7F:CF40              qol.asm           saved engine values the menu changes ($1BB1-$1BB8, $1BBF, $1BC1, $1BC5, choice variables)
  $7F:CF50              qol.asm           start of the page where the menu was opened (24-bit)
  $7F:CF54              qol.asm           chosen chapter (1-31) or 0 = go back
  $7F:CF60-$7F:CF7F     qol.asm           bitmap of the looping sounds now playing
  $7F:CF80, $7F:CF88    qol.asm           buffers for music and scene codes inserted before a jump
  $7F:CFF0              qol.asm           flag: menu script running
  $7F:D000-$7F:D4FF     flow.asm          boxes drawn on the flowchart (8 bytes × 160)
  $7F:D600-             flow.asm          node → box number
  $7F:D800-$7F:D8FF     flow.asm          flowchart working values
  $7F:FFE0              wordwrap.asm      flag: line break before the next character (magic $5A3C)
  $7F:FFE2-$7F:FFEF     savecompat.asm    temporary values for save conversion
  $7E:1FF2              qol.asm           text colour saved before rewinding

 - WRAM contents are undefined at power-on. Flags are tested against 16-bit magic values, not 0/1.

■ SRAM ($70:0000-$70:1FFF, 8KB) [verified]
  $70:0000-$70:001F     header. Overwriting it makes the game erase the slots.
  $70:0020 + n × 0x5E3  slots 0-3 (0 = working copy during play). Up to 0x17AB
  $70:1800-$70:184F     v1.2 records (cleared to 0 at power-on if the marker is missing)
 - The save format is in section 6.
```

## 3. Script

```text
■ Japanese ROM: Huffman bit stream [verified]
 - The whole script is one bit stream. Base $15:E401 (file 0xAE401)
 - Bits within a byte are read from the lowest bit.
 - Tree: bit 1 → $02:C1E1 (file 0x141E1), bit 0 → $02:CD4F (file 0x14D4F). 16 bits per entry
   Root node offset 0x0B6C. If the top bit of a value is 1 it is a leaf (symbol = value & 0x1FFF), otherwise (value & 0x1FFF) × 2 is the next node
 - Symbols 0x000-0xFFF = characters (font codes), 0x1000-0x1046 = control codes
 - Jump argument = 24-bit bit offset from the base, stored as plain 24 bits inside the bit stream.
   After reading, $02:C0A1 converts it to a LoROM address.
 - Size: about 2.46 million bits (about 300,000 bytes)

 e.g. the first sentence of the script, 「夏の夕暮。」 (decoded with tools/script.py)
   after four leading control codes {3A:15,39}{32:16,1}{22:0,7}{22:1,1}, from bit 126 (bit6 of file 0xAE410)
   夏 1000100000000010 (16)   の 01001 (5)   夕 1111101010101000 (16)
   暮 00110111101111 (14)     。 10010 (5)    {00} 11001 (5)      → 6 symbols, 61 bits
   「の」 = 0B6C -0-> 0B68 -1-> 0B62 -0-> 0B54 -0-> 0B38 -1-> 862E (leaf, symbol 0x62E)

■ v1.0 and later: 2 bytes per symbol [verified]
 - One symbol = 2 bytes big-endian (high byte first). Jump argument = 3-byte little-endian LoROM address
 - Starts at $20:8000. Past the end of a bank ($XX:FFFF) it continues at $8000 of the next bank.
 - Read routines changed by v1.0: $02:C156 (2-byte read instead of Huffman), $02:C087, $02:C106 (bit offset conversion skipped)
 e.g. the same first sentence in v1.0, 「여름의 해질녘.」 (file 0x100018)
   01 D8 여 / 04 85 름 / 01 CF 의 / 04 DF space / 04 95 해 / 01 BA 질 / 01 B9 녘 / 05 C7 . / 10 00 {00}
   → 9 symbols, 18 bytes. The whole v1.0 script is 694,995 bytes
 e.g. the first jump of the first choice: Japanese @b0003109 (bit 3109), v1.0 @208349 ($20:8349)

■ Script start [verified]
 - $02:A569: picks scenario 0/1/2 from the playthrough count ($700024 + slot × 0x5E3) and a random number. 0 and 1 on the first playthrough, 2 can also appear from the second
 - Start address table $02:A627 (file 0x12627, 3 bytes × 3)
   Japanese 08 20 AF | 68 F7 E4 | C0 4B C5 (bit offsets)
   v1.0     00 80 20 | A9 D6 2E | C0 4B C5 ← entry 2 is still the Japanese value, so the game hangs from the second playthrough
   v1.2     00 80 20 | 95 D3 2E | A8 EA 25
 - The Japanese script blocks are in the order 0 → 2 → 1.

■ Control codes [verified: branch table, argument table and use counts in the script]
 - Branch table $00:F390 (2 bytes × 0x47), argument table $00:F41E (2 bytes × 0x47). Right after them is the font group table $00:F4AC
 - Argument table value: low byte = number of arguments, high byte = bit mask of the arguments that are 24-bit jump arguments
   Argument count 0x63 is a choice. The handler ($00:9DAE) reads 3 symbols and then (first symbol & 7) - 1 jump arguments.
   The skip routine ($00:A99F) reads only 2 symbols, so a parser must follow the handler.
   A jump argument of 0 is a disabled option.

  code          action
  {00}          line break (no input wait)
  {03:@}        jump
  {04:v,n,@}    jump if $1BEF[v] & 0xFF == n (note that it compares the high bits too)
  {05:v,n,@}    jump if not equal
  {13}          skip the next automatic input wait once
  {16}          input wait ($A7F8: $1A93 = $FE)
  {17:n}        pause n × 6 frames ($A7FF)
  {19} {1A}     choice. arguments: (option count + 1) | mask A << 3 | mask B << 8, mask C, variable number, one jump per option
  {1C}          end of a choice option text
  {1D}          end-of-ending marker. Its branch table target is $A99E, which does nothing; the new-playthrough code ($01:F792) looks for this code directly
  {1E:x} {1F:y} text position (not used in the script)
  {20}          hero name
  {22:v,n}      $1BEF[v] low 3 bits = n ($A889)
  {25} {26}     clear the text buffer and go to the next page ($A7BB)
  {27:n}        clear the screen
  {2E}-{33} {36} {37}  scene (background). Puts the scene number in $1A55 ($AAC9). First argument of the 2-argument codes = fade speed
  {39:x}        play sound    {3A:f,x} fade in    {3B:x} stop    {3C:f,x} fade out    {3D:x} play and wait
  {44:n}        menu action added by v1.2 (unused in the original script)

 - Codes the script does not use: 01 02 06-08 0A-12 14 15 18 1B 1E 1F 23 24 26 28 29 2D 31 44
 - {23} ($00:E13F) / {24} ($00:E1DD): a debug feature that picks a scene number and goes there [verified: code and Mesen 2]
   {23}: reads a table with the number at $7F:FFF0 × 14, puts symbols and {24} in the $5F buffer, saves state in $1A03 etc., $1BB1 = 3
   {24}: $1BAD = $FE. From the next frame, $00:E1E4 in the main loop changes the number with the D-pad (up/down ±1, left/right ±20); A/B leaves
   The addresses pointing to the count table and the scene table were cleared to 0, so it reads $00:0000. 0 uses in the Japanese, v1.0 and v1.1 scripts
 - Printing 「 」 』 . ？ ！ makes the engine wait for input by itself. ($00:AC15 / $00:AC52, character list $02:A97C) [verified]
   Clearing with {25} without a wait moves on without A; a {16} right after an automatic wait needs two presses.

■ Script text format (tools/dump.py, tables/script*.txt) [verified]
 - A #address line = jump target. Characters come from the table, control codes are {XX:args}, jump arguments are @address
 - Splitting the Japanese bit stream by the same rules (before jump targets, after {25}) gives the same line numbers as v1.0. All 6,730 lines have the same control code sequence.
 - Reassembling the extracted script without changes gives v1.0 byte for byte. (tools/assemble.py)
```

## 4. Font

```text
■ Format [verified: tools/font.py, decoder $00:A57F]
 - Variable-size 1bpp glyphs in bank $1F. Group table $00:F4AC (file 0x74AC)
 - One group entry is 5 bytes
   +0 (16-bit)  low 12 bits = glyph count, high 4 bits = width
   +2 (16-bit)  start address within bank $1F
   +4           height << 2
   e.g. the first v1.2 entry 05 92 00 80 2C = 517 glyphs, width 9, $1F:8000, height 11
 - The n-th glyph of a group is n × width × height bits after the start address. One row = width bits, the leftmost pixel is the highest bit of the row
 - The decoder reads 3 bytes per row, so 2 spare bytes follow the group data. It cannot cross into bank $20.
 - Glyphs are bottom-aligned. (y_top = y + $18D7 - height)
 - When a glyph is drawn, $00:A61C ORs it into the 2bpp tiles in WRAM $7F:0010-. plane0 = colour 1 (text), plane1 = colour 2 (shadow)

■ Group table limits [verified]
 - Right after the table, $00:F5CE is the list of characters that may hang at the end of a line (codes 1478 1479 1494 1458 1455 1496 1498 1501 1503, ended by $FFFF).
   So the table can hold at most 58 entries (290 bytes). The Japanese ROM and v1.0 both use all 58.
 - The engine does not look for an end marker in the group table. [verified: $00:A4F4-$00:A51C]
   It adds up the glyph counts (low 12 bits) entry by entry from the first and stops at the entry the code falls into.
   A code beyond the last group reads the $00:F5CE data after the table as group entries.
   tools/font.py stops at an entry whose glyph count or width is 0.
 - v1.1 turned 168 codes nobody references (1247 and later, not Hangul) into blank glyphs of the same size as their neighbours and merged them into 45 entries.
   "Referenced" was judged from the dialogue, the name entry table ($02:A990-$02:B03F) and the two character lists ($02:A97C, $00:F5CE).
 - 75 new glyphs (codes 1614-1688) were added as 3 entries (9×11: 33, 10×11: 20, 11×11: 22), making 48 entries. 10 remain free.
 - v1.3: codes 1689-2773 (51 compatibility jamo + the 1,034 KS X 1001 syllables the font lacks, Galmuri11 11×11) were added as one 49th entry.
   The data does not fit bank $1F, so it is at $36:8000, and the decoder's LDA #$1F / STA $16 at $00:A56C became JSL NeBank,
   which picks bank $36 for entries from 48 on. The width table is filled for the new codes too (11).
 - Glyph width table $1E:F000 (1 byte per code, 0x800 entries): for v1.1 word wrapping. Characters that hang at the line end have width 0
 - The name entry screen uses the same codes as the dialogue. The v1.0 code-to-character mapping was not changed.

■ Character tables [verified]
 - tables/kr-v1.0.tbl: v1.0 glyphs drawn and read 9 times with macOS Vision, majority vote, a corner-pixel rule for ㅁ/ㅇ, 30 characters fixed by context review
   The ㅗ/ㅜ/ㅡ stems are 1 pixel, so misreads may remain in rarely used characters. [inferred]
 - tables/jp.tbl: for comparison. Contains some misreads.
 - Code 1247 = space, 1248 = non-breaking space (before the honorific after a name), 1478 comma, 1479 full stop, 1482 exclamation mark (wide glyphs including the trailing gap)
```

## 5. Engine and hook points

```text
■ Main loop and input [verified: work notes]
 - $00:8570 (NMI side): $4218-$421F → $0A25. $00:8B9A builds $CC/$CD and $00:8BD6 keeps only newly pressed buttons.
   $00:8BF3: key repeat (first 0x14 frames, then 6 frames)
 - Select and R are not used anywhere. Start pauses
 - Main loop $00:9951: input, layout, screen, input wait ($00:9CE7), script reading ($00:999A)
   The script is read only when $1A95 | $1A99 | $1A9D | $1BAB | $18C7 are all 0.
 - X during an input wait with 2 or more pages rewinds ($01:F3BB). Y goes forward again

■ Four copies of the script position, and tasks [verified]
 - Position copies $195B $1972 $1989 $19A0. $00:9BA7 reloads $52 from $195B, so changing the position means writing all four.
 - $00:8D50 starts a task (A = entry point, X = bank, Y = number). $09F0+number = running, $00:8D99 = the task ends itself
 - Task 0 = layout read-ahead ($00:AB5A, D = $0180). Control codes below $28 are executed here as well.
   So new control codes must be $28 or above, and a jump hook must act only when D = 0 (the main text).
 - Task 2 = scene read-ahead ($00:AE47, D = $0280). Reads from $19A0, preloads scene graphics, and stops at choices and conditional jumps.
   After a jump code runs, $00:9A5A passes it $52 and restarts it.
 - A scene code waits until that scene is ready in $1AF4 ($19D0 = $FF).
   Changing the position without a jump or choice requires calling $00:9A5A. Without it the game hangs forever on a black screen.
 - Task 1 = sound command read-ahead (entry point $00:CB99 from $00:9B53, Y = 1). Position $1989-$198C [verified]
   When reading ahead hits a sound code ({39} {3D} {45} etc.), $00:CCAC sends the list from the $01:8007 table to the sound command buffer
   ($10A5/$10A6, lock $10A3). At {19} {1A} {04} {05} {1D} {23} {24} {43} {44} it leaves the position in $1989-$198C
   and ends; the next time it starts, $00:CC96 resumes reading from there.
   Reading it as a task that prepares sounds in advance is an inference. [inferred]

■ Choices [verified]
 - $00:A13B: if the option is picked for the first time $1BC1++, position to after the choice, backlog cleared ($1BBF = 0), autosave (JSL $02:A795)
 - Hidden options: when bookmark stage bit0/1/2 is set, masks A/B/C are lifted. The stage is set from the ending record variables at a new playthrough ($01:F792).
 - At most 5 options are visible at once. Putting in 6 broke the screen.
 - The chapter list appears over the current scene background like the original choices. The eyeball-like picture visible above the menu is not a sprite but
   the scene background BG2. There are 0 OAM entries at that time, and changing $0A0E shows it only while BG2 is on. [verified]
 - Continuing in the 1C lane (script line 5904) from an old menujump save (bookmark stage 0) masks every option of choice {1A:1548,0,344},
   the position becomes 0 and the game runs away into $00:0000. v1.1 does the same; normal play cannot reach that state. [verified]
 - 382 choices ({19} at 98 places + {1A} at 284) use 380 variables. The variables shared by two choices are 259 and 298

■ Line breaks and the text window [verified]
 - Left margin x = 12, line break limit x = 242, first line y = 16, line spacing 23, letter spacing 2 → 9 lines per screen. From the 10th line on, text is cut off.
 - $00:A777: after drawing a glyph, breaks the line if x + width exceeds the limit. Characters in $00:F5CE may hang at the line end
 - Printing a character that sets an input wait, such as a full stop, makes the engine insert a wait code into the $5F buffer, so $5D is not 0.
   A check that uses $5D to tell whether a name is being printed must only be done on a space.

■ Screen [verified]
 - Text layer BG3, 2bpp, mode 1. Bitmap offset = tile row × 512 + tile column × 16 + (y & 7) × 2, bit7 is the leftmost pixel
 - While $19CE is set, $00:A426 sends rows $19C4-$19C6 and columns $19C8-$19CA to VRAM.
 - Main screen layers $0A0E (normally $17), colour math $0A13. Setting $B6 bit6 applies them at the next NMI
 - Text palette colour 1 = $0C9B, colour 2 = $0C63, colour 3 = $1FFF. CGRAM copy $0C99; setting $B5 bit3 makes the NMI upload it
 - Drawing one glyph with the game font: $1A7D = code, $1A7F/$1A81 = coordinates, JSL $00:9595
 - While the sound driver runs, the reset code ($00:8EA0) hangs in its IPL upload. That is why a soft reset approach was not used.

■ All hook points [verified: org lines in the asm sources, Japanese and v1.2 ROM bytes, asar symbols]
  address    original bytes (JP)    v1.2           new code           source           does
  $00:A777   C2 30 18 AD 83 1A      22 00 80 1E…   WordWrap $1E:8000  wordwrap.asm     word-level line breaks
  $02:A54F   A5 13 9F AF 05 70      22 00 80 18…   MarkNew $18:8000   savecompat.asm   v1.1 marker in a new slot
  $02:A83B   AD 5D 00 8F B1 05      22 13 80 18…   MarkSave $18:8013  savecompat.asm   marker on autosave
  $02:A6D3   AF AC 05 70            22 22 80 18    LoadSave $18:8022  savecompat.asm   convert old save positions
  $00:9CF9   A5 CC 29 00 80         22 45 84 1A EA SelCheck $1A:8445  qol.asm          Select during input wait → flowchart
  $02:A79C   AD BF 1B 0A 0A         22 B7 83 1A EA AutoSave $1A:83B7  qol.asm          record chapters read, skip autosave inside the menu
  $02:C120   A5 10 85 52            5C D2 83 1A    JumpHook $1A:83D2  qol.asm          restore menu values on a jump
  $02:A56F   C2 30 29 FF 00         22 97 82 1A EA LapHook $1A:8297   qol.asm          new playthrough = ending record
  $02:A4D1   29 FF 00 85 30         22 65 82 1A EA NewSlot $1A:8265   qol.asm          reset records for a new slot
  $01:F3BB   C2 30 AD BF 1B         22 4C 80 1A EA BacklogIn $1A:804C qol.asm          yellow text when entering rewind
  $01:F421   A9 C0 00 8D 2D 0A      22 5B 80 1A EA EA  BacklogOut $1A:805B  qol.asm  restore colour when leaving rewind
  $02:B955   20 6B B9 20 89 B9 …    22 87 80 1A EA… ShioriSlot $1A:8087 qol.asm         last chapter title on the bookmark screen
  $00:CE3F   22 00 80 02            22 14 80 1A    BootLogo $1A:8014  qol.asm          reset SRAM records at power-on
  branch table $00:F390 + code × 2
   {44}      A955 → FAB0 (Cmd44Tramp → Cmd44 $1A:848C), argument table 0000 → 0001     menu action
   {39}-{3D} A8F1 A8FE A8F8 A908 A926 → FAC6 FAD1 FADF FAE9 FAF7               record looping sounds, then the original handler
 - $00:FAB0-$00:FB07: glue code that must be called from within bank $00 (originally filled with FF)
 - asar caveat: a relative branch out of range fails the build. Those were changed to the opposite condition + JMP.

■ v1.0 hooks [verified: comparing the Japanese and v1.0 ROMs, Mesen 2]
 - v1.0 replaced 7 places in the Japanese code with JML. v1.1 and v1.2 leave them as they are.
  address    Japanese         v1.0
  $00:B472   AB 4C AB 86      5C F0 A5 16   → $16:A5F0
  $00:C436   AD D0 19 D0      5C 0B E5 15   → $15:E50B
  $00:C4EC   AD D0 19 D0      5C 99 E4 15   → $15:E499 (screen update)
  $00:D585   C2 30 A9 01      5C 00 92 16   → $16:9200
  $02:B521   22 3B 93 00      5C 20 A6 16   → $16:A620
  $02:B54B   C2 30 A9 5C      5C 3B AE 16   → $16:AE3B
  $02:BCF9   C2 30 9C 9E      5C 4F A6 16   → $16:A64F
 - When hook code writes 1-3 to $0100, the screen update hook ($15:E499) DMAs graphics to VRAM.
   1 = $16:8000 0x1200 bytes → VRAM $5700 (right after power-on)
   2 = $16:A67B 0x580 bytes → VRAM $4840 (before the bookmark screen)
   3 = $16:AC7B 0x1C0 bytes → VRAM $4330 (before the name entry screen)
 - The area around $15:E401-$15:E52A is v1.0 code too.

■ Name entry screen (v1.3) [verified: MesenCE]
 - Module $02:B040-$02:B6FF. Focus $1AA1 (0 = left menu, nonzero = grid, $FFFF = done), menu choice $1AAB (0 letters, 1 digits, 2 Hangul),
   Hangul page $1AAD (0-9), page number $1AA7 = menu or 2 + page, redraw flag $1AA9
 - Page data: the pointer tables $02:B18E (drawing) and $02:B849 (input) point to the same place. 50 codes and $FFFF per page, 0 = empty.
   The grid is that code string printed by the dialogue engine (spacing $10, left $90, margin $E6 -> 5 columns)
 - Grid cursor $1A9F (column) / $1AA0 (row). Row $0A is the command row: 1 delete, 2 back to the menu, 3 space (code 0), 4 END
 - Name $1BC9 (6 codes), count $1AA3 (at most 6). $02:B334 appends a code and $02:B357 draws it in the name box (x = 13 x n + 31, y = 40)
 - The Japanese voicing marks are still handled ($02:AFE4/$AFE6, tables $02:AEC4 and $02:AF90).
 - The arrows of 「한글 ◀ 1 ▶」 are tiles of the BG1 book picture (run-length tile map of the Japanese ROM near $07:E4D0); the digit is printed at $02:B5C5.
 - v1.3 (asm/nameentry.asm, tools/namefont.py)
   · Hangul page 1 ($02:AAB4) is now the 2-set jamo page (consonant block on top, vowel block below, each with its Shift row above it).
   · $02:B114 and $02:B12F: left/right on the Hangul button no longer turn pages (right enters the grid). $02:B5C5 page number NOP, ◀▶ tiles become button face
   · The menu order is 한글, 영문자, 숫자. The menu index is the page number, so entries 0 and 2 of the page pointer tables
     $02:B18E and $02:B849 swap, and the first page drawn ($02:B5CC) is the jamo page. $02:B585-$02:B5B8 set x, y and the string
     ($02:A9CA 영문자, $A9D4 숫자, $A9DE 한글) of each button label, so their order and x change. x $44 for 한글 is where the first
     letter of 숫자 (which starts with a blank) lands.
   · The grid cursor skips empty cells on every page ($02:B1D8, $B1ED, $B20A, $B220 → NeUp, NeDown, NeRight, NeLeft). Up/down
     go to the next cell in the same column, or if the column has none, the nearest cell of the next row that has one (left on
     a tie). Left with no cell to the left goes to the menu. Entering the grid ($02:B15D) moves the cursor to the top left if
     its cell is empty on that page.
   · $02:B282: A on the Hangul page -> NeA. The composing states (initial, medial, final for each jamo typed) are stacked in WRAM $7F:E000,
     and the syllable being composed is always the last code of the name. Every write goes through $02:B334 (trampoline $02:D8BD);
     replacing the last character means decrementing $1AA3 and appending again.
   · $02:B23F: delete -> NeDel. While composing it takes back one jamo. If the name is not what we last wrote (count and last code), the
     composing state is dropped.
   · The rules are those of the 2-set keyboard. A vowel that would make a syllable outside KS X 1001 is ignored; a final that would
     do so commits the syllable and starts a new one.
```

## 6. Saves

```text
■ Slot format (same in Japanese, v1.0, v1.1, v1.2) [verified]
 - Loading ($02:A642) copies the slot to slot 0 and then reads it; autosave ($02:A795) writes slot 0 and then copies it to the original slot.
 - The addresses below are for slot 0. Add n × 0x5E3 for slot n. (The game code also uses X = slot × 0x5E3)
 - Checksum: sum of 0x5E1 bytes from $700022 ($02:A76B, $02:A8B7)
  address           meaning
  $700022           slot number the working copy belongs to
  $700024           playthrough count ($1BC3)
  $700026           number of choices made ($1BC1)
  $700028           page count ($1BC5)
  $70002A-$7003D5   backlog page start positions, 4 bytes each (24-bit position + $55), up to 235
  $7003D6-          script variables, 0x1A4 bytes ($1BEF-)
  $70059A-$7005B3   other state ($1BBF backlog count, $1BB1-$1BB7, $5B, $1BBD, $1BE9, $1A55, position)
  $7005AC           position to continue reading from (24-bit), $7005AF = $55
  $7005B1           $5D
  $7005B3           scene number ($1A55)
  $7005B5           v1.1 marker $C311 (2 bytes the game does not use, 0 when a new slot is made)
  $7005D5           name ($5F)
  $7005E5           screen state, 30 bytes ($18DD)

 - Meaning of the position: Japanese = byte address in the Huffman bit stream ($15-$1D) + $55 bit number
   (bit offset = (file offset - 0xAE401) × 8 + $55), v1.0/v1.1 = LoROM address in the 2-byte script ($20-$35)

■ Continuing old saves (v1.1) [verified]
 - Conversion tables: $17:8000 for v1.0, $19:8000 for the Japanese version. A 2-byte count (4,854) followed by (old 24-bit, new 24-bit) pairs in old-address order. Ends at $XX:F1C5
 - On load, if the marker is missing, the bank of the position tells Japanese from v1.0, a binary search replaces the position with "the last entry at or below it", then the marker is written and the checksum recomputed
 - The name in a Japanese save is replaced with the default name 公平 (Kohei).

■ v1.2 records $70:1800 [verified]
  $70:1800       marker $514C. If missing, $70:1800-$70:184F is cleared to 0 at power-on and the marker written
  $70:1810 + (slot - 1) × 16   slots 1-3
    +0  4 bytes  chapters read in this playthrough (1 bit per chapter)
    +4  4 bytes  chapters read so far
    +8  4 bytes  endings seen
    +12 1 byte   last chapter read
    +13 1 byte   variable 17 on entering the chapter
    +14 1 byte   whether that value is present
 - Whether a chapter was read is judged by whether the position at autosave falls into the chapter's line range.
 - An ending is judged by the position at the moment a new playthrough picks its scenario ($02:A56F).
```

## 7. Space used and space left

```text
■ ROM used by v1.1 and v1.2 (up to the last non-zero byte) [verified]
  location              source                   contents
  $00:FAB0-$00:FB07     asm/qol.asm              bank $00 glue code
  $17:8000-$17:F1C5     tools/savemap.py         v1.0 save position conversion table
  $18:8000-$18:81CF     asm/savecompat.asm       save compatibility code
  $19:8000-$19:F1C5     tools/savemap.py         Japanese save position conversion table
  $1A:8000-$1A:96D0     asm/qol.asm, flow.asm    convenience feature code
  $1B:8000-$1B:8F39     tools/qol.py             chapter ranges ($1B:8000), chapter starts ($1B:8200), endings ($1B:8300), menu strings ($1B:8400-)
  $1B:F000-$1B:F21F     tools/qol.py             scene code per chapter, looping sound list, looping sound bitmap
  $1C:8000-$1C:E627     tools/flow.py            nodes ($1C:8010, 16 bytes each), scenes ($1C:C000), music ($1C:D000), rows per chapter ($1C:E000)
  $1E:8000-$1E:80C9     asm/wordwrap.asm         word wrap code
  $1E:F000-$1E:F7FF     tools/mkfont.py          glyph width table
  $1F:8000-$1F:D457     tools/mkfont.py          v1.1 font
  $20:8000-$35:AF66     tools/assemble.py        v1.1 script
  $36:8000-$36:C01C     tools/namefont.py        v1.3 name glyphs (1,085)
  $36:D000-             asm/nameentry.asm        v1.3 name entry code and tables (jamo tables, 2,350 syllable numbers and codes)
  $02:D8BD-$02:D8C3     asm/nameentry.asm        trampoline to $02:B334

■ Zero runs (4KB or more) [verified: v1.2 ROM. Not a guarantee that they are free]
  $15:E52B-$16:8069, $16:AE4F-$16:FFFF, $18:81D0-$18:FFFF, $1A:96D1-$1A:FFFF, $1B:8F3A-$1B:EFFF,
  $1C:A944-$1C:BFFF, $1C:E628-$1D:FFFF, $1E:80CA-$1E:EFFF, $1F:D458-$1F:FFFF, $35:AF67-$3F:FFFF
 - A run of zeros is not necessarily free; part of a table can be 0. Before using one, check that none of the sources above write to those addresses.
 - The back of $1F is within the range the font decoder reads, so it is safest to put only new group data there. [inferred]
```

## 8. How it was checked

```text
 - Mesen 2 --testrunner + Lua (lua/). Lua file I/O needs AllowIoOsAccess turned on in the settings, and LIBDIR must be an absolute path.
   Saving and loading savestates only works inside a CPU execution callback. (lua/lib.lua)
 - Finding hangs: PC log every frame (lua/qol/pcs.lua) → write watch on suspicious RAM (lua/qol/wtrace.lua) → compare with the normal path
 - Regression: from the same save, mash A for 30,000 frames and check that the sequence of autosave positions ($7005AC) matches v1.1
 - For every build, check that build/waits.tsv (input wait positions compared) and build/overflow.tsv (over 9 lines) have 0 entries
 - Emulators: compat/lr.py (loads libretro cores directly and feeds the same input)
   With the final v1.2 (CRC32 2C31A0B2), 6 cores × 7 cases: new game (without/with header), continuing v1.1, v1.0 and Japanese saves, chapter list, flowchart
  emulator            result
  bsnes               OK (all 7)
  bsnes-hd beta       OK (all 7). Outputs 216 lines instead of 224
  snes9x, snes9x2010  OK (all 7)
  Beetle Supafaust    OK (all 7)
  Mesen-S core        undetermined. All 7 exit immediately with exit 139. Same with the Japanese original
  Mesen 2             OK (playthroughs 1-4, continuing every kind of save. Checked by hand before this re-measurement)
   The cores that passed reached the same scenes and choices to the end; the only difference was the timing of text printing, a few frames.
```

## 9. Not checked

```text
 - The work notes have no record of running on real hardware (an actual Super Famicom, a flash cartridge). Only the emulator results above.
 - Line counts, input waits and jumps were computed for every branch with the tools. On emulator screens, the first screen of all 30 chapters,
   30,000 frames of each of the 3 scenarios, and the start of playthroughs 1-4 were checked.
 - Free WRAM was checked only in the scenes the write watch ran through. A scene the watch did not cover may still use it. (section 2)
 - That task 1 ($1989) prepares sounds in advance is an interpretation from its behaviour. (section 5)
 - The table {23}/{24} read has its address cleared to 0, so which scenes could originally be picked is unknown. (section 3)

Tools used (versions checked in the working environment)
 - asar 1.91, Mesen 2.1.1, Python 3.9.6 + Pillow 11.3.0, macOS Vision (tools/ocr/, macOS only)
```
