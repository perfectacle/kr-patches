# [SFC] Super Mario RPG ROM analysis (Korean patch v1.1/v1.2 work notes)

English | [한국어](ANALYSIS.ko.md)

```text
The ROM structure and methods confirmed while working on the Korean patches v1.1 and v1.2.
A record so that anyone who analyses this ROM again or continues fixing this patch can pick up at the same addresses.
Patch page: https://perfectacle.github.io/games/kr-patches/sfc/super-mario-rpg/#making
v1.0 release post: https://blog.naver.com/perfectacle/220297115483

 - Markers
   · [verified] checked by reading ROM bytes directly or by running it in Mesen 2
   · [inferred] has supporting evidence but was not confirmed by running it
   · [source]   stated in external documents (mostly for the North American version). The source URLs are at the end of section 7.
   · Items without a marker were checked against the ROM and in Mesen 2 while making this patch.

 - Target ROM: Japanese original, no header, 4,194,304 bytes (SA-1)
   CRC32 5527071E / MD5 59483FEB9EB20207E3241E005FBDDE7E
 - v1.1 was built on top of the v1.0 Korean ROM (Japanese + v1.0 IPS, CRC32 F4305A06).
   Resulting ROM: CRC32 ABD8AC13 / MD5 8E5320631EDCF274BF5C7A62C0417C55
 - v1.2 fixed three things in v1.1: names in battle messages, the battle name banner (section 3),
   and a dialogue font code collision (section 2 "Dialogue font code collision").
   Resulting ROM: CRC32 05DBCBE6 / MD5 B7F488D4F448304890A4BCE8000248E2
   Differences from the v1.1 ROM [verified]
   · file 0x7FDC-0x7FDF header checksum
   · 0x15693, 0x156A8-0x156BE, 0x156DF-0x156F5 (battle messages and 1C 38), 0x241D5-0x241DB, 0x24209-0x2420F (name banner)
   · 0x60B4: the address of v1.1's JSL KoDlgName ($C0:60B3). For the reason below, the tables and code at the back of $E2 moved 2 bytes earlier.
   · name tables and code from $E2:B400: new code ($E2:FDE2-$E2:FF6C), 해피쉘 (Happy Shell), 파이어쉘 (Fire Shell), 힐쉘 (Heal Shell), 천둥콰르릉 (Thunderbolt)
   · 2 dialogue font glyphs (0x2490E8-0x2490FE 콰, 0x2494D8-0x2494EC 힐)
   · menu dynamic glyphs: 248 → 249 (셸 removed, 힐 and 휠 added; section 2 "Two wrong lines in the menu font code table"), numbers and pictures changed
 - Address notation below
   · $XX:YYYY = SFC address (bank:address)
   · file 0xNNNNNN = offset in the headerless ROM file
   · $C0-$FF bank conversion: file offset = (bank & 0x3F) × 0x10000 + address
     e.g. $E2:B400 = file 0x22B400, $C1:06AF = file 0x106AF
 - The included tools were written in Python 3 (needs Pillow), asar 1.91 (65816 assembler) and for Mesen 2 (Lua scripts).
   Exact versions are in section 10.
```

## 0. ROM header and memory

```text
■ ROM header (file 0x7FC0-0x7FDF) [verified]

  offset    Japanese                v1.1                    meaning
  0x7FC0    "SUPER MARIO RPG      " "SUPER MARIO RPG (K)  " game title, 21 bytes
  0x7FD5    23                      23                      map mode (SA-1)
  0x7FD6    35                      35                      cartridge type (SA-1 + ROM + RAM + battery)
  0x7FD7    0C                      0C                      ROM size 2^12 KB = 4MB
  0x7FD8    05                      05                      RAM size 2^5 KB = 32KB (BW-RAM)
  0x7FD9    00                      00                      region (Japan)
  0x7FDB    00                      00                      version
  0x7FDC    8A BA                   32 90                   checksum complement
  0x7FDE    75 45                   CD 6F                   checksum (Japanese 4575, v1.1 6FCD)

 - In v1.2, 0x7FDC-0x7FDF is C3 D4 3C 2B. (checksum 2B3C)

 - The extended header 0x7FB0-0x7FBF is 30 31 41 52 57 4A ... ("01ARWJ") in both ROMs.
 - The save file (.srm) Mesen 2 creates was also 32,768 bytes.
 - The meaning of the cartridge type byte is interpreted per the SFC header specification.

■ Memory used in this document

  name      size     address                  notes
  ROM       4MB      $C0:0000-$FF:FFFF        four 1MB windows (section 3 "Why the ROM stays 4MB")
  WRAM      128KB    $7E:0000-$7F:FFFF        patch variables at $7E:0C00-$17FF
  VRAM      64KB     (PPU)                    field menu dynamic glyph cells $6000-$7FFF
  BW-RAM    32KB     $40:xxxx (SA-1 side)     battle menu bitmap $40:7000, name buffer $40:6800

■ $00:3000-range and $00:6000-range as seen from the S-CPU [verified]
 - S-CPU $00:3000-$37FF = SA-1 I-RAM 0-$7FF.
   Comparing the two memories byte by byte in Mesen 2 matched 2048/2048 bytes.
 - S-CPU $00:6000-$7FFF = one 8KB BW-RAM block. The block number is set by register $2224 (BMAPS),
   and the game writes 01 at $C0:089C. So $00:6000 = BW-RAM $2000, $00:7000 = BW-RAM $3000 = SA-1 $40:3000.
 - Checked in two scenes, field and battle. (MAPCHECK=1 of test/probe.lua)
 - The current room number $00:3030 is SA-1 I-RAM $30; the event variables in $00:7000-range are BW-RAM $3000-range.
```

## 1. Dialogue text

