# [SFC] Dragon Ball Z: Super Gokuden – Kakusei-hen ROM analysis (Korean patch v1.2-v1.4 work notes)

English | [한국어](ANALYSIS.ko.md)

```text
The ROM structure and methods confirmed while working on the Korean patches v1.2 to v1.4.
I hope it helps anyone analysing the same game or the same engine (Super Gokuden Totsugeki-hen and others).
Patch page: https://perfectacle.github.io/games/kr-patches/sfc/dragon-ball-z-super-gokuden-kakusei/

 - Target ROM: Japanese original, no header, 2,097,152 bytes (LoROM)
   CRC32 3172CD4F / MD5 8502A3E5C0FDC56B6495A644ACA54413
 - Address notation below
   · $XX:YYYY = SFC address (bank:address)
   · file 0xNNNNN = offset in the headerless ROM file
   · LoROM conversion: file offset = (bank & 0x7F) × 0x8000 + (address & 0x7FFF)
 - The included tools were written in Python 3 (needs Pillow) and for Mesen 2 (Lua scripts).
```

## 1. Dialogue text

```text
■ Dialogue IDs and pointer tables
The dialogue command (0x08) of the script names a 16-bit dialogue ID.
IDs are split across banks, and each bank starts with a 16-bit pointer table.
(ID dispatch routine: $83:BA13)

  ID range       bank   pointer table
  000 - 3DF      $99    $99:8000
  3E0 - 5B6      $9A    $9A:8000
  5B7 - 7AE      $9B    $9B:8000
  7AF - 97C      $9C    $9C:8000
  97D - B44      $9D    $9D:8000
  B45 - D15      $9E    $9E:8000
  D16 - ED3      $9F    $9F:8000
  ED4 - F94      $98    $98:C1C8

 - Pointers are 16-bit addresses within the same bank.
   So dialogue cannot move to another bank.
   Lengthened dialogue was moved to free space (0xFF) in the same bank and only its pointer fixed.
 - Several IDs can point to the same string.
   Such strings must not be edited in place but written separately at a new location.
 - For dialogue IDs 0x200 and above, the $98:8000 table has 2 bytes of information per ID,
   and the first byte is the speaker number.

■ String format
 - One character = 16-bit little-endian code
 - 0x000A = line break, 0x0000 = end of string
 - The top bit of a code (0x8000) was stripped and the rest read as the character code.
   [verified] No actual dialogue in the Japanese ROM has a code with this bit set.
 - One page is 4 lines. Empty lines (consecutive line breaks) fill the page to move to the next one.
 - Characters per line: 10 in a window with a face picture, 14 in the narration window [verified]
   · The window is chosen at $80:B879. If the dialogue ID ($3F) is below 0x200 or
     the speaker number (first byte of $98:8000 + (ID-0x200)×2) is not 0xFF, it sets
     $020E=0x10, $0210=8 (face window); if 0xFF, $020E=0x15, $0210=8 (narration window),
     then calls $81:8000. $81:8000 lays out the window tilemap as $020E 8×8 tiles
     × $0210 rows.
   · $80:9B2C, which prints characters, advances 12 pixels per character and breaks the line
     when the next character would pass $020E × 8 pixels (codes below 0x100 are skipped, not printed).
     0x10 cells = 128 pixels = 10 characters, 0x15 cells = 168 pixels = 14 characters. [verified, code]
   · In a test ROM with dialogue ID 200 (narration) and 201 (face) changed to lines of 14–17 and 10–13 characters,
     the engine moves to the next line from the 11th character in the face window and from the 15th in the narration window.
     The overflowing characters take one more line, so the page is pushed.
   · The Japanese ROM also has 2 overflowing lines (ID 7C0, 12 characters; E59, 11 characters),
     and in the Japanese ROM too "‥!" and "‥" are printed alone on the next line.
   · 81 of IDs 000–056 are short exclamations without a speaker number and always use the face window.
     057–1FF after them are font test lines.
   · The v1.2 problem (fixed in v1.3): lines were split assuming a 15-character narration window,
     so 9 lines in IDs 600, 83E, 881, 883, 895 (2 lines), F84, F86 and F87 had 15 characters.
     The last character dropping to the next line was confirmed in scenes 084, 08D and 0B8.
     v1.3 re-split them to 14 characters or fewer following the existing line splitting rules (section 7);
     the page count is unchanged. All face window lines are within 10 characters, and the 6 lines that overflowed in v1.1
     (IDs 228, 2AB, 449, 530, 952, F8D) were all fixed in v1.2.
   · tools/check_width.py compares every line of the dialogue and the battle speech bubbles (section 8) with its window size
     at the end of the build and stops the build if one overflows. Run on the v1.2 ROM it fails with 8 dialogue lines
     and 4 bubbles (1022, 10DC, 1194, 11CE). Run on the Japanese ROM it flags
     7C0, E59 and 118D (a 13-character bubble). These lines overflow in the original too.
 - Some glyphs draw two characters in one cell, such as "!!" and "!?".

■ Font
16×16 characters, stored as 2bpp 8×8 tiles.

  code range     file offset
  100 - 4FF      0x1B00A0
  500 - 8FF      0x1B8000
  900 - FFF      0x1B3CA0  (same data as the area after 2E0 in the first sheet)

 - One sheet row = 16 tiles = 8 characters
   The upper half of a character is at (code - start code) × 32, the lower half 0x100 bytes later
 - Only codes where (code - start code) ÷ 8 is even are real characters.
   Odd rows are lower-half tiles and are not used as character codes.
 - The font is single-colour; plane 0 and plane 1 hold the same values.
 - The 11 new characters v1.2 needed were drawn with the Galmuri11 font
   into glyph slots no dialogue uses.
   [verified] Build output (code = character, original character in parentheses):
   123=깨(겄) 133=꽉(겸) 140=꾼(곡) 237=닿(뜸) 530=렁(씹) 546=롭(얄)
   562=벅(엎) 586=빡(왈) 5B7=뻐(읏) 641=셋(쩡) 642=씻(쪄)
   v1.3 puts the same characters in the same slots. The bubbles use only existing characters,
   with no new ones. The 2 characters needed for the Totsugeki-hen password (section 11)
   are drawn by tools/password.py into the next free slots: 644=뎀(쫄) 647=띠(찔)
 - 6 characters that had no name in the v1.1 table (tables/kr.txt) were also appended (checked by their pictures):
   2D1=딩 2D2=렉 805=션 2D4=창 277=펙 A37=홍. These are characters v1.1 drew for the password grid.

■ Character tables
 - tables/jp.txt : Japanese code table
 - tables/kr-v1.3.txt : v1.3 code table (generated at build time, including the new glyphs)
 - 4 characters missing from the v1.1 table (tables/kr.txt) were appended in v1.3:
   297=P, 7E5=롱, 7F0=릭, 840=토. They are codes v1.1 used in the bubbles, checked by
   their pictures. Adding these 4 lines leaves the v1.2 build output (E46C7A28) the same.
 - Caution: the v1.1 table lists code 922 as "렁", but the actual picture is "렇".
```