```text
■ Dialogue IDs and pointer table
Dialogue IDs are 0x000-0xFFF (4096), and the address calculation routine is $C0:5800.

 - Pointer table: $F7:E000 (file 0x37E000), 16 bits per ID
   The value is not an absolute address but an "offset from the group start address".
 - Group = ID >> 9 (8 groups of 512)
 - Group start addresses are in a header at the start of each bank from $E2.
   · first 16 bits of the header = header size (this value is also the start address of the bank's first group)
   · then the start addresses of the following groups (16 bits each)
   · groups that do not fit in the header continue in the next bank.

  ID range       bank   groups
  000 - 7FF      $E2    0 - 3
  800 - DFF      $E3    4 - 6
  E00 - FFF      $E4    7

 - Example: dialogue ID 0x204 (v1.1 ROM) [verified]
   · group = 0x204 >> 9 = 1
   · $E2 header = 08 00 F5 03 15 33 6D 67 → header size 0x0008 (4 groups), group 1 start = $03F5
   · pointer at $F7:E000 + 0x204 × 2 = $F7:E408 (file 0x37E408): 25 00 → 0x0025
   · $E2:03F5 + 0x25 = $E2:041A (file 0x22041A)
   · string: 1B 07 20 1D 07 1D 22 21 00 = 「<item name>」을 획득! ("Got 「<item name>」!")
     ($1B 07 = name + 「」 + centred + 을/를, 20 = space, 1D07 = 획, 1D22 = 득, 21 = !, 00 = end)
   · v1.0 string of the same ID (file 0x220510): 09 3B 1A 3C 8F 20 1D 07 1D 22 21 00
     (09 = 3-cell tab, 3B/3C = 「」, 1A = name, 8F = 을)
 - Dialogue cannot move to another bank, and the group order must be kept.
 - In bank $E4, the menu font starts at $E4:2800 right after the dialogue, so the dialogue must not run past it.

■ String format and control codes
1-byte and 2-byte codes are mixed.

  code          meaning
  00            end of dialogue
  01            line break
  02 - 04       window advance
  (00 - 06 were all treated as codes that end a line)
  08 / 09 / 0A  tab (2 / 3 / 4 cells)
  0B xx, 0D xx  codes followed by a 1-byte parameter
  1A            insert item name (item number in $0234)
  1B            unused in the original (used in v1.1 for name insertion, see below)
  1C xx         insert number (1-byte parameter)
  1D-1F xx      2-byte characters
  20 - FF       1-byte characters
  3B / 3C       「 」
  3D / 3E       『 』

 - One dialogue character cell and the tab unit are both 10 pixels. Lines were fitted to 22 cells.
 - Each tab code delays character output by about 30 frames.
   So centring was done with "one tab code + spaces".
 - In the control code branch table, the handler address of $1B was $624E (does nothing and moves on).

■ Item name insertion codes ($1A, $1B)
 - Original $1A: copies the bytes of the item name table to $7E:2D00 with MVN,
   then continues output using that as a substring.
 - v1.1 changed $C0:60B2 to write the Korean name (dialogue encoding) to $7E:2D00.
   · $0221 = name byte count (the dialogue engine counts bytes; a 2-byte character counts 2)
   · $021C = substring address ($2D00)
 - The branch address of the unused $1B ($C0:6896) was changed to the same handler as $1A ($60A6).
   The handler tells them apart by the code byte, and $1B is followed by a 1-byte flag.
   · 1 = wrap the name in 「」
   · 2 = centre the line (reads ahead the remaining characters of the line and pads spaces in front)
   · 4 = append 을/를 after the name, matching its final consonant
 - At build time, patterns such as 「{1A}」, 「{1A}」을 and 「{1A}」(을)를 in the dialogue were changed to $1B + flag.
   The name length is only known at run time, so centring of the "obtained" messages must also happen at run time.

■ Dialogue relocation
 - v1.0 wrote item names directly into the dialogue text in English. (e.g. 『MUSHROOM』을 얻었습니다, "Got 『MUSHROOM』")
   These were replaced with Korean names, and each bank was refilled keeping the group order.
 - After refilling, the bank headers (group start addresses) and the $F7:E000 pointer table are rebuilt.
 - Several IDs can point to the same address. Each address was written once and all pointers fixed.
 - Result (against v1.0): $E2 -7,584 bytes, $E3 -9,136 bytes, $E4 -2,133 bytes
   because Korean names are shorter than the English ones and the junk bytes below were dropped.

■ Problems v1.0 left
 - Bytes not shown on screen remained after the end code (00) of dialogue.
   They are fragments of the original text left when v1.0 overwrote it. Relocation discarded everything after the end code.
 - Some places had an end code where the dialogue should continue. (checked against the Japanese original)
   · ID 498: empty (original: frog coin received message)
   · ID 8B4: empty (original: Peach's "shh" line)
   · ID E85: cut after the first line (the original has two lines)
   Lesson: entries of length 0 or noticeably shorter than the original are worth comparing with the original.

■ Other text that uses the same encoding as dialogue

  contents          pointer table              count  handling
  battle dialogue   $F9:6554 (bank $F9 addr)   256    refilled
  item descriptions $FA:2F20 (bank $FA addr)   177    refilled
  menu text         $FE:EF00 (base $FE:F000)   118    fixed in place
  battle messages   $FA:26F1 (base $FA:0000)    46    fixed in place
  "what's on your mind" $F9:9411 (base $F9:0000) 256  fixed in place

 - The menu text area contains data no pointer points to.
   So strings were fixed in place rather than moved.
   Only strings that grew used the 0 bytes after them, or were moved to spare space ($FE:F61C-$FE:F6FF) with the pointer fixed.
 - No spare space to move into was found for the battle message and "what's on your mind" areas,
   so they were only allowed to grow into the 0 bytes after each string.
```

## 2. Fonts