## 2. Cause of the v1.1 progression bug (the spaceship wandering off the map)

```text
v1.1 put the lengthened Korean credit and place name strings into free space filled with 0xFF.
But in both places it overwrote real data starting a few bytes before that data ended.

 1) $83:F3AF (file 0x1F3AF)
    The last entry (0xFFFF) of the cutscene character X coordinate table was overwritten.
    This table is read at $83:E44F and $83:E755.
    Result: characters slide off towards a wrong coordinate (x=0x2A5).

 2) $88:FFAE (file 0x47FAE)
    The end marker (0xFFFF) of the movement path record at $88:FFAA and
    the whole record at $88:FFB0 were overwritten. (path pointer table: $88:FC80)
    Result: the map movement routine reads the place name string bytes as a path, and the spaceship leaves the map.

[verified] What v1.1 put in these two places was not dialogue from the dialogue banks but
    $83:F3AF: ending credit strings (pointers $83:9009/900B/900D, $83:94AB/94C5)
    $88:FFAE: place name strings (pointers $88:800C/8018/801C/8048)
The Korean dialogue of the 8 dialogue banks ($98–$9F) stayed within each bank in v1.1 as well.

Fix: restore the original bytes, push the strings that were there further back,
and adjust the pointers to those strings by the same amount. (tools/fix_overwrites.py)
Lesson: do not assume "a run of 0xFF = free space".
Data that uses 0xFFFF as an end marker may sit right before it.
Leave margins around free space and check that it is 0xFF in the original as well.
```

## 3. Title screen

```text
 - Compression: LZSS, decompression routine $80:9CFA
   · first 2 bytes = decompressed size
   · then one flag byte + 8 items, repeated (flags from the low bit)
   · flag 1 = 1 literal byte
   · flag 0 = 16-bit word: length = (word & 0xF) + 3, distance = word >> 4
     A distance pointing before the start of the output reads as 0.
   · The $80:9DA7 variant rearranges the plane order of every tile after decompression.
     (8 rows of plane 0 + 8 rows of plane 1 → SFC 2bpp order)
 - Two BG3 data sets for the title, given by 5-byte entries (address low, address high, bank, size low, size high).
   · 2bpp tiles (tiles 0x000-0x134): $89:9B9D, entry at file 0xD720
   · 32×32 tilemap: $89:C4F3, entry at file 0xD95F
 - When recompressed data was longer than the original, it was moved to file 0x4C801-0x4FFFF (all 0xFF) and the entry fixed.
 - The "DRAGON BALL Z" logo and "(c) BANDAI 1995" are left as in the original.
   This (c) tile is shared with the first copyright line, so do not touch it.
 - The katakana line under the logo (ドラゴンボール) was erased with blank tiles (0xFF, not used by the tilemap).
```

## 4. Ending credits

```text
 - Output routine: $83:8669
 - Name line pointer table: $83:949D (file 0x1949D), 21 16-bit pointers
 - The string format is the same as dialogue (16-bit codes), ending with 0x0000.
 - Lines longer than the original were moved to file 0x1F510 (a 0xFF area unused in the Japanese ROM too) and their pointers fixed.
   (v1.2: "MR. 포포" → "미스터 포포", "Mr. Popo")
```

## 5. Hidden debug menu

```text
A debug menu remains in the retail Japanese ROM.
 - To enable it: change 80 0C (BRA) at file 0x5C to EA EA (NOP NOP).
 - On boot, the ADVENTURE / BATTLE / SOUND menu appears.
 - ADVENTURE has scenario select, flag editing, and message/face/map/BG viewers.
 - ADVENTURE → スタート starts from the scene number in $7E029C.
   It also loads the map that fits the scene. (map number $02A0, table $80:C67B)
 - It starts with the scene progress flags reset, so ordinary conversation scenes come out as in real play.
 - Both the patch note screenshots and the full scene regression test (376 scenes) were done this way.
   (lua/dbgscene.lua)
 - The DBZ quiz that appears in the middle of a scene must be skipped with the X button to continue.
```

## 6. Saves (SRAM)

```text
 - Slot bodies: 0x100 / 0x300 / 0x500, 0x134 bytes each
 - Slot summaries: from 0x800, every 0x20 (0x13 bytes)
                   from 0x860, every 0x20 (0x0C bytes, "Gokuden2nd" + check value)
 - Empty slots are filled with 0x60.
 - Erasing a slot means erasing both summary areas as well, not just the body.
 - v1.2 and v1.3 did not change the save structure, so they are compatible with v1.1 saves.
```

## 7. Other

```text
 - ROM header checksum: file 0x7FDC-0x7FDF (2-byte complement + 2-byte checksum)
   Recomputed after changing the ROM. (tools/fixsum.py)
 - Dialogue line splitting rules (v1.2)
   · Do not break in the middle of a word.
   · Keep the upper and lower lines about the same length.
   · Do not use more lines than needed.
   · Keep stammered speech ("주‥죽어", "d-die") on one line.
```

## 8. ROM map (Japanese / v1.1 / v1.2 compared) [verified]

```text
The three ROMs were compared byte by byte and the changes counted per bank ($80–$BF, 32KB each).
v1.1 ROM = Japanese + v1.1/v1.1.ips (CRC32 32219BC3)

 - Banks changed by v1.1
   $80  debug menu text ($80:C96F), ROM header title ($80:FFC0)
        Japanese "スーパーゴクウデン カクセイヘン" (half-width) → "DBZ SUPER GOKUDEN 2"
   $81–$84 menus, character board, status window ($84:86BE), technique names ($84:C234), save menu ($83:AA0E)
        battle guidance text ($82:F6D3 "공격 입력" (attack input) etc.)
   $83  ending credits, free area at $83:F3AF (section 2 above)
   $88  place names ($88:8000 pointer table), $88:FFAE (section 2 above)
   $89  $89:9989 "プレイヤーチェンジ" → " 플레이어 체인지" (player change) (16-bit string,
        copied by $89:964C to the $0A00 buffer and shown in a window)
   $98–$9F the 8 dialogue banks
   $B4  battle speech bubble dialogue: dialogue IDs 1000–13FF, 1,024 pointers at $B4:8000,
        strings from $B4:8800. 898 real lines; the other 126 are font test lines.
        Several IDs share one string, so there are 729 actual strings.
        · In the battle script (bank $B5, data bank = $B5, position $0FC9), the 2 bytes after commands 01/02/03
          are the bubble ID. The command table is $82:D14C (command 00 = end).
          Command lengths: 01–03, 0A, 12 = 3; 04–09, 0B = 1; 0C, 0D = 2; 0E–11 = 4
          (0E–11 jump to the 2-byte address that follows if the condition holds).
          Script start tables: $B5:BA7E, $B5:C5AC, $B5:CC74, $B5:D141 (80 each,
          read by $82:D099/D0DE/D0EF/D125 with the battle number in $0E2B).
        · Command 01 = $82:D172: reads the pointer at $82:D19C and copies it to $0A00,
          $020E=0x0C, $0210=0x0A → 96 pixels = 8 characters × 5 lines.
          Commands 02/03 = $82:D1DC: reads at $82:D206, $020E=0x12, $0210=6
          → 144 pixels = 12 characters × 3 lines. Characters are printed by the same $80:9B2C as dialogue (section 1).
        · [verified] Following the 4 start tables through every branch gives 592 bubble IDs,
          and no ID is used with both sizes. The read code addresses ($82:D1A0 = command 01, $82:D20A = 02/03)
          of the 230 bubbles that actually appeared while running the 376 scenes
          all agree with this. The only 8-character × 5-line windows are 1033, 1034, 10DD/10DE (Kaio-ken
          explanation) and 1189 (Chi-Chi's explanation).
          The other 306 IDs are not called by any script.
        · [verified] With test lines shown in scene 00A (ID 1000 = 11, 12, 13 characters;
          1001 = 12, 13, 14 characters), the 12-character window moves to the next line from the 13th character,
          and the overflowing line is outside the window and not visible.
        · In the battle of scene 00A (World Martial Arts Tournament), ID 1000 "너 정말로 누구야?" ("Who are you, really?")
          was confirmed to come from this table.
        · v1.2 did not touch them; v1.3 fixed 443 strings
          (719 IDs) against the Japanese original. tables/bubbles-v1.3.tsv, tools/bubble_patch.py.
          The 7 lines at IDs 137B–1381 are where v1.1 put an ending farewell and the names of the translation team,
          so they were left as they are (section 10).
   $B6–$B7 dialogue font
 - Banks changed by v1.2 (against v1.1)
   $80  4 header checksum bytes ($80:FFDC)
   $83  4 end-marker bytes at $83:F3AF, credit block moved, "미스터 포포" line at $83:F510
   $88  8 bytes of end marker and record at $88:FFAE, place name block moved
   $89  title tiles ($89:9B9D) and tilemap ($89:C4F3) recompressed
   $98–$9F 782 dialogue lines
   $B6–$B7 11 new characters
 - Banks changed by v1.3 (against v1.2)
   $80  4 header checksum bytes
   $98, $9B, $9C  line breaks of 8 narration lines (relocated by the number of added line break codes)
   $B4  443 battle bubble strings, 185 of them moved to free space in the same bank
        (3,669 bytes free in $B4 after the build)
   $81  code tables of the password/name entry cells $81:8D56, $81:8E00 (section 11)
   $83  password pair table $83:A60E, name conversion table $83:AEB0 (section 11)
   $84  password/name entry grids $84:A3E0, $84:A4D0 (section 11)
   $B7  4 new characters (딩 띠 렉 창)
 - The other banks ($85–$87, $8A–$97, $A0–$B3, $B5, $B8–$BF) are identical in all three ROMs.
 - Banks changed by v1.4 (against v1.3, section 12)
   $80  renderer hook $80:9B7E, header ROM size byte (0x0B → 0x0C) and checksum
   $81  name entry hooks, code and tables ($81:DA60–$81:E234), title menu cursor box x ($81:8672),
        chapter menu strings ($81:D654), addresses of the button icon palette instructions ($81:95F3 and the like)
   $84  title menu strings ($84:A1D8–$84:A24D), status screen button guides and 「기술 경험치」 ($84:86DC–$84:896C)
   $C0–$CA  new 1 bpp glyphs (name glyphs, title and chapter menu glyphs)
   $CB  2 bpp button guide glyphs
   $E0  syllable → code table NeSylCode ($E0:8000–$E0:D747)
   The ROM is 4 MB now; $CC–$DF and $E1–$FF are 0xFF.

■ v1.3 relocation per dialogue bank (tools/build.sh output)
  Of 782 lines, 432 did not fit in place and were moved within the same bank.
  (The v1.2 build moved 436 lines; $9C 70 lines and 4,831 bytes, $98 30 lines and 3,224 bytes.)

  bank   lines moved   free space left after the build
  $99      76      2,526 bytes
  $9A      61      4,680 bytes
  $9B      78      3,715 bytes
  $9C      67      4,840 bytes
  $9D      48      3,700 bytes
  $9E      27      3,476 bytes
  $9F      46      3,463 bytes
  $98      29      3,226 bytes

 - "Free space" is the total of the 0xFF runs from the first string to the end of the bank,
   minus a 1-byte margin next to live data. (The same rule as dialogue_patch.py)
 - The Korean dialogue of v1.1 was shorter than the Japanese, so every bank had 0xFF left at its end.

■ Other free space left
 - File 0x4C801–0x4FFFF (14,335 bytes): 0xFF in both the Japanese ROM and v1.2.
   Kept for moving the title data if it grows; v1.2 does not use it.
 - File 0x1F53C–0x1FFFF (2,756 bytes): 0xFF in both the Japanese ROM and v1.2.
   The v1.2 credit line uses 0x1F510–0x1F53B.
```

## 9. Using the Mesen 2 scripts