```text
■ Menu font (item/menu screens, 1-byte codes)
 - $E4:2800 (file 0x242800), 256 codes × 24 bytes, 8×12 2bpp
   glyph of code c = $E4:2B00 + (c - 0x20) × 24 (00-1F are empty)
 - When a menu opens, an outline/shadow is added to make 8×16 4bpp ($C3:6D74, outline routine $C3:6869)
   and all 256 characters are uploaded to VRAM BG1. Tile number = (c - 0x20) × 2 (upper), +1 (lower)
 - v1.0 used all of 0x20-0xFF with no gaps. (165 Hangul, data/tbl/korTBL2.tbl)
   Lesson: the reason item names could not be put in Korean was not ROM space but
   the "1-byte code = 256 cells resident in VRAM" structure.

■ Dialogue font (variable-width output, 1-byte + 2-byte codes)
 - $E4:4000 (file 0x244000), 24 bytes per character
 - Glyph number
   · 1-byte code c: c - 0x20
   · 2-byte code (p, l): 0xE0 + (p - 0x1D) × 0x100 + l
   → 0x000-0x3DF, 992 characters
 - v1.0 code table: data/tbl/korTBL.tbl
   All 768 2-byte codes are mapped, so there are no free codes.

■ Reusing unused 2-byte codes
21 characters needed for item names were missing from the dialogue font.
So 21 2-byte codes that no text uses were found, and the new characters drawn in their place.

  1D12=캔  1DD4=깃  1DF5=널  1E00=닉  1E1C=링  1E47=몽  1E9A=샷
  1EFE=샹  1F04=셜  1F13=셸  1F15=쉘  1F44=캡  1F5B=핸  1F5C=훈
  1F87=슐  1F8D=싹  1F93=쑥  1FA0=잣  1FA7=츠  1FBD=퀸  1FF2=탕

 - Deciding "unused" must include every area that uses the same encoding, not just dialogue.
   (dialogue, battle dialogue, item descriptions, menu text, battle messages, "what's on your mind", enemy attack names,
    level-up/action command guidance text) tools/py/textusage.py
   Lesson: picking by dialogue alone breaks characters used elsewhere, such as 「봅」 in the menu tutorial.
   The build stops if a reused code appears in v1.0 text.

■ Dialogue font code collision (fixed in v1.2) [verified]
 - Of the 21 above, 1F44 was originally "힐" and 1FA0 originally "콰". The v1.0 text did not use them, so they became reuse
   candidates, but the names newly added by v1.1, "힐셸" (item 0x43, "힐쉘" from v1.2) and "천둥콰르릉" (special 0x18), used the
   original korTBL codes, so wherever they were drawn with the dialogue font (result window, level-up screen, names in dialogue,
   Yoshi Cookie message, name banner) they appeared as "캡셸" and "천둥잣르릉". Menus use the menu font and showed them correctly.
   (Confirmed from the font bitmap: glyph 1FA0 is "콰" in the v1.0 ROM and "잣" in the v1.1 ROM)
 - Of 768 2-byte codes, v1.0 text used 747 and 21 were reused, so none were free.
   Rescanning every text area of the built v1.1 ROM (the same range as textusage.py + KoDlgNames, KoLvSkills)
   found exactly two codes used in v1.0 but no longer used in v1.1.
     1F7F = 줏 (gone after the spelling fix "줏어" → "주워")
     1FA9 = 궈 (gone after the spelling fix "잠궈" → "잠가")
 - v1.2 renamed item 0x43 to "힐쉘" to match "레이지쉘" (0x21, 0x46). (data/name_overrides.json)
   해피셸 (0x30) and 파이어셸 (0x3E) were made "해피쉘" and "파이어쉘" the same way.
   쉘 uses dialogue font 1F15 (one of the reused codes) and a dynamic glyph in menus. No name uses 셸 any more, but 1F13 stays
   셸. (tools/build.py DLG_PINNED: pins the reused code assignment of the released ROM per code, so a syllable that is no longer
   needed does not shift the codes of other syllables)
 - v1.2: drew "콰" at 1F7F and "힐" at 1FA9. (tools/build.py DLG_REUSE_FIXED) The prefix is 1F, so the result window
   (KoResultChar, which reads only prefixes 1D-1F) draws them too. The codes of the existing 21 characters are unchanged.
   · A syllable originally mapped to a reused code is treated as "not in the font" and gets a new code.
   · The build stops if a syllable of a name (items, specials, names in dialogue, dialogue fix text) goes to a reused code,
     or if 줏/궈 appears again in new text.
   · build/dlg_tbl.json keeps 줏/궈 at the very end, because dlg_rewrite.py decodes v1.0 dialogue with this table in reverse
     (the last syllable per code) to find fix targets such as "잠궈".
 - Checks: all 182 names (every Korean name) converted from the built table back to screen characters matched;
   verify_dialogue.py gives the same result as v1.1 (no byte changes in the dialogue area); Mesen 2 before/after screens (result window 캡셸 → 힐쉘,
   천둥콰르릉 on the level-up screen and the name banner).

■ Dialogue font extension (glyphs from 0x3E0)
 - $E4:9D00 (file 0x249D00), right after the last dialogue font glyph (0x3DF), is empty (zeros).
   32 glyph slots were reserved there. (v1.1 uses 5: 솟 쑤 웨 휠 릉)
 - The dialogue engine cannot print these glyphs. (the 2-byte prefix codes are only 1D-1F)
   Only the special names on the level-up screen use this area, with prefix $20. (see section 4)

■ Two wrong lines in the menu font code table (fixed in v1.2) [verified]
 - korTBL2 lists 5F=힐 and FF=휠, but in the ROM the picture at 0x5F is a dot (●) and at 0xFF is "빼".
   v1.1 used the table as it was, so menus (field and the shared battle data) showed "힐셸" as "●셸" and "지노휠" (Geno Whirl) as "지노빼".
   (Names in the dialogue font were right)
 - All 165 Hangul of the menu font were drawn next to their code table characters and compared by eye; these two were the only wrong ones.
 - v1.2: tools/build.py MENU_TBL_WRONG drops the two lines so 힐 and 휠 are drawn as dynamic glyphs.
 - Check: tools/py/check_menu_names.py (the last step of tools/make.sh; the build fails on a mismatch)
   It reads KoNames, KoSkills, KoEnemies and KoGlyphOffs back from the built ROM and compares 414 item, special and enemy names character by character.
   · dynamic glyphs: picture in the ROM = picture redrawn with Galmuri (must be identical)
   · menu font codes: must be listed with the same character in data/tbl/menu_font_audit.txt (186 codes checked by eye, character, picture sha1)
     and have the same picture
   · MENU_REUSE 85/9B/DF: must equal the Galmuri pictures build.py drew
   The battle menu (SA-1, KoFetch/KoGlyphX) reads the same tables and pictures, so it is covered too.
 - Galmuri and the v1.0 menu font differ in design; judging by how similar the pictures look picked wrong for 89 or more of
   the 165 characters. So the menu font is judged against a list checked once by eye and picture hashes.
 - 지노휠 could not be checked on screen because there is no savestate with Geno in the party; it was checked with the test above.

■ Menu font reuse (MENU_REUSE)
 - The guidance text on the field special screen cannot use dynamic glyphs (section 6),
   so the 3 characters it needs were put directly into the menu font.
 - Codes 85, 9B and DF, unused by menu text and by item/special/enemy names, were picked
   and changed to 되 (85), 운 (9B) and 웁 (DF).

■ New glyphs
 - Galmuri11 Condensed (SIL OFL) drawn at 12 pixels, made into 8×12.
 - 2 bytes per row (second byte 0) × 12 rows = 24 bytes
```

## 3. Item / special / enemy names

```text
■ Original name tables (v1.0 put names here in English capitals)

  contents    address                    entry size  structure
  items       $FA:41FC (file 0x3A41FC)   15 bytes    icon 1 + name 10 + unused 4
  specials    $FA:137F (file 0x3A137F)   15 bytes    same format as items
  enemies     $F9:8C11 (file 0x398C11)    8 bytes    name 8

 - The first 27 entries of the special table (0x00-0x1A) are the party's specials.
   The rest are enemy attack names, already in Korean in v1.0.

■ New name tables (from $E2:B400 = file 0x22B400)
After the data of dialogue bank $E2, the space is zero up to 0x230000 in the Japanese ROM too.

  KoNames      256 × 21 bytes   icon 1 + 10 16-bit characters
  KoSkills      64 × 21 bytes   same format
  KoEnemies    256 × 16 bytes   8 16-bit characters
  KoDlgNames   256 × 22 bytes   names in dialogue encoding (1-byte header + name + 0)
  KoParticles                    을 / 를 (dialogue encoding)
  KoLvSkills    64 × 16 bytes   special names for the level-up screen

 - 16-bit character codes
   · 0x0000-0x00FF: the menu font 1-byte code as is
   · 0x8000 | n: dynamic glyph n (a character not in the menu font)
 - KoDlgNames / KoLvSkills header = name byte count | 0x80 (if the last character has a final consonant)
 - Names were put in without spaces because the screen cells are too few.

■ Dynamic glyph data
 - The 249 characters missing from the menu font were stored as 8×12 2bpp (24 bytes).
 - The battle renderer reads glyphs at "$E4:2B00 + 16-bit offset",
   so the data must lie within file 0x242B00-0x252AFF.
   Within that range, it was split across stretches that are 0 in both the Japanese ROM and v1.0.
   (filled in the order 0x24EDD8, 0x2511C2, 0x252534, 0x251D48)
 - Glyph number → offset table: KoGlyphOffs (16-bit)

■ Field menu (S-CPU)

  hook         contents
  $C3:7990     draw item name → DrawItemName
  $C3:799D     draw special name → DrawSkillName
  $C3:0102     JSR $013E in the menu NMI → NmiUpload (runs the original jobs, then uploads glyphs)
  $C3:6D74     start of the routine that builds the font when a menu opens → ResetSlots
  $C3:2078     name of the item being carried to a character (sprite) → HeldName

 - Characters in the menu font use tile (c - 0x20) × 2 as before.
 - Missing characters are assigned one of 128 cells in VRAM $6000-$7FFF (BG1 tiles $200-$2FF).
   The field menu screen does not reference this area, and it is reloaded when a menu opens.
   So the slot table is cleared when a menu opens, too.
 - Assigned characters are converted with the game's outline routine ($C3:6869) and collected in WRAM (up to 12),
   then DMAed to VRAM in the NMI.
 - Patch variables live in WRAM $7E:0C00-$17FF. (the game does not use it in menus, battle or dialogue)
 - The name sprite shown while carrying an item reads glyphs from $7E:8000 + (c - 0x20) × 32.
   Codes 00-1F point to $7E:9C00-$9FFF, so dynamic characters are converted there and used from 00.
 - Lesson 1: when the menu NMI job slots ($A0-$A7) are full, the registration routine ($015B)
   sends a sound command and gives up registering. (the symptom: music changes in Toad's menu tutorial)
   So the NMI routine was hooked directly instead of using a slot.
 - Lesson 2: the variable area first chosen, $7E:F580-$F8FF, was the item sprite buffer.
   "WRAM that is normally 0" can still be used on particular screens.

■ Battle menu (SA-1)
 - $C1:6A3F reads 11 characters via the $308C pointer and draws them into a BW-RAM bitmap.
   Glyphs are read directly from $E4:2B00 + (c - 0x20) × 24.

  hook         contents
  $C1:6AC7     read a character → KoFetch (reads from KoNames when the address is in the item/special table)
  $C1:6AFA     glyph address calculation → KoGlyphX
  $C1:6C6D     copy the name into the $40:6800 buffer → KoCopy (writes Korean for the item/enemy tables)

 - In the $40:6800 buffer, dynamic characters are written as 2 bytes.
   $1C-$1F + low byte = dynamic glyph ((code - $1C) << 8) | low byte
 - Code $1F, unused by the menu font, serves as the "dynamic character" marker passed to the renderer.

■ Why the ROM stays 4MB
 - The SA-1 MMC shows a chosen block in each of four 1MB windows at $C0-$FF.
   Reading beyond 4MB would mean switching a window at run time,
   and since the S-CPU and SA-1 run at the same time, the other side reading the original block during the switch would misbehave.
 - So the ROM was not expanded, and only space that is empty in the original as well was used. (see section 9)

■ Item names in dialogue
 - The $1A/$1B handler (section 1) copies the dialogue-encoded name from KoDlgNames to $7E:2D00.
 - 을/를 after the name is chosen by the final-consonant bit of the header. (을 = $8F, 를 = $76)

■ Names in battle messages (v1.2) [verified]
 - Battle messages in the banner at the top of the screen are drawn with the dialogue font by the interpreter at $C1:5680.
   Control code 1C xx follows the $C1:5683 branch table at entry xx - $30.
   1C 31 = name of item $FA06 ($C1:56A8), 1C 37 = name of special $FA14 ($C1:56DF)
 - The original routines read the original name tables ($FA:41FC, $FA:137F) directly. (ADC $FA000A at $C1:56B4 etc.)
   v1.0 had put English there and v1.1 did not touch these two places either,
   so when a Yoshi Cookie turned a monster into an item, "몬스터는 MUSHROOM 모습이 됐다!" ("The monster turned into a MUSHROOM!") appeared. (since v1.0)
 - v1.2 replaced both routines in place. (src/main.asm org $C156A8, org $C156DF)
     LDA $FA06 (or $FA14) / JSL KoBtlItem (or KoBtlSkill)
     loop: JSL KoBtlNext / BCS end / JSR $5769
   · KoBtlItem: copies the name from KoDlgNames to the buffer at $7E:1110.
   · KoBtlSkill: party specials 0x00-0x1A use KoLvSkills; enemy attacks from 0x1B use the original table (Korean since v1.0) as is.
   · KoBtlNext: puts the next character in A. 2-byte characters with prefix $1D-$20 are passed as (prefix - $1C) << 8 | low byte,
     so characters with prefix $20 (the dialogue font extension area) are drawn too. Sets carry at the end of the name.
   · $C1:5769 is the character drawing routine of the original interpreter.
 - New code $E2:FDE2-$E2:FF6C (including the banner fix), variables $7E:1100-$7E:1105, name buffer $7E:1110-$7E:1124,
   banner string $7E:1128-$7E:112E
 - Check: Mesen 2 showed "몬스터는 버섯 모습이 됐다!" (turned into a 버섯, Mushroom), and the bsnes, bsnes-hd beta and Supafaust cores showed
   "몬스터는 단단해져라 모습이 됐다!" (turned into a 단단해져라). (section 8, emulators)
   A message using 1C 37 was not seen in an actual scene.

■ Battle name banner (battle animation command $63) [verified]
 - Battle animation script interpreter: $C2:0C43 reads the command byte from [$60] and goes to JMP ($0D31,X).
   Entry $63 of table $C2:0D31 is $4131, and $C2:4131 is the name banner command. The command is the two bytes 63 xx.
 - xx picks the branch, and the number is $40:0060,X (the entity's number slot, copied to $E0).
     0  enemy attack names  $F9:59F4 (address stored at $F9:0012)  13-byte entries  $C2:41A5
     1  specials, magic     $FA:137F ($FA:0008)                    15-byte entries  $C2:41D9
     2  items               $FA:41FC ($FA:000A)                    15-byte entries  $C2:420D
   The result goes into $0B86 (address) / $0B88 (bank) / $0B8A (character count), with $0B80 = 3 and $0B84 = 4.
 - $C1:51A7 copies 32 bytes from [$0B86] to $7E:05E0 and puts 00 at position $0B8A.
   This text is drawn by the battle message interpreter ($C1:5598). The interpreter draws 2-byte characters with prefixes 1D-1F,
   but $20 is a space, so it cannot draw characters from the dialogue font extension area (prefix $20).
 - Forcing it to show in the v1.1 ROM: enemy attack 0x22 "허수아비의 종소리" and magic 0x40 "파이어볼" in Korean,
   item 0x6D "YOSICOOKIE", specials 0x00 "JUMP" and 0x0E "CRUSH" in English.
 - Whether branch 1 with party specials (0x00-0x1A) and branch 2 appear in normal play [verified + byte search]
   · Monster behaviour scripts: bank $F9, pointer table $F9:30AA (address at $F9:0010), interpreter $C2:A38C.
     Below 0xE0 = attack; E0-FF go through the branch table at $C2:A3C3. The action kind is $072A (attack 2, magic 3), the number $072C.
     The numbers of the magic commands EF xx / F0 xx yy zz are all 0x40 or above. (no party special numbers)
     E1, which produces action kind 4, occurs as a single byte in all the scripts, and that is the argument of E3 E1 (dialogue number).
   · Animation data: 63 01 occurs only at $F5:252C (a part enemy magic calls in common; right before it, $F5:2524 is 63 00).
     Searching the whole ROM for 63 0x preceded by 11 or 69 found no 63 02 in the script area.
     The scripts were not all followed by command length. [inferred]
   · In battles where enemies only use normal attacks, in the 15 savestates in test/states, and when the party used items and specials,
     this branch did not run.
   So the English banner is taken not to appear in normal play.
 - The v1.2 fix (src/main.asm org $C241D5, $C24209, $C15693, $C156BB, $C156F2)
   · $C2:41D5, $C2:4209: JSL KoBanSkill / KoBanItem; JMP $0C53
     KoBanSkill points to $FA:137F as before for numbers 0x1B and up (enemy magic).
     Otherwise it writes 20 1C 38 A5 <kind 1|2> <number> 00 to WRAM $7E:1128 and points $0B86/$0B88 there.
   · Entry 8 of the 1C table ($C1:5683) (originally $56A3, same as entry 0) was changed to $C1:56BB (JML KoBtlBanner).
     KoBtlBanner goes to the original handling ($C1:56A3) if the next byte is not A5. If it is A5, it reads the kind and number
     and passes the name one character at a time to $C1:56F2 (JSR $5769; RTL) via KoBtlItem/KoBtlSkill + KoBtlNext.
     The interpreter uses Y as the drawing position ($C1:55BB, which reads the bytes, also does PHY/PLY), so KoBtlBanner preserves Y too.
   · KoBtlNext treats $20 as the extension character prefix only when the byte after it is below $20.
     This is because of the spaces in unused item names left in English ("KILL BOMB" etc.).
 - Check (test ROM: the start of the behaviour scripts of Goomba (6) and Spikey (1) changed to EF 40 FF FF; for items also $F5:252D set to 02)
   · Enemy magic 0x40 shows "파이어볼" through the original path.
   · In Mesen 2, changing the value written at $C2:4166 (STA $E0) showed all 27 party specials and 165 items (155 with names +
     10 in English) through the real path. Recording the character codes passed to $C1:56F2 and converting them back with the code table
     matched every name (final v1.2 build, 192). Extension characters (솟아나라쑤욱, 지노웨이브, 지노휠, 릉 of 천둥콰르릉)
     are drawn too. On the first run only 힐셸 and 천둥콰르릉 differed; that is section 2 "Dialogue font code collision".
   · Tools: test/probe.lua (EXEC, ONCE); the script that changes the banner number and records character codes is test/banner_ids.lua;
     the comparison is tools/py/check_banner.py
```