```text
 - Run: Mesen --testrunner <ROM> <script.lua>
   The scripts use Lua file I/O, so AllowIoOsAccess must be turned on in the Mesen settings.
 - lua/dbgscene.lua (run on a ROM with the debug menu enabled)
   · At frame 430 it puts the scene number in $7E029C and starts with A.
   · Environment variables: TARGET (scene number, hex), MAXF (last frame, default 3000),
     PERIOD (A mashing interval, default 70), EVERY (capture interval), QUIZ=1 (skip the DBZ quiz with X),
     SHOT_DIR (folder for screenshots and ids.txt)
   · It watches reads of the 8 dialogue pointer tables and the $B4:8000 (battle bubble) table and
     writes "frame dialogueID kind readCodeAddress" to ids.txt.
     kind d = dialogue, b = battle bubble. The code reading the dialogue tables was $83:BB0A, $83:BADA,
     $83:BAC0 and $83:BA56; for the bubble table, $82:D1A0 (command 01) and $82:D20A (commands 02/03).
     The address recorded is that of the instruction after the one that read.
   · Long scenes such as dialogue during battle needed MAXF raised to 30000.
 - lua/crjump.lua: starts at scene 0x050, then the moment $80:822D executes it changes
   PC to $83:8669 (the credit output routine) to show the ending credits right away.
 - Lessons from lua/lib.lua
   · Button input must be set in the inputPolled event for the game to read it.
   · Saving and loading savestates only works inside an exec callback. (M.defer)
   · Errors in Lua callbacks fail silently. Wrap them in pcall and pass the memType argument exactly.
   · SRAM written from Lua is not saved.
     It was copied directly to ~/Library/Application Support/Mesen2/Saves/<ROM name>.srm.
 - Window width test: redirect the pointers of dialogue ID 200 (narration) and 201 (face) to free space in $99,
   put in test lines and start scene 000; ID 200 appears around frame 744
   and ID 201 around frame 1237 (PERIOD=120).
 - lua/compat.lua: plays the input scripts in compat/ (section 10 below) as they are on Mesen 2.
   Environment variables SCRIPT, SHOT_DIR, LUA_DIR (folder containing lib.lua).
```

## 10. For the next person

```text
 - [left as is] Bubble IDs 137B–1381 (7 lines) are where v1.1 put an ending farewell and the names of the
   translation team instead of the Japanese dialogue. v1.3 did not change them either.
     137B い‥生きていたのか!!                 → 자 이제 슬슬/작별할 시간이다! (Well then,/time to say goodbye!)
     137C それじゃ そろそろ/おわかれの時間だ! → 지금까지 이 게임을/즐겨주셔서 감사합니다!! (Thank you for/playing this game!!)
     137D ここまで やりこんで/くれた キミとなら/次もきっと会えるよな!! → 한글화/엑소버드/PERFECTACLE (Korean translation/Exobird/PERFECTACLE)
     137E そ‥孫‥/だれと 話てるんだ‥?        → 번역/김태준/라헬 (Translation/Kim Taejun/Rahel)
     137F 打ち所がわるかったか‥               → 번역/별소리/양동이 (Translation/Byeolsori/Yangdongi)
     1380 うるせえぞピッコロ!/だまらねえと魔封波で/封じこめんぞ!! → 번역/UNKNOWN (Translation/UNKNOWN)
     1381 じゃあな みんな!/また会おうなーーー!! → THANK YOU/FOR PLAYING
 - [unchecked] Whether the 306 bubbles no battle script calls ever appear was
   not checked. check_width.py treats a bubble as an 8-character × 5-line window if the Japanese has 4 or more lines,
   otherwise as a 12-character × 3-line window. 10AF, 10C6, 11CF and 11FD, whose Japanese already fits neither window,
   only produce warnings.
 - [caution] bubble_patch.py uses only the character table dialogue_patch.py produced.
   dialogue_patch.py looks only at the bubbles of the input ROM (v1.1) when picking free glyph slots,
   so before adding more characters, check that the slot is not used by the v1.3 bubbles.
 - Scene regression (lua/dbgscene.lua, 12,000 frames per scene, A every 40 frames, QUIZ=1)
   compares the whole order in which dialogue IDs appeared.
   · v1.2 vs Japanese: 342 of 376 identical. Of the 34 that differ, 30 diverge after a battle starts
     (different dialogue lengths shift the moment of input, which changes the battle outcome),
     3 (045–047) differ in how often the same line repeats in the dinosaur chase scene, and 1 (052)
     is v1.2 seeing 4 more lines within 12,000 frames.
   · v1.3 vs v1.2: 360 identical. The other 16 are all cases where, after a battle starts, one side is still
     in battle and shows fewer lines. Rerunning the 16 for 30,000 frames makes
     13 identical; the remaining 01D, 01E and 11D are cases where one side drags the battle out longer with the same input
     (still on the battle screen at 28,000 frames). Mesen's test mode ends after about 100 seconds,
     so a 30,000-frame run is recorded up to about frame 28,000.
   · v1.3 vs Japanese: 348 identical.
 - Emulator compatibility (compat/run_all.sh, lua/compat.lua)
   The same input scripts (compat/s_*.txt) were fed to Mesen 2 and libretro cores.
   new = new game, 9,000 frames (headerless ROM, headered ROM),
   cont = continue from the released 100% save, 6,000 frames (Japanese, v1.2, v1.3),
   narration = debug menu scene 084, bubble = scene 00A (Japanese, v1.3),
   pwjp/pwko = new game → password, entering the Totsugeki-hen debug ENDING password (in kana on the Japanese ROM;
   on v1.2 and v1.3 by finding the cells matching the Totsugeki-hen v1.1 screen characters, section 11),
   pwdebug/phrase = enter the debug ENDING password / 「손오공은사이어인」, set a name, then
   play 9,000 frames, wrong = 「손오공은사이어」 (7 characters), cheat = 「체력을늘려줘신룡」.
   To run them, put libretro cores (.dylib) in compat/cores/ and jp.sfc,
   v12.sfc, v13.sfc, v13h.smc (headered ROM), jpd.sfc and v13d.sfc (debug ROMs with file 0x5C changed to
   EA EA) and save.srm in compat/roms/. ROMs and cores are not included.
   Debug scenes write the scene number to $7E029C at frame 430. For bsnes, which does not expose a WRAM pointer,
   a Pro Action Replay cheat makes the game read that value for 40 frames.

   emulator            result
   Mesen 2             OK (all scenarios)
   bsnes               OK (scene set by cheat)
   snes9x, snes9x2010  OK (scene number order same as Mesen 2)
   bsnes-hd beta       new, cont and passwords OK (outputs 216 lines). Neither WRAM pointer nor cheats work,
                       so debug scenes are undetermined
   Beetle Supafaust    new, cont and passwords OK. Adding a cheat makes the core exit with an exception,
                       so debug scenes are undetermined
   Mesen-S core        undetermined (even the Japanese original exits immediately with exit 139)

   The only differences between cores were a few frames in text printing timing and the screen height.
   Passwords behaved the same on every core: Japanese and v1.3 pass (name screen), v1.2 rejects.
   「손오공은사이어인」 passes on every core, goes to the name screen with the default name (엑소버드),
   and after setting a name reaches the same scene as the debug password (the DBZ quiz at the World Martial Arts Tournament).
   v1.2 and the 7-character phrase are rejected; 「체력을늘려줘신룡」 passes.
 - Regression sample: rerunning 63 scenes (one in every 6) with the final build gave
   63/63 identical dialogue ID orders against the previous v1.3 results.
 - The title Korean logo font (BM YeongSung) uses the macOS system font path.
   On other systems, TITLE_FONT in tools/title.py must be changed to produce the same ROM.
 - Tool versions used (the zip was rebuilt with these versions and CRC32 B9F14962 confirmed)
   · Python 3.9.6, Pillow 11.3.0
   · Mesen 2.1.1 (macOS)
```

## 11. Password carried over from Totsugeki-hen (v1.3)

```text
 - Entering the 50-character password from the Totsugeki-hen ending at new game → password carries over the name and records.
 - Check routine $83:A1F8 [verified]
   · Collects the input at $1F00 (16-bit codes, 0x272 = space) into $1E00 without the spaces.
   · For each pair of characters it finds the same pair in the $83:A60E table (256 pairs, 2 codes per pair)
     and writes its index (0–255) as 1 byte. The first 23 pairs = 23 bytes; the sum is 16-bit.
   · It passes (returns 0) if the two bytes (low, high) given by the 24th and 25th pairs equal the sum.
   · On a pass, $83:A313 looks up bytes 6–15 (five 16-bit characters, the name) in $83:AD58 (Totsugeki-hen code list),
     replaces each with the entry at the same index in $83:AEB0 (Kakusei-hen codes) and writes them to $0C00.
 - Contents of the 23 bytes [verified: Totsugeki-hen $81:D048 (makes the password), Kakusei-hen $83:A313 (takes it)]
     bytes   value stored by Totsugeki-hen        what Kakusei-hen does
     0–1     9 bits of $0D99/$0D9B/$0D9D          if byte 0 bit 2 ($0D99 & 0x200) is set,
             (byte 0 bits 0–7, byte 1 bit 0)      sets technique 15's bit ($0D2E bit 15) via $82:EDFB
     2–4     $0C8B–$0C8D                          not read
     5       $0B00                                not read
     6–17    $0B01–$0B0C (name, 6 16-bit chars)   converts 6–15 to a 5-character name at $0C00
     18–20   $0C91, $0C92, $0C90                  not read
     21–22   $022F–$0230                          written to $0266–$0267: the play time, where $80:8610
                                                  raises the hours ($0267) when the minutes ($0266) reach 60
     23–24   sum of 0–22 (16-bit)                 checked
   · Health and battle power ($0C86–$0C90, $0CAA–$0CB4) start at fixed values regardless of the password.
   · Technique 15 is Goku's power technique 「거북선인류최종오의」 (Turtle Hermit school ultimate secret) on the technique table
     [verified: in Mesen, setting only $0D2E bit 15 and opening the technique table shows only this row lit. Unlearned techniques
     are drawn darkened by $81:CB8B with palette $1400].
   · Where Totsugeki-hen sets $0D99 bit 9 (technique 9 「무천류 최종오의」, entry 9 of the name table at $84:B605)
     [verified: reading Totsugeki-hen v1.1 code and scripts]
     - Code that writes $0D99: new game initialisation ($80:80F7, $0D99 = 0x37), event script
       commands 1C–1E ($81:99F9), map script commands 0E ($81:B81D, set) and 0F ($81:B868, clear).
       The battle reward table ($B0:F9ED) has no flag 9, and no event script has 1C–1E 09 00.
     - Map script 0E 09 00 occurs once, at $B3:DB07. Of the five other 0E 09 00 in the ROM,
       $90:9DCE, $92:BBC8 and $97:DD04 are not in banks with map scripts, $AC:9239 is
       a 09 command following the operand 0E of command 38, and $8A:C7D7 does not fit the script grammar
       before or after, so it is taken to be data [inferred].
     - The choice at $B3:DA41 (0x6F 「마신다」 drink / 0x70 「마시지 않는다」 don't drink) is the Ultra Divine Water scene
       at Korin Tower. The end of the 「마신다」 branch: 0E 0D 00, 0E 0F 00, 0E 0C 00 (techniques 13, 15, 12: Super Kamehameha,
       Kamehameha attack, guided Kamehameha) → 0D 96 00 07 DB (command 0D, $81:B7C3: go to $DB07 if event
       flag 0x96 of $0D79 is set) → if clear, 3B (end of script,
       $81:AA2B) → if set, 0E 09 00 then 3B.
     - Flag 0x96: at $B6:BEF1, 0C 96 00 (clear, $81:B771), then the Arale quiz (message 0x0F58,
       choices 0x72–0x74); only the third answer (0x74, 「ほひょ！？」 in Japanese, 「PERFECTACLE」 in the Korean
       Totsugeki-hen) passes 0B 96 00 (set, $81:B726) at $B6:BF0E.
     - So bit 9 is set only by answering the Arale quiz correctly and drinking the Ultra Divine Water; it can be clear
       even after finishing Totsugeki-hen.
   · Values in the Totsugeki-hen debug ENDING password: byte 0 = 0, name = あ×6 (0x100),
     18 = 100, 20 = 50, 21–22 = 2 (0 hours 2 minutes), the rest 0.
 - Phrase passwords [verified]
   · When 입력완료 (done) is pressed, $83:A408 compares the input with 6 phrases before $83:A1F8 runs.
     $83:B008 「체력을늘려줘신룡」 → starting health and battle power, $83:B046 「하드코어한플레이를
     하고싶어신룡」 → low starting stats, $83:B0A4 「이회차플레이를하고싶어신룡」 → result 2
     (restart), $83:B10E 「콜렉션좀많이모아줘신룡」 → $0CCE and $0D9E tables set to FFFF,
     $83:B182 「모든기술을알려줘신룡」 → all technique bits, $83:B1E2
     「모든세이브를클리어해줘신룡」 → erases the 3 save slots. (The Japanese version uses kana phrases; v1.1 changed them to Korean)
   · The v1.3 cell rearrangement drops 룡, 션, 싶, 플, 해 and 회 from the grid, so they were put into cells that are not
     password characters (ぼ ぽ ボ ポ and blanks) so all six phrases can still be typed.
   · Phrase added in v1.3, 「손오공은사이어인」 (the password the Korean Totsugeki-hen ending shows):
     $83:A4D0 (no phrase → return 0) was changed to JMP $83:FE00, and the new routine compares the input
     with the 8 characters at $83:FE80. On a match it sets technique 15, puts in the same starting health and
     battle power as $83:A313, writes $0266 = 2 (0 hours 2 minutes) and returns 1. 1 means a phrase password
     matched, so it goes to $81:9276 and skips the name conversion ($83:A313), and the name screen shows
     Kakusei-hen's default name.
     · Why these defaults: health and battle power are fixed values in the original too. Technique 15 is a bit
       that is set only when the conditions above (Arale quiz answer + Ultra Divine Water) are met, but this password
       stands in for a fully completed Totsugeki-hen, so it is set. The play time of 0 hours 2 minutes has no basis
       and was picked arbitrarily, borrowing the value from the debug ENDING password.
     · Phrase codes (Kakusei-hen): A27 577 144 5B4 A04 5C2 552 5C4 (손오공은사이어인)
       Codes Totsugeki-hen uses to draw the same characters: 182 1A7 106 1AF 221 1C1 1A2 1C2
 - Entry screen [verified]
   · Codes the cells enter: $81:8D56 hiragana, 85 cells; $81:8E00 katakana, 85 cells
     (index = row × 15 + cell, read by $81:91F9). The name entry screen uses the same tables.
   · Screen grids: $84:A3E0, $84:A4D0 (16-bit strings, one row = blank+5 cells+blank+5 cells
     +blank+5 cells+line break, drawn by $81:8B74). A enters input mode, X switches hiragana/katakana.
 - Problems in v1.1 (through v1.2) [verified]
   · The cells and grids were changed to Korean codes while the $83:A60E pair table kept the Japanese codes,
     so no password could pass.
   · The character layout of the cells differed from the Totsugeki-hen ending screen: of the 156 password character cells,
     only 25 showed the same character as Totsugeki-hen.
   · $83:AEB0 was also shifted by one entry from the 37th entry on, so 136 of its 171 characters were wrong.
 - The v1.3 fix (tools/password.py, tables/totsugeki-password.tsv)
   · Matching the pair table of the Totsugeki-hen v1.1 ROM ($B7:F09F, Totsugeki-hen codes) slot by slot with the Kakusei-hen pair table
     found 152 password characters; drawing the Totsugeki-hen font (8×16, $83:DE00) as pixels showed which Hangul
     each character looks like on the Totsugeki-hen screen. (Those different from their name in the character table:
     ち=께, ナ=건, デ=띠, バ=떠)
   · One Kakusei-hen code was chosen per character and written into the pair table, the 170 entry cells, both grids and
     the 171-character name table. Cells that are not password characters (ぼ, ぽ, ー etc.) get the characters of the name table,
     and the blanks in the や and わ rows stay blank as in the Japanese version.
 - Checks (Mesen 2, pwjp and pwko of compat/run_all.sh)
   · Finding and pressing the Totsugeki-hen debug menu ENDING password exactly as the Totsugeki-hen v1.1 screen shows it:
     v1.3 passes to the name screen (가가가가가); v1.2 has no 「건」 cell, so the password is wrong.
   · Another password using the whole pair table (23 random bytes + sum) also passes on v1.3.
   · 「손오공은사이어인」: passes to the name screen (default name 엑소버드). The scene order after setting a name
     was the same as with the debug ENDING password, and the only memory differences were the name and $0D2E bit 15.
     「손오공은사이어」 (7 characters) is a wrong password. 「체력을늘려줘신룡」 also passes on v1.3.
   · A password made with Totsugeki-hen codes 0x186 0x225 0x1C2 0x14C 0x12C in the name bytes (6–15)
     shows 「스서인레다」 on the v1.3 name screen (name conversion confirmed).
 - Things that also happen in the original [verified]
   · Totsugeki-hen uses 0x227 (ぺ, hiragana), but the same slot in the Kakusei-hen pair table is katakana ペ.
     They look the same on screen, so typing the hiragana is wrong in the Japanese version too (the reason the debug ENDING
     password was rejected in the Japanese version). Typing the katakana passes.
   · The Totsugeki-hen pair table has 152 characters, Kakusei-hen 151. The 3 slots where Totsugeki-hen uses り (0x147)
     (values 0x4C, 0x73, 0x7B) are taken as リ (0x1E7) by Kakusei-hen.
   · Korean v1.3 rewrites the pair table slot by slot to match the Totsugeki-hen pair table,
     so typing ぺ (성) and り (디) exactly as the Totsugeki-hen screen shows them passes. The original Japanese
     codes can be found by comparing the pair table in tables/totsugeki-password.tsv with $83:A60E
     of the Kakusei-hen ROM.
 - On the Totsugeki-hen v1.1 screen, different password characters looked the same.
   つ and へ = 나 (pixel-identical), も and ら = 등 (pixel-identical), ル and ォ = 지, わ, を and ん = 러.
   Kakusei-hen v1.3 shows へ=다, も=동, ル=저, を=레, ん=렉 as the Totsugeki-hen character table names them,
   and Totsugeki-hen v1.2 draws the same mapping. The mapping the two games share is the fourth column of
   tables/totsugeki-password.tsv (the Hangul shown in the Kakusei-hen cell),
   and all 163 characters are distinct. ち=께, ナ=건, デ=띠 and バ=떠, whose shapes differ from their table names but do not
   collide, keep their Totsugeki-hen v1.1 shapes.
 - [unchecked] There is no save from actually playing Totsugeki-hen to the end, so the only passwords checked are
   the debug menu ENDING password and the constructed ones.
 - [unchecked] Whether Totsugeki-hen can be finished without drinking the Ultra Divine Water. The condition for technique 15
   was found by reading the scripts and the command handling code, not confirmed by playing.
```