## 4. Automatic particle selection

```text
■ Dialogue
 - $1B flag 4: appends 을/를 depending on whether the last character of the name has a final consonant.
 - At build time, the particle right after a renamed name was fixed together with it.
   (이/가, 을/를, 은/는, 과/와, 아/야, 으로/로, tools/py/textfix.py)
   For names ending in a digit, 0, 1, 3, 6, 7 and 8 were treated as having a final consonant.

■ Level-up screen (SA-1)
 - In the level-up screen sentence, code $03 inserts the special's name.
   Originally the name came from the item-format table (English in v1.0).
 - Glyph list entry = code | kind << 8; the renderer draws dialogue font glyph number (code - 0x20).

  hook         contents
  $C2:D3CF     special name → KoLvSkill (reads from KoLvSkills and appends 을/를)
  $C2:D4EA     right after drawing a number → KoLvAfterNum (draws only one of "(이)가")
  $C2:D734     glyph kind decoding → KoLvAttr (handles 2-byte characters)

 - For 2-byte characters the prefix byte ($1D-$20) goes into the kind byte, and KoLvAttr turns it back into a glyph number.
   Prefix $20 is the dialogue font extension area (0x3E0 and up).
 - The original sentence "(을)를 배웠습니다." was changed to "배웠습니다." ("learned"). (found and fixed within $C2:D300-$C2:D800)
 - 이/가 after a number: "가" if the last digit is 2, 4, 5 or 9, otherwise (0, 1, 3, 6, 7, 8) "이"
   (levels 10, 20... end in "십", so "이")
```

## 5. Battle result window

```text
 - The name of an item received is copied to $7E:05E0 and drawn with the dialogue font ($E4:4000).

  hook         contents
  $C1:779A     copy the name → KoResultName (copies from KoDlgNames and sets the position)
  $C1:787E     read a character → KoResultChar (turns a 2-byte character into one glyph)
  $C1:7161     window size choice → KoResultGeom

 - The original always places the item name at the left of the line below "아이템" (item).
   v1.1 right-aligns it to the end of the numbers (right edge 180 pixels),
   and if the name is 5 characters or fewer, puts it on the same line as "아이템" and makes the window one line shorter.

  layout  condition                window
  0       $3F8E is not 0           original large window
  1       no item                  original small window
  2       name of 5 chars or fewer same line, window one line smaller
  3       name of 6 chars or more  next line, original large window

 - Window bounds = [$3F90 - r, $3F92 + r + 1] × [$3F94 - r, $3F94 + r + 1], r = 3 × $3FB4 - 3 (verified)
 - Passing -Dres_ui=0 to asar builds with the original layout. (for before/after screenshots)
```