## 12. v1.4 names: jamo name entry and new 16 px glyphs

```text
 - v1.4 ROM: output of tools/build-v1.4.sh = CRC32 8AA3123E, 4,194,304 bytes (header ROM size byte 0x7FD7: 0x0B → 0x0C).
   Banks $C0-$FF map to file 0x200000-. [verified]
 - The five names [verified]
   · $0C00 + name × 10, five 16-bit codes each (space 0x272). $80:81D2 copies the defaults from $84:A048.
     The Japanese ones are プレイヤー, なかよし, いじわる, 女の子ちゃん and せんせい (the player, classmates, the teacher).
   · Writers: the name entry ($81:8AF7 and 8B0C write $0C00 + $022B × 2; Y blanks all at $81:8A19)
   · Readers (static search, then confirmed by running)
       $81:8BB1        the name list of the name entry (copied to $0A00, drawn by $80:997B)
       $81:A12F etc.   quiz ranks 1-4 on the achievement list (name number $03A7)
       $80:99E0, 99F9  control codes 0x10 (name 0) and 0x11 (name 4) in $80:997B strings: the classmates'
                       comments that X shows on the achievement list (strings $84:D53E-$84:ED18)
       $83:A336-       the name conversion of the Totsugeki-hen password (section 11)
     The dialogue engine skips codes below 0x100, and no dialogue has a name code.
 - Glyphs (tools/font16.py)
   · The 882 Hangul syllables of the dialogue font (section 1) stay; the other 10,290 syllables and the 51
     compatibility jamo are drawn with Galmuri11 (12 px) as new codes 0x1000-0x3864. 「띄」 (help text) is one of them.
   · From 0x3865 come the typeset title and chapter menu glyphs (also 1 bpp, bank $CA), and from 0x3C00 the button
     guide glyphs (both planes, 64 bytes, bank $CB), below.
   · The earlier new glyphs (dialogue_patch.py) were aligned by each glyph's bounding box; the 11,000 here share
     one origin taken from 「가」, so 「으」 and 「우」 keep the font's own heights.
   · The font has one colour (plane 1 = plane 0), so a new glyph is 1 bpp, 32 bytes (a left and a right byte per
     row) at bank $C0 + (code - 0x1000) / 0x400, offset ((code - 0x1000) % 0x400) × 32 (banks $C0-$CA).
   · Syllable → code table NeSylCode at $E0:8000 (11,172 entries)
   · Why all of 가-힣: the name entry composes jamo freely, so 뷁 is typed through 뷀, and 뷁, 뷀, 똠 and 얅 are
     not in KS X 1001. Even the 2,350 KS syllables alone would need a larger ROM (the dialogue font has about 80
     free slots and the 2 MB ROM about 50 KB of scattered free space), so all are there.
 - Renderer hook (asm/v14.asm, code at $81:DA60-)
     $80:9B7E  the branch for codes from 0x900 (SEC / SBC #$0900 / STA $2F). From 0x1000 it expands the glyph
               to 2 bpp in low WRAM $1600-$161F (top tiles) and $1700-$171F (bottom tiles), sets DB = $80,
               $50 = $1600, $27 = 0 and returns to $80:9B9A. The renderer reads its $0200- variables and the glyph
               through DB, and banks $C0- have no low-RAM mirror; DB = $7E could make the line-break path read
               I/O registers from WRAM, so the glyph goes through low RAM instead.
 - Name entry ($81:8959 loop) [verified]
   · The Japanese screen is a grid of 15 cells × 6 rows (hiragana and katakana pages, X switches) and
     「입력완료」 (cell 0x55). The password entry ($81:9033 etc.) reads the same cell tables and grids on its own
     and is left alone.
   · The v1.4 grid (NeGrid and NeCell in work/font16_data.asm): row 0 consonants, row 1 double consonants,
     rows 2 and 3 vowels. Both pages point at it (the LDA long operands at $81:8B70 and $81:8B82).
   · A ($81:89DD) composes, B ($81:89E5) takes back one jamo (deletes a character when not composing),
     X ($81:8A0B) types a space, Y still clears all, and Start (after $81:89ED) puts the cursor on 입력완료 (A there
     goes on to the next name); Start did nothing on this screen in the Japanese game. The help text ($81:891A) now says 지우기 and 띄어쓰기.
   · The syllable being composed is at $022B. The next one goes to $022B + 1 and blanks the rest of that name;
     a key past the fifth position of a name is ignored. When B, 입력완료 or Y move the cursor off the last
     position and code we wrote, the composing state is dropped and typing overwrites from the cursor. B then
     moves the cursor back one position like the game's B, and on past the name's trailing spaces to just after
     its last character. Y ($81:8A26) also resets the state.
   · The cursor skips empty cells: the ends of the original moves, STA $0229 / JMP $89BA ($81:8A58 right,
     $81:8A8D left, $81:8AAF down, $81:8AD1 up), become JMPs that repeat the move while the cell is empty.
   · State in WRAM $7F:FF00-$7F:FF31, which nothing wrote after boot in new game, password and battle
     scenes (a write callback on the whole CPU address space with the mirrors folded together). It is reset
     when the screen opens, at $81:89A6.
 - Centred title menus (MENUS in tools/font16.py)
   · $84:A1D8 (new game / option), $84:A1FA (continue / new game / option), $84:A22E (start / password) and
     $81:D654 (the chapter to continue from, 피콜로편부터 and so on) were
     centred with leading spaces only, so a line moved in 12 px steps and sat up to 6 px off, with a 12 px space
     inside 새 게임.
   · The cursor box also sat 4 px from the left and 8 px from the right of the window's inside (x 66-189), at
     x 70-181. Its x is LDA #$0048 / STA $45 at $81:8672; 0x4A moves it to 72-183, 6 px on each side.
   · Each line is now typeset from the dialogue font's glyphs pixel by pixel (4 px word space), centred on x 128
     on screen and cut into 12 px glyphs with new codes; a line keeps its number of codes. Every line of the three
     menus is now centred at x 128.
 - Two syllables squeezed into one glyph (FIELDS in tools/font16.py)
   · Where the Japanese status screens had one kanji, v1.1 drew two syllables into one 12 px glyph:
     0x273 전환, 0x274 취소, 0x275 험치, 0x276 다음. They are in the button guides of the status, achievement list,
     event clear list, skill experience, skill setting and skill list screens ($84:86DC, 87E2, 886A, 888C, 8904,
     896C) and the command 「기술경험치」 ($84:878E).
   · Each field is copied a fixed number of codes ($81:96AB and the like, LDX/CPX) into a window of fixed width
     ($020E), so neither can grow. The dialogue font's syllables do not fit even one pixel apart (기술경험치 is
     51 px in a 48 px window), so the button icons stay and the labels are typeset in Galmuri11 Condensed (7 px)
     into the field's width (its codes × 12 px + 4 px, cut at the window edge) and cut into 12 px glyphs with new
     codes. Button guides are centred; the command item starts where the other items do and now reads 「기술 경험치」, spaced out
     (2 px between letters, 5 px between words) to end where 기술설정 and 기술습득 end (x 46).
   · Button icon colours: the guides are on BG3 (2 bpp), and each screen ORs a palette into the four tilemap entries
     (two tiles, two rows) under each icon ($81:95F3 and the like: LDA $7E5xxx / ORA #$0400, 0800, 0C00 or 1000 /
     STA $7E5xxx). Each guide ends on screen x 230, where the lines below it end (values, separators, lists), keeps
     the same margin from its panel's left edge as from the right (x 243) and spaces its items evenly. Each icon is
     kept within two tiles (left column mod 8 at most 5) and off any tile another icon uses (a shared tile gets both
     palettes), and those instructions' addresses move with the icons. The event clear list does not fit 96 px that
     way, so it shows only 「Ⓑ취소」 and Ⓐ's palette instructions become NOPs. These
     glyphs keep both planes for the icon colours (64 bytes, codes 0x3C00-, bank $CB) and the renderer copies them
     as they are.
 - Checked (MesenCE 2.2.1)
   · Five names (뷁얅닭, 똠방, 쌤힣, 읊잖, 손오공) land in WRAM as typed and show correctly in the name list,
     the achievement list ranks and the classmates' comments (「뷁얅닭의움직임이 심상치 않다!」).
   · B through 뷁 → 뷀 → 붸 → 부 → ㅂ → space, X for a space, keys ignored once five positions are full.
 - Emulator compatibility (compat/run_all.sh, section 10): the v1.4 ROM ran new14 (with and without header),
   cont, bubble, narration, pwko, pwdebug14, phrase14, wrong and cheat on Mesen 2, bsnes, bsnes-hd beta,
   snes9x, snes9x2010 and Beetle Supafaust; all 54 scene-word logs match the v1.3 logs of the same scenario.
   new14, phrase14 and pwdebug14 only change the moves to 입력완료 on the name screen for the v1.4 grid
   (left, then up). As with v1.3, Supafaust's debug scenes and the Mesen-S core give no verdict.
   This comparison ran on the build before the title menu and button icon fixes (CRC32 29F5A03B). What changed since
   is the menu and guide glyphs, the cursor box x and the palette instruction addresses; the status screens were
   checked on MesenCE screenshots.
```

## 13. Included files

```text
gokuden2-kr-v1.3-tools.zip
 - tools/build.sh          : the whole build order
                              (Japanese + v1.1 IPS → bug fixes → title → dialogue → bubbles → password
                               → credits → width check → checksum → two IPS files)
 - tools/bubble_patch.py   : inserts and relocates the battle speech bubbles ($B4)
 - tools/check_width.py    : fails the build if a dialogue or bubble line is wider than its window
 - tools/password.py       : aligns the Totsugeki-hen password entry cells, check table and name table (section 11)
 - tables/totsugeki-password.tsv : password characters and pair table taken from the Totsugeki-hen v1.1 ROM
 - tools/dialogue.py       : reads the dialogue pointer tables
 - tools/extract.py        : Japanese/Korean dialogue dump (TSV)
 - tools/dialogue_patch.py : inserts and relocates dialogue, draws new glyphs
 - tools/font.py           : reads font glyphs
 - tools/lz.py             : LZSS compression/decompression
 - tools/title.py          : builds and inserts the title graphics
 - tools/fix_overwrites.py : repairs the v1.1 data overwrites
 - tools/credits.py        : fixes the ending credits
 - tools/fixsum.py         : recomputes the header checksum
 - tools/ips.py            : applies/creates IPS
 - tools/fonts/            : Galmuri fonts (SIL OFL, LICENSE.txt included)
 - tools/usedsheet.py      : list of glyphs used by the dialogue
 - tables/jp.txt          : Japanese character code table
 - tables/kr.txt          : v1.1 character code table (build input, 4 missing characters added)
 - tables/kr-v1.3.txt   : v1.3 character code table (build output)
 - v1.1/v1.1.ips          : v1.1 patch (build input)
 - tables/dialogue-v1.3.tsv : 782 corrected dialogue lines (ID, text, "/" = line break).
                              Only the line breaks of 8 narration lines differ from the v1.2 table.
 - tables/bubbles-v1.3.tsv  : 443 corrected battle bubbles (the first ID among IDs sharing a string)
 - lua/dbgscene.lua, lua/crjump.lua, lua/lib.lua, lua/compat.lua : Mesen 2 scripts
   (debug menu scene start and dialogue ID logging, showing the ending credits directly, compatibility input playback)
 - compat/lr.py, compat/run_all.sh, compat/s_*.txt : a tool that feeds the same input to libretro cores
   for comparison, and its input scripts (section 10)
 - tools/build-v1.4.sh     : order of the v1.4 build on top of the v1.3 build (section 12)
 - tools/font16.py         : draws the new glyphs, typesets the menus and button guides, builds the jamo tables and grid
 - asm/v14.asm             : renderer hook and jamo name entry (asar 1.91)
 - compat/s_new14.txt, s_phrase14.txt, s_pwdebug14.txt : scenarios for the v1.4 grid

Notes
 - ROM files are not included.
   To build, put the Japanese original ROM named super-gokuden-jp.smc in the unzipped folder
   and run zsh tools/build.sh. (Resulting CRC32 B9F14962)
 - The BM YeongSung font used for the title Korean logo uses the macOS system font path,
   so on other systems the TITLE_FONT path in tools/title.py must be changed.
 - The paths in the first lines of the Lua scripts are for the working environment; adjust them before use.
```