## 6. Next-technique hint on the field special screen

```text
 - The original draws the name in a 4-cell slot and then draws menu text $1C after it.
   So short names left gaps like "マロ　　が…".
 - The text list of this screen is $C3:33B5.
   Its first byte was changed to 1 so that only $1C is drawn; the patch routine draws the other lines.

  location      contents
  $C3:77F6      start of drawing the menu text → KoSpecialHint (pulls $1C right after the name)
  $C3:33B5      first byte of the text list → 1
  $C3:35F0      level number position → second line ($7E:5D8E)
  $FE:F0A9      menu text $1C → "는" (code $76)

 - Result: "<name>는 / 레벨 N이 되면 / 새로운 기술을 배웁니다" ("<name> / learns a new technique / at level N")
   A one-digit number is pulled right after "레벨 ", and 이/가 is chosen by the last digit.
 - The layer this text is drawn on cannot use dynamic glyphs,
   so the needed characters (되, 운, 웁) were put directly into the menu font. (section 2, menu font reuse)
```

## 7. Debug features and RAM

```text
Addresses are as seen from the S-CPU. Checked by running the Korean ROM based on the Japanese version in Mesen 2.

■ Battle debug menu [verified]
 - From file 0x106A9: AF AE FF 00 05 80 F0 01 60 (LDA $00FFAE / ORA $80 / BEQ +1 / RTS).
   Changing F0 (BEQ) at 0x106AF to 80 (BRA) makes Start open the menu on your turn in battle.
   Same location as the North American PAR code C106AF80. [source]
   Mesen 2 Lua: emu.write(0x106AF, 0x80, emu.memType.snesPrgRom)
 - Items: SCENE / OBJ / BG / (blank) / HPMAX / MUSIC / SE / LINE / (blank) / EFFECT / EVT 1-3 / TEST
   Results of running each one on the Korean ROM based on the Japanese version. (test/states/battle_menu.mss + Start) [verified]
     OBJ     object viewer
     BG      "BG NO." window
     HPMAX   tried with HP already full, so no visible change
     MUSIC   "NO." window, "MAX.5F"
     SE      appears to be a sound effect test [inferred]
     LINE    a black horizontal line at the top of the screen (appears to be a CPU usage display [inferred])
     EFFECT  "BG ANIME" window
     EVT 1   the Bowser's Keep chandelier scene and Peach's "쿠파를 조심해요 마리오 씨!!" ("Watch out for Bowser, Mario!!")
     EVT 2   battle with the red-clothed enemy on the chandelier
     EVT 3, TEST   not checked
   The cursor also stops on the blank lines between items; pressing A there just closes the menu.
 - SCENE: the screen shows SCENE / NO. xxx / 00; the number is hex.
   Up/down changes the number, and A loads that formation.
   The chosen number goes to $7E:052A, and after loading to $7E:FA0E.
 - Magic effect test menu: file 0x106D1 is 20 B3 AF (JSR $AFB3),
   the same location the North American codes C106D2F3 C106D307 change. Not tried. [inferred]

■ Field debug menu [verified]
 - Enable the North American PAR D4AFC100 D4AFC226 DF000001 and talk to the NPC in Mario's house (North American name Fungi Light) [source]
 - File 0x14AFC1-0x14AFC2: Japanese value 73 25; the North American code writes 00 26.
   Following the per-room NPC pointer table (file 0x148000), this is inside the second NPC record of room 0xBD.
   It appears to change the NPC event number from 0x573 to 0x600. [inferred]
 - File 0x1F0000 (Japanese 00 0C): the first entry of the bank $1F event pointer table.
 - On the ROM based on the Japanese version, the three locations were changed as ROM bytes (0x14AFC1-0x14AFC2 = 00 26, 0x1F0000 = 01) and the menu opened.
   In room 0xBD (Mario's house), face north from (6,16) in front of the lamp, or north-east from (5,15), and press A.
 - Menu: EVENT / 데모 (demo) / 옵션 (option) → next / 어묵브리지 / 파타부대 → next / 광차이후 / 와인강
 - The black screen seen earlier when warping to room 0xBD was due to the arrival coordinates. The real entrance of this room is (2,16).

■ Room warps and the debug room [verified]
 - $00:3030 (16-bit) = current room number. The S-CPU writes it when passing a door or exit.
   e.g. shop 0x002F → outside the door 0x0017
 - Returning a value from a Mesen 2 write callback makes that value the one actually written.
   This was used to change the room number to the desired one when passing an exit, to warp.
   Writing it beforehand with emu.write has no effect because the game overwrites it.

     local T = 0x0000   -- destination room number
     emu.addMemoryCallback(function(addr, val)
       if addr == 0x3030 then return T & 0xFF else return (T >> 8) & 0xFF end
     end, emu.callbackType.write, 0x3030, 0x3031, emu.cpuType.snes, emu.memType.snesMemory)

 - Room number 0x0000 = debug room
   A "임시 WORLD MAP입니다. 말을 걸어서 가고 싶은 곳으로 가세요." ("This is a temporary WORLD MAP. Talk to go where you want.") banner, several Toads and Bowser.
   Each Toad reportedly sends you to save, Nimbus Land, Barrel Volcano and so on. [source]
 - Other rooms tried: 0x0045 cave map, 0x0001 blue screen, 0x00BD black screen
 - The arrival coordinates and direction come from the original exit data, so depending on the map the screen can look empty.
   The callback must be removed after one use. If left in place, every later room change goes to the same room.
 - Per-room NPC data pointers: file 0x148000 (16-bit × 512, an increasing table)
 - The North American debug room PAR 7FF40400 7FF40501 was not tried on the Japanese version.

■ Forcing battle formations [verified]
 - $7E:FA0E (16-bit) = formation number. Written when entering a battle.
   Changing it with the same kind of write callback as above (addresses 0x7EFA0E-0x7EFA0F) starts the battle with a different set of enemies.
   e.g. changing a field Goomba's original value 0x000E to 0x0022 or 0x0100 gave different formations.
 - $7E:0048 / $7E:D123 from overseas RAM maps were not written on entering battle in the Japanese version.

■ RAM [verified: those marked / the rest: sources and observations of the Japanese version agree]

  $00:3030     current room number (16-bit) [verified]
  $00:3112     menu open permission (writing FF lets the menu open where it is normally blocked) [verified]
  $7E:052A     SCENE number of the battle debug menu [verified]
  $7E:FA0E     battle formation number (16-bit) [verified]
  $7F:F800     Mario's stats (0x14 bytes) [verified: Lv1 HP 20/20]
               +0 level, +1 HP (16-bit), +3 max HP (16-bit), +5 speed, +6 attack, +7 defence,
               +8 magic attack, +9 magic defence, +0A experience (16-bit), +0C weapon, +0D armour, +0E accessory,
               +12 learned special bits
  $7F:F814 / F828 / F83C / F850   Peach / Bowser / Geno / Mallow
  $7F:F864     equipment inventory
  $7F:F882     item inventory (30 slots, empty FF)
  $7F:F8AF     coins (16-bit) [verified]
  $7F:F8B1 / F8B2   current FP / max FP [verified]

 - To see the item menu right away, write $00:3112 = FF and $7F:F882 = item number every frame and open the menu with X.
   (POKE="003112=FF;7FF882=60" of tools/run_seq.sh)
 - Event variables: $7000-$71FF used by the event scripts (16-bit variables, flag bits from $7040) are [source].
   S-CPU $00:7000 is BW-RAM $3000 (SA-1 $40:3000). (section 0) [verified]
 - The string "JAPANESE VER. by M.YOSHIOKA" is at $C3:0010. [verified]

■ Sources
 - TCRF: https://tcrf.net/Super_Mario_RPG:_Legend_of_the_Seven_Stars
 - Data Crystal RAM map: https://datacrystal.tcrf.net/wiki/Super_Mario_RPG:_Legend_of_the_Seven_Stars/RAM_map
 - smrpgpatchbuilder (event commands, variable ranges): https://github.com/pidgezero-one/smrpgpatchbuilder
```

## 8. Testing and screenshots

```text
 - Everything was automated with Mesen 2's --testrunner mode and Lua scripts.
   · Lua file I/O needs AllowIoOsAccess turned on in the Mesen settings.
   · Button input must be set with emu.setInput in the inputPolled event for the game to see it.
   · Savestates can only be saved/loaded inside a CPU execution callback, so this was deferred to the next instruction.
   (test/lib.lua, test/seq.lua)
 - Scenes that are hard to reach were made into new states by writing RAM values into existing savestates. (tools/make_states.sh)
   e.g. experience set to just before a level-up → level-up screen in the next battle
        an event flag set to "not seen yet" → the cutscene plays on re-entering the room
 - Showing any dialogue right away: a test-only ROM (build/harness.sfc)
   It hooks $C0:5809 and, if $7E:17F0 = $A55A, replaces the next dialogue opened with the ID in $7E:17F2.
   The desired dialogue was shown in place of a shopkeeper's line, to capture v1.0 and v1.1 under the same conditions.
   (test/harness/harness.asm, tools/py/dlg_shots.py)
 - Going to a particular place: a test-only ROM with one exit record changed
   The destination room number and arrival coordinates of the exit record of Bandit's Way 3 (room 0x4D) (file 0x1D34E2, 9 bytes) were changed
   to arrive at a chosen place, such as Moleville, facing a chosen direction. (tools/py/scene_rom.py)
 - When the mosaic during screen transitions broke screenshots, the screen was drawn directly from a VRAM dump. (tools/py/bgrender.py)
 - Dialogue regression check: confirms 0 dialogue changes outside the fix list (tools/py/verify_dialogue.py)
 - Logging execution points and forcing values: test/probe.lua (EXEC = log and save the screen when that address executes,
   POKE = write every frame, ONCE = write for one frame only, MAPCHECK = compare the memory correspondence of section 0)

■ Emulators (v1.2) [verified]
 - compat/lr.py: a small program that loads libretro cores directly and feeds them the same input. compat/run_all.sh runs
   the same scenarios on the Japanese ROM, v1.1 and v1.2 for each core. Mesen 2 reads the same scenario files with
   compat/mesen_run.lua. Results are in compat/results.txt.
   · new: power on, new game, mash A up to Bowser's Keep (9000 frames)
   · cont: continue a v1.1 save → battle a group of Spikeys → use a Yoshi Cookie for 3 turns
   · cont_long: same as cont, using a Yoshi Cookie for 30 turns
 - Save: 6 Yoshi Cookies were added (compat/make_save.py) to the BW-RAM taken from a Mesen 2 savestate (compat/dumpsrm.lua).
   Slot 1 is BW-RAM $0000-$07FF, and the 16-bit value at $07FC is
   the complement of the byte sum of $0000-$07FB. If it does not match, the slot shows as empty.

  emulator                result
  Mesen 2 2.1.1           new and cont to the end. In cont, all three ROMs show the same transformation message on the same frame as bsnes.
                          Yoshi Cookie message "버섯" from a savestate; 11 field menu regression cases pass.
                          Rerunning the same ROM gives some screens a few pixels apart (enemy and cursor motion), so ROMs were compared by message
  bsnes 115               new and cont to the end. Transformation message in cont: Japanese "カタクナール", v1.1 "BRACER",
                          v1.2 "단단해져라". The 14 new screens are the same for v1.1 and v1.2
  bsnes-hd beta 10.6      same as bsnes, except that in new the captures go black from the Bowser's Keep opening (mode 7). Same for the Japanese ROM
  Snes9x 1.63             new, cont and cont_long to the end. No transformation in 30 turns (same for the Japanese ROM).
                          All 301 screens are the same for v1.1 and v1.2
  Snes9x 2010 1.52.4      same as Snes9x
  Beetle Supafaust 1.29.0 3 transformations in cont_long, on the same frame for all three ROMs. v1.2 shows "단단해져라"
  Mesen-S 0.4.0           every run, including the Japanese ROM, ends with exit 139

 - The name spelling (셸 → 쉘) and menu characters (힐, 휠) fixed after the table was made were checked by rerunning new and cont on bsnes and Snes9x:
   all 84 screens were the same as the runs in the table.
 - Whether a transformation succeeds is random, so it differs by core. On the same core, the three ROMs gave the same result on the same frame.
 - Not tested on real hardware (an actual Super Famicom, a flash cartridge).
```

## 9. Other

```text
 - ROM header: file 0x7FC0 (SA-1, map mode $23, per-byte values in section 0)
   The checksum is at file 0x7FDC-0x7FDF (2-byte complement + 2-byte checksum)
   and was recomputed with asar's --fix-checksum=on. (v1.0 C88A → v1.1 6FCD → v1.2 2B3C)
 - The ROM size is the same 4MB as the original, and the SRAM size in the header and the save structure are unchanged.
   v1.1 and v1.0 save files work as they are.
 - Free space used (all 0 or 0xFF in the Japanese original)

  location                 use                                    left in the v1.2 ROM [verified]
  $C3:F000-$C3:F3FF        field menu code (originally 0xFF)      286 bytes from $C3:F2E2
  $C3:FC40-$C3:FFFF        battle menu, result window code (0xFF) 215 bytes from $C3:FF29
  $E2:B400-$E2:FFFF        new name tables, level-up/special screen/dialogue code, battle message and name banner code
                                                                  147 bytes from $E2:FF6D
  $C1:56BB-$C1:56BE        1C 38 entry (space left by the routine v1.2 replaced)   all used
  $C1:56F2-$C1:56F5        JSR $5769; RTL (same reason)                            all used
  $E4:9D00-$E4:9DFF        dialogue font extension, 32 glyphs     27 glyphs (5 used)
  $E4:EDD8 etc.            249 dynamic glyphs                     100 glyphs (below)
  $FE:F61C-$FE:F6FF        lengthened menu text                   205 bytes from $FE:F633

 - Dynamic glyphs fill the four FREE_RUNS stretches of tools/build.py in order.
   File 0x24EDD8 (4,648 bytes) is full, and 0x2511C2 (1,601 bytes) is used up to 0x251701.
   What remains is 10 glyphs from 0x251702, 61 glyphs at 0x252534 (1,484 bytes) and 29 glyphs at 0x251D48 (697 bytes). [computed]
   The battle renderer reads $E4:2B00 + 16 bits, so this cannot extend outside that range (file 0x242B00-0x252AFF).
 - Remaining byte counts were measured as the length of the 0 or 0xFF run from the end of each stretch.

 - asar caveat: writing a numeric address directly in a branch instruction (BRA $C16AD7 etc.) sometimes computed the relative offset wrongly.
   Branches go to labels in the same block, and assert pc() == ... checks the overwritten range.
 - Dialogue line splitting rules
   · A line does not exceed 22 cells.
   · 님/씨 after a name, as in "마리오님", is spaced, but kept attached if the line would exceed 22 cells.
   · "Obtained" messages are centred on the screen.
```

## 10. For the next person

```text
■ Not checked
 - The magic effect test menu (section 7): only the location to change was checked; it was not run.
 - EVT 3 and TEST of the battle debug menu (section 7)
 - The battle animation scripts were not all followed by command length to confirm there is no 63 02.
   (section 3 "Battle name banner": only byte pattern searches and analysis of the monster behaviour scripts)
 - Where a message using battle message control code 1C 37 (special name) is (section 3)

■ Known limits
 - The ROM cannot exceed 4MB. (section 3 "Why the ROM stays 4MB")
 - The dialogue engine's 2-byte prefixes are only $1D-$1F, so the dialogue font extension area (glyphs from 0x3E0) cannot be used in dialogue.
   If dialogue needs more new characters, more unused 2-byte codes must be found with textusage.py.
 - The field menu has 128 dynamic glyph cells, and at most 12 glyphs are collected in WRAM at a time.
 - Name length: 10 characters for items and specials, 8 for enemies (the cell sizes of the original tables)
 - No free space to move the battle message and "what's on your mind" text into was found, so they only grew into the 0 bytes after each string.
 - The menu text area contains data no pointer points to, so its strings must not be moved.

■ Tool versions used [verified]
 - asar 1.91 (tools/asar --version)
 - Mesen 2.1.1 (build 137ae7ce3bf3f539d007e2c4ef3cb3b6c97672a1)
 - Python 3.9.6, Pillow 11.3.0
 - Galmuri11 Condensed 2.404
 - libretro cores for compatibility checks: bsnes 115, bsnes-hd beta 10.6, Snes9x 1.63, Snes9x 2010 1.52.4,
   Beetle Supafaust 1.29.0, Mesen-S 0.4.0 (section 8)
```

## 11. Included files

```text
Super_Mario_RPG_K_v1_2_tools.zip
 - README.txt                : build instructions
 - ANALYSIS.txt              : this document
 - tools/make.sh             : the whole build (name/glyph data → dialogue relocation → asar)
 - tools/build.py            : generates name tables, dynamic glyphs, dialogue font reuse, level-up/special screen strings
 - tools/py/dlg_rewrite.py   : refills the dialogue and other text ($1B conversion, centring, end code repair)
 - tools/py/dialogue.py      : reads the dialogue pointer table
 - tools/py/textfix.py       : applies dialogue fixes (context checks, particle correction)
 - tools/py/textusage.py     : surveys the 2-byte codes used in text
 - tools/py/dump_text.py     : text dump
 - tools/py/render_jp.py     : draws the Japanese original with the dialogue font
 - tools/py/verify_dialogue.py, verify_menu.py : regression checks
 - tools/py/make_ips.py      : IPS creation (headerless / headered)
 - tools/py/scene_rom.py     : builds test ROMs with changed exits
 - tools/py/dlg_shots.py, patchnote_shots.py, patchnote_compose.py, shotcmp.py, bgrender.py etc.
                             : screenshot capture, comparison, VRAM rendering
 - tools/py/dis65816.py      : a simple 65816 disassembler
 - tools/make_harness.sh, make_states.sh, run_seq.sh, test_menu.sh : test ROMs, savestates, Mesen runs
 - src/main.asm              : all hook code (asar)
 - test/harness/harness.asm  : test-only dialogue substitution hook
 - test/lib.lua, seq.lua, poke_state.lua, warp_seq.lua : Mesen 2 test scripts
 - test/probe.lua            : execution point logging, value forcing, memory correspondence comparison (section 8)
 - compat/                   : emulator compatibility checks (lr.py, mesen_run.lua, run_all.sh, scenarios s_*.txt,
                               make_save.py, dumpsrm.lua, results.txt) (section 8)
 - data/items_ko.json, skills_ko.json, enemies_ko.json : Korean names (165 items, 27 specials, 232 enemies)
 - data/*_en.json            : v1.0 English names
 - data/name_overrides.json  : name exceptions
 - data/dialogue_names.json  : English names in dialogue → Korean
 - data/dialogue_fixes.json  : dialogue review fix list
 - data/honorifics.json      : 님/씨 spacing targets
 - data/tbl/                 : v1.0 code tables (korTBL = dialogue font, korTBL2 = menu font),
                               menu_font_audit.txt (menu font codes checked by eye)
 - tools/py/check_menu_names.py : checks every name against the glyphs the menus draw (last build step)
 - tools/fonts/galmuri/      : Galmuri11 Condensed (SIL OFL, LICENSE.txt included)
 - v1.0/Super Mario RPG (K) (V1.0).ips : v1.0 patch (build input)

Notes
 - ROM files, asar and Mesen are not included.
 - To build, put the Japanese original with the v1.0 IPS applied at rom/smrpg_kr_v1.sfc,
   put the asar 1.91 executable at tools/asar, and run zsh tools/make.sh.
   (Result build/test.sfc, CRC32 05DBCBE6) The detailed steps are in README.txt.
 - tools/py/patchnote_compose.py uses a macOS system font path, so change the FONT path on other systems.
 - The test scripts assume tools/Mesen.app (Mesen 2) and the savestates in test/states/.
   The savestates are not included.
```
