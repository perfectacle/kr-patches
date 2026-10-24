; Korean item names for the field menu (Super Mario RPG JP + Korean V1.0).
;
; Names come from a new table of 16-bit characters. Codes below $0100 are the
; existing 1-byte menu font; codes with bit 15 set are glyphs from KoGlyphs that
; are not in the menu font. Those are converted with the game's own outline
; routine and uploaded during NMI to VRAM $6000-$7FFF, which BG1 can reach as
; tiles $200-$2FF and which no field-menu screen references. The menu reloads
; that VRAM region on open, so the slot cache is reset at the same time.

sa1rom

; WRAM $7E:0C00-$17FF is never written by the game in menus (including the
; held-item sprite, which uses $F580-$F8FF), battle or dialogue.
!cnt2   = $0C00     ; slots in use * 2
!pend   = $0C02     ; glyphs staged but not uploaded yet
!tmpg   = $0C04
!attr   = $0C06
!cells  = $0C08
!ptr    = $0C0A
!lock   = $0C0C     ; nonzero while Stage is filling an entry; NMI must wait
!hcnt   = $0C12     ; dynamic glyphs placed for the held-item name
!pslots = $0C20     ; VRAM word address of each staged glyph (12 words)
!table  = $0C40     ; glyph index held by each slot (128 words)
!stage  = $0D40     ; 12 staged glyphs x 64 bytes (two 4bpp tiles)
!stagemax = 12
!plen   = $1040     ; byte count of each staged glyph (12 words)
!tmpq   = $1058
!tmpl   = $105A
; Name entry and file select (src/name_entry.asm)
!ne_n     = $1200   ; characters committed
!ne_ch    = $1202   ; 8 words, their codes (menu-font code, or $8000 | name glyph)
!ne_sp    = $1212   ; states on the composing stack (0 = not composing)
!ne_stk   = $1214   ; 6 states x 4 bytes: initial, medial, final, unused
!ne_state_end = $1230
!ne_save  = $1230   ; copy of $1200-$122F, restored when an input is refused
!ne_cellg = $1260   ; 8 words, name glyph held by each name cell's slot ($FFFF = none)
!ne_gslot = $1270   ; next grid slot
!ne_t0    = $1272
!ne_t1    = $1274
!ne_t2    = $1276
!ne_t3    = $1278
!ne_t4    = $127A
!ne_len   = $127C
!ne_vowel = $127E   ; medial of the vowel being typed
!fs_cnt   = $1280   ; file-select slots in use * 2
!fs_tab   = $1282   ; 16 words, name glyph held by each file-select slot

!font_tmp = $F500   ; input/output buffer of the outline routine

!item_table = $41FC     ; bank $FA
!enemy_table = $8C11    ; bank $F9, 8 bytes per enemy
!skill_table = $137F    ; bank $FA, same entry format as items
!skill_count = $001B    ; ally specials; later entries are enemy attacks, already Korean in V1.0
!tbloff = $0C0E         ; offset of the name table from KoNames (field menu)
!esc_first  = $001C     ; $1C-$1F + low byte = dynamic glyph in a $40:6800 name buffer
!glyph_base = $E42B00   ; battle renderer reads glyphs relative to this
; KoCopy reuses the original routine's direct-page variables: the source
; pointer at $9D-$9F and the byte count at $84.
!kc_src     = $9D
!kc_n       = $84

; Menu routines this patch relies on (bank C3)
!blank_name    = $795C
!put_name      = $79C5
!outline_glyph = $6869
!run_nmi_tasks = $013E

!slot_vram_word = $3000     ; VRAM $6000 (bytes) as a word address
!slot_tile      = $0200     ; BG1 tile number of slot 0

org $C37990
    JMP DrawItemName

; Menu NMI handler: call the glyph uploader in place of the task runner (it
; runs the tasks first).
org $C30102
    JSR NmiUpload

; Item carried to a character in the menu: its name is drawn as a sprite from
; the converted menu font ($7E:8000 + (code - $20) * 32).
org $C32078
    JSR HeldName

org $C3799D
    JMP DrawSkillName

; Start of the routine that builds the menu font when a menu opens.
org $C36D74
    JSR ResetSlots
    NOP #2

org $C3F000
; In: $70 = item id, $62 = tilemap offset, $9D = palette, $9E = offset of the
; lower tile row. DB = $7E, X/Y 16-bit. Mirrors $795C + $79C5.
DrawSkillName:
    REP #$20
    LDA.w #KoSkills-KoNames
    BRA DrawName

DrawItemName:
    REP #$20
    LDA #$0000
DrawName:
    STA !tbloff
    SEP #$20
    PHX
    PHY
    LDA $70
    CMP #$FF
    BNE .item
    JSR !blank_name
    JSR !put_name
    PLY
    PLX
    RTS

.item
    REP #$20
    LDA $72
    PHA
    LDA $70
    PHA
    AND #$00FF
    STA !tmpg
    ASL
    ASL
    STA !ptr
    ASL
    ASL
    CLC
    ADC !ptr
    ADC !tmpg
    ADC !tbloff
    STA !ptr            ; id * 21 within the selected table

    SEP #$20
    LDA $9D
    ASL
    ASL
    ORA #$20
    XBA
    LDA #$00
    REP #$20
    STA !attr
    LDA $9E
    AND #$00FF
    STA $72             ; ($72),Y addresses the lower tile row

    LDY $62
    LDX !ptr
    LDA.l KoNames,X
    AND #$00FF
    JSR PutStatic
    INX
    LDA #$000A
    STA !cells
.loop
    LDA.l KoNames,X
    BMI .dynamic
    JSR PutStatic
    BRA .next
.dynamic
    AND #$7FFF
    PHX
    PHY
    JSR Alloc
    PLY
    PLX
    ASL
    ORA #!slot_tile
    JSR PutTile
.next
    INX
    INX
    DEC !cells
    BNE .loop

    STY $62
    PLA
    STA $70
    PLA
    STA $72
    SEP #$20
    PLY
    PLX
    RTS

PutStatic:
    SEC
    SBC #$0020
    ASL
PutTile:
    ORA !attr
    STA $0000,Y
    INC
    STA ($72),Y
    INY
    INY
    RTS

; In: A = glyph index. Out: A = slot. Clobbers X/Y.
Alloc:
    STA !tmpg
    LDX #$0000
.find
    CPX !cnt2
    BCS .new
    LDA !table,X
    CMP !tmpg
    BEQ .hit
    INX
    INX
    BRA .find
.hit
    TXA
    LSR
    RTS
.new
    CPX #$0100
    BCC .room
    ; Out of slots: start over. Names already on screen that use reused slots
    ; would show the new glyph, which only happens past 128 distinct glyphs.
    JSR WaitFlush
    LDX #$0000
.room
    LDA !tmpg
    STA !table,X
    TXA
    INC
    INC
    STA !cnt2
    TXA
    LSR
    PHA
    JSR Stage
    PLA
    RTS

; In: A = slot, !tmpg = glyph index.
Stage:
    ASL
    ASL
    ASL
    ASL
    ASL
    CLC
    ADC #!slot_vram_word
    PHA
    LDA !tmpg
    ASL
    TAX
    LDA.l KoGlyphOffs,X
    TAX
    LDY #$0000
.copy
    LDA.l !glyph_base,X
    STA !font_tmp,Y
    INX
    INX
    INY
    INY
    CPY #$0018
    BCC .copy
    LDA #$0000
.clear
    STA !font_tmp,Y
    INY
    INY
    CPY #$0040
    BCC .clear

    JSR !outline_glyph
    PLA
    LDY #$0040

; In: A = VRAM word address, Y = $40 (two 4bpp tiles) or $20 (two 2bpp
; tiles), font_tmp = output of the outline routine (two 2bpp tiles, top and
; bottom). A/X/Y 16-bit.
QueueTmp:
    STA !tmpq
    STY !tmpl
    LDA !pend
    CMP.w #!stagemax
    BCC +
    JSR WaitFlush
+
    INC !lock
    LDA !pend
    XBA
    LSR
    LSR
    TAX                 ; pend * 64
    LDY #$0000
    LDA !tmpl
    CMP #$0040
    BNE .two
    ; 4bpp with planes 2/3 cleared, because the slot area holds other graphics.
.out
    LDA !font_tmp,Y
    STA !stage,X
    LDA !font_tmp+16,Y
    STA !stage+32,X
    LDA #$0000
    STA !stage+16,X
    STA !stage+48,X
    INX
    INX
    INY
    INY
    CPY #$0010
    BCC .out
    BRA .queued
.two
    LDA !font_tmp,Y
    STA !stage,X
    INX
    INX
    INY
    INY
    CPY #$0020
    BCC .two
.queued
    LDA !pend
    ASL
    TAX
    LDA !tmpq
    STA !pslots,X
    LDA !tmpl
    STA !plen,X
    INC !pend
    STZ !lock
    RTS

WaitFlush:
    PHP
    REP #$20
-
    LDA !pend
    BNE -
    PLP
    RTS

; Runs from the menu NMI right after the game's own NMI tasks. Staged glyphs
; are uploaded here instead of through a task slot: the slot helper ($015B)
; plays a sound and gives up when all four slots are busy (e.g. Toad's menu
; tutorial), which left glyphs unuploaded and changed the music.
NmiUpload:
    JSR !run_nmi_tasks
    PHP
    REP #$30
    LDA.l $7E0000+!pend
    BEQ .exit
    LDA.l $7E0000+!lock
    BNE .exit           ; Stage is filling an entry; retry next frame
    SEP #$20
    LDA #$80
    STA $2115
    LDA #$01
    STA $4300
    LDA #$18
    STA $4301
    LDA #$7E
    STA $4304
    REP #$20
    LDX #$0000
.loop
    TXA
    LSR
    CMP.l $7E0000+!pend
    BCS .done
    LDA.l $7E0000+!pslots,X
    STA $2116
    TXA
    ASL
    ASL
    ASL
    ASL
    ASL
    CLC
    ADC #!stage
    STA $4302
    LDA.l $7E0000+!plen,X
    STA $4305
    SEP #$20
    LDA #$01
    STA $420B
    REP #$20
    INX
    INX
    BRA .loop
.done
    LDA #$0000
    STA.l $7E0000+!pend
.exit
    PLP
    RTS

; Fills $0994/$0995 like $795C, from KoNames. Codes $00-$1F wrap to
; $7E:9C00-$9FFF in the sprite builder, so dynamic glyphs are converted there.
!held_glyphs = $9C00
HeldName:
    SEP #$20
    LDA $70
    CMP #$FF
    BNE +
    JMP !blank_name
+
    REP #$30
    LDA $70
    AND #$00FF
    STA !tmpg
    ASL
    ASL
    STA !ptr
    ASL
    ASL
    CLC
    ADC !ptr
    ADC !tmpg
    TAX                 ; id * 21
    SEP #$20
    LDA.l KoNames,X
    STA $0995
    LDA #$0B
    STA $0994
    REP #$20
    STZ !hcnt
    LDY #$0001
.loop
    LDA.l KoNames+1,X
    BMI .dynamic
    SEP #$20
    STA $0995,Y
    REP #$20
    BRA .next
.dynamic
    AND #$7FFF
    PHX
    PHY
    JSR HeldGlyph
    PLY
    PLX
    SEP #$20
    STA $0995,Y
    REP #$20
.next
    INX
    INX
    INY
    CPY #$000B
    BCC .loop
    SEP #$20
    RTS

; In: A = glyph index. Converts it to $7E:9C00 + n*32 and returns code n.
HeldGlyph:
    STA !tmpg
    ASL
    TAX
    LDA.l KoGlyphOffs,X
    TAX
    LDY #$0000
.copy
    LDA.l !glyph_base,X
    STA !font_tmp,Y
    INX
    INX
    INY
    INY
    CPY #$0018
    BCC .copy
    LDA #$0000
.clear
    STA !font_tmp,Y
    INY
    INY
    CPY #$0040
    BCC .clear
    JSR !outline_glyph
    LDA !hcnt
    ASL
    ASL
    ASL
    ASL
    ASL
    TAX
    LDY #$0000
.out
    LDA !font_tmp,Y
    STA !held_glyphs,X
    INX
    INX
    INY
    INY
    CPY #$0020
    BCC .out
    LDA !hcnt
    INC !hcnt
    RTS

ResetSlots:
    REP #$20
    LDA #$0000
    STA.l $7E0000+!cnt2
    STA.l $7E0000+!pend
    STA.l $7E0000+!lock
    STA.l $7E0000+!fs_cnt
    LDX #$0000
    RTS

; In: X = offset from KoNames of a $0000-terminated string in the name
; encoding, Y = tilemap offset, $9D = palette. DB = $7E. Draws it like
; DrawName (lower tile row at +$40). Out: Y = offset after the text.
KoDrawStr:
    PHP
    REP #$30
    LDA $72
    PHA
    SEP #$20
    LDA $9D
    ASL
    ASL
    ORA #$20
    XBA
    LDA #$00
    REP #$20
    STA !attr
    LDA #$0040
    STA $72
.loop
    LDA.l KoNames,X
    BEQ .done
    BMI .dynamic
    JSR PutStatic
    BRA .next
.dynamic
    AND #$7FFF
    PHX
    PHY
    JSR Alloc
    PLY
    PLX
    ASL
    ORA #!slot_tile
    JSR PutTile
.next
    INX
    INX
    BRA .loop
.done
    PLA
    STA $72
    PLP
    RTL

assert pc() <= $C3F400

; ---------------------------------------------------------------------------
; Battle menus (SA-1). $C1:6A3F draws 11 characters read through the pointer
; at $308C into a bitmap, taking glyphs from $E42B00 + (code - $20) * 24.
; Characters read from the item-name table are translated to KoNames; glyphs
; outside the menu font come back as !dyn_mark with the glyph index in Y.

!dyn_mark   = $001F     ; unused code in the menu font, below the printable range

org $C16AC7
    JSL KoFetch
    BRA +
    NOP #10
+
assert pc() == $C16AD7

org $C16C6D
    JML KoCopy

; Battle text ($C1:5680, drawn with the dialogue font): control codes 1C 31 and
; 1C 37 insert the name of item $FA06 / special $FA14, read straight from the
; original tables, which still hold the V1.0 English names (Yoshi Cookie:
; "몬스터는 MUSHROOM 모습이 됐다!"). Feed the dialogue-encoded Korean names to the
; interpreter's own glyph routine ($5769, A = code; 2-byte codes as
; (prefix - $1C) << 8 | low, so prefix $20 reaches the font extension).
org $C156A8
    LDA $FA06
    JSL KoBtlItem
-
    JSL KoBtlNext
    BCS +
    JSR $5769
    BRA -
+
BtlTextRts:
    RTS
; Code 1C 38 did what 1C 30 does (the 1C table repeats its first entry for
; nibbles 8-F). It now also draws the name banner text built by KoBanText.
BtlCode38:
    JML KoBtlBanner
assert pc() <= $C156BF

org $C15693           ; entry 8 of the 1C table at $C1:5683
    dw BtlCode38

org $C156DF
    LDA $FA14
    JSL KoBtlSkill
-
    JSL KoBtlNext
    BCS +
    JSR $5769
    BRA -
+
    RTS
; $5769 for KoBtlBanner, which runs in bank $E2
BtlGlyph:
    JSR $5769
    RTL
assert pc() <= $C156F6

; Name banner of battle animation command $63 ($C2:4131): argument 1 shows
; special $E0 and argument 2 item $E0, read from the original tables
; (English since V1.0 for items and ally specials). Point the banner at a
; short text built in WRAM instead (see KoBanText).
org $C241D5
    JSL KoBanSkill
    JMP $0C53
assert pc() <= $C241E3

org $C24209
    JSL KoBanItem
    JMP $0C53
assert pc() <= $C24217

; Battle result window ("<item> 획득"): the name is copied to $7E:05E0 and drawn
; with the dialogue font ($E44000 + (code - $20) * 24). Copy the dialogue-encoded
; Korean name instead, and read 2-byte codes as one glyph.
; Battle result window. The game picks one of two window sizes (with or
; without a dropped item). A short Korean item name fits on the "item"
; label's line, so that case gets a window one line shorter:
;   0  $3F8E set: the game's large window
;   1  no item: the game's small window
;   2  short item name: on the label's line; shorter window
;   3  long item name: on the line below the label; the game's large window
; The name is right-aligned to the numbers above in every case.
; Window = [$3F90 - r, $3F92 + r + 1] x [$3F94 - r, $3F94 + r + 1] with
; r = 3 * $3FB4 - 3 (measured).
!res_name_pos  = $0398  ; tilemap position the game gives the item name
!res_label_row = $0300  ; row of the "item" label
!res_name_row  = $0380  ; row the game gives the item name
!res_right     = 186    ; numbers' right edge (180) + 2 px glyph gap + 4 to round to the nearest tile
!res_short     = 5      ; longest name that fits beside the label
; asar -Dres_ui=0 builds the game's own layout (Korean names only), for
; before/after screenshots of this change.
!res_ui ?= 1

if !res_ui
org $C17161
    JSL KoResultGeom
    BRA +
org $C17189
+
endif

; Level-up screen (SA-1). Code $03 in its text inserts a special's name
; from the item-format table (English in V1.0); its glyph list entries are
; code | class << 8, and the renderer reads glyph (code - $20) of the
; dialogue font. Names now come from KoLvSkills, and a 2-byte syllable is
; stored as its prefix in the class byte, which KoLvAttr turns back into the
; glyph index.
org $C2D3CF
    JSL KoLvSkill
    BRA +
org $C2D415
+
org $C2D4EA
    JSL KoLvAfterNum
assert pc() == $C2D4EE
incsrc "../build/lvtext.asm"

org $C2D734
    JSL KoLvAttr
    TAX
    NOP #2
assert pc() == $C2D73B

; Field special menu: the name is drawn in a 4-cell field and menu text $1C
; follows it, so short names left a gap. The text now starts right after the
; name.
org $C377F6
    JSL KoSpecialHint
    NOP
assert pc() == $C377FB

; The hint reads "<name>는 / 레벨 N이 되면 / 새로운 기술을 배웁니다". Of the
; screen's text list ($C3:33B5) only $1C (now "는") is drawn; KoHintLines draws
; the rest, and the level number moves to line 2.
!hint_lv    = $5D88     ; tilemap offsets in $7E: "레벨" on line 2
!hint_num   = $5D8E     ; the level's two cells, right-aligned
!hint_line3 = $5E04
org $C333B5
    db $01
org $C335F0
    dw !hint_num
org $FEF0A9
    db $76, $00         ; menu text $1C = "는"

; Shop menu text $4F "소지한 갯수": menu-font text, so the dialogue-encoded
; fixes in dialogue_fixes.json cannot reach it.
org $FEF2B9
    db $63              ; 갯 -> 개

org $C1779A
    REP #$30
    JSL KoResultName
    JMP $7875
assert pc() <= $C177DA

org $C1787E
    JSL KoResultChar
    NOP #3
assert pc() == $C17885

; Dialogue code $1A inserts the name of item $0234: the original copies the
; table bytes to $7E:2D00 and continues the dialogue from there.
; Control code $1B was unused (handler at $624E just continues); send it to
; the item-name handler, which tells the two apart by $80.
org $C06896
    dw $60A6

org $C060B2
    PHB                 ; the engine pulls this at $C0:5F46 (the original pushed it before its MVN)
    JSL KoDlgName
    LDY #$2D00
    JML $C05F1B

org $C16AFA
    PHA                 ; balanced by the PLA after the glyph is drawn
    JSL KoGlyphX
    BRA +
    NOP #8
+
assert pc() == $C16B09

org $C3FC40
; In: X = address of the character in bank $FA (or $40 if $3090 is set).
; Out: A = character code, Y = glyph index when A = !dyn_mark. Clobbers X.
KoFetch:
    LDA.l $003090
    BEQ .fa
    LDA.l $400000,X
    AND #$00FF
    CMP #!esc_first
    BCC .ret
    CMP #!esc_first+4
    BCS .ret
    ; Escape byte + low byte: dynamic glyph ((esc - !esc_first) << 8) | low.
    SEC
    SBC #!esc_first
    XBA
    PHA
    LDA.l $400001,X
    AND #$00FF          ; the high byte of that read is the next character
    ORA $01,S
    TAY
    PLA
    LDA.l $00308C
    INC
    STA.l $00308C
    LDA #!dyn_mark
.ret
    RTL
.fa
    CPX #!item_table
    BCC .skill
    CPX #!item_table+(256*15)
    BCS .orig
    PEA $0000
    TXA
    SEC
    SBC #!item_table
    BRA .lookup
.skill
    CPX #!skill_table
    BCC .orig
    CPX #!skill_table+(!skill_count*15)
    BCS .orig
    PEA.w KoSkills-KoNames
    TXA
    SEC
    SBC #!skill_table
    BRA .lookup
.orig
    LDA.l $FA0000,X
    RTL
.lookup                 ; A = offset in the 15-byte table, table offset on the stack
    LDY #$0000
.div
    CMP #$000F
    BCC .split
    SBC #$000F
    INY
    BRA .div
.split                  ; A = position in the entry, Y = item id
    PHA
    PHY
    TYA
    ASL
    ASL
    PHA
    ASL
    ASL
    CLC
    ADC $01,S
    ADC $03,S
    ADC $07,S
    STA $01,S           ; id * 21 within the selected table
    LDA $05,S
    BEQ .icon
    CMP #$000B
    BCS .space
    ASL
    DEC
    CLC
    ADC $01,S
    TAX
    LDA.l KoNames,X
    BMI .dynamic
    AND #$00FF
    BRA .done
.icon
    LDA $01,S
    TAX
    LDA.l KoNames,X
    AND #$00FF
    BRA .done
.space
    LDA #$0020
    BRA .done
.dynamic
    AND #$7FFF
    TAY
    LDA #!dyn_mark
.done
    PLX
    PLX
    PLX
    PLX
    RTL

; In: A = character code, Y = glyph index if A = !dyn_mark.
; Out: X = glyph offset from $E42B00.
KoGlyphX:
    CMP #!dyn_mark
    BNE .static
    TYA
    ASL
    TAX
    LDA.l KoGlyphOffs,X
    TAX
    RTL
.static
    SEC
    SBC #$0020
    JSR .times24
    TAX
    RTL
.times24
    ASL
    ASL
    ASL
    PHA
    ASL
    CLC
    ADC $01,S
    PLX                 ; drop the temporary without touching A
    RTS


; In: A = item id (16-bit). Copies its dialogue-encoded name to $7E:05E0.
KoResultName:
    PHY                 ; tilemap position from the caller
    AND #$00FF
    ASL
    PHA
    ASL
    ASL
    CLC
    ADC $01,S
    ASL
    CLC
    ADC $01,S           ; id * 22
    TAX
    PLA
    LDY #$0000
    SEP #$20
-
    LDA.l KoDlgNames+1,X
    PHX
    TYX
    STA.l $7E05E0,X
    PLX
    INX
    INY
    CMP #$00
    BNE -
    REP #$20
    PLY
if !res_ui == 0
    RTL
endif
    CPY.w #!res_name_pos
    BNE .done
    JSL KoResultLayout
    CMP.w #$0002
    BEQ +
    LDA.w #!res_name_row
    BRA ++
+
    LDA.w #!res_label_row
++
    PHA                 ; row of the name
    LDX #$0000
    LDY #$0000          ; glyphs
-
    LDA.l $7E05E0,X
    AND #$00FF
    BEQ +
    INX
    INY
    CMP #$001D
    BCC -
    CMP #$0020
    BCS -
    INX                 ; 2-byte glyph
    BRA -
+
    TYA
    ASL
    PHA
    ASL
    ASL
    CLC
    ADC $01,S           ; glyphs * 10 px
    STA $01,S
    LDA.w #!res_right
    SEC
    SBC $01,S
    PLX
    LSR
    LSR
    LSR                 ; first tile column
    ASL
    CLC
    ADC $01,S
    PLX
    TAY
.done
    RTL

; Out: A = layout (see the result window note). Reads $3F8E and $FA06
; through the caller's DB.
KoResultLayout:
    PHX
    LDA $3F8E
    BNE .big
    LDA $FA06
    CMP.w #$0100
    BCS .none
    AND #$00FF
    ASL
    PHA
    ASL
    ASL
    CLC
    ADC $01,S
    ASL
    CLC
    ADC $01,S           ; id * 22
    TAX
    PLA
    LDA #$0000
    PHA                 ; glyphs
-
    LDA.l KoDlgNames+1,X
    AND #$00FF
    BEQ +
    INX
    CMP #$001D
    BCC ++
    CMP #$0020
    BCS ++
    INX
++
    LDA $01,S
    INC
    STA $01,S
    BRA -
+
    PLA
    CMP.w #!res_short+1
    BCS .long
    LDA.w #$0002
    PLX
    RTL
.long
    LDA.w #$0003
    PLX
    RTL
.none
    LDA.w #$0001
    PLX
    RTL
.big
    LDA #$0000
    PLX
    RTL

; Replaces the game's choice of window size.
KoResultGeom:
    PHX
    JSL KoResultLayout
    ASL
    ASL
    ASL                 ; 8 bytes per layout
    TAX
    LDA.l .geo,X
    STA $3F90
    LDA.l .geo+2,X
    STA $3F92
    LDA.l .geo+4,X
    STA $3F94
    LDA.l .geo+6,X
    STA $3FB4
    STA $3FB6
    PLX
    RTL
.geo                    ; $3F90, $3F92, $3F94, $3FB4
    dw $007A, $0092, $0056, $0012
    dw $0065, $00A7, $0044, $000B
    dw $0071, $009B, $004E, $000F
    dw $007A, $0092, $0056, $0012

; In: X = index into $7E:05E0. Out: A = glyph index + $20 (what the drawer
; expects), X advanced, flags set from A.
KoResultChar:
    LDA.l $7E05E0,X
    INX
    AND #$00FF
    CMP #$001D
    BCC .done
    CMP #$0020
    BCS .done
    SEC
    SBC #$001D
    XBA                 ; (prefix - $1D) * 256
    PHA
    LDA.l $7E05E0,X
    INX
    AND #$00FF
    CLC
    ADC $01,S
    ADC #$00E0+$20      ; 2-byte glyphs start at index $E0
    STA $01,S
    PLA                 ; Y holds the caller's draw position, keep it
.done
    ORA #$0000          ; the caller tests Z for the terminator
    RTL

; $C1:6C6D copies a name from [$9D] (Y bytes, stops at 0) to $40:6800+X before
; the battle renderer draws it from there. Names from the item or enemy table
; are written in Korean instead, dynamic glyphs as two bytes.
KoCopy:
    PHX
    PHY
    LDA $9F
    AND #$00FF
    CMP #$00F9
    BEQ .enemy
    CMP #$00FA
    BEQ .item
.orig
    PLY
    PLX
    SEP #$20
    STY $84
    JML $C16C71
.enemy
    LDA $9D
    SEC
    SBC #!enemy_table
    BCC .orig
    CMP #$0800
    BCS .orig
    BIT #$0007
    BNE .orig
    ASL                 ; id * 16
    CLC
    ADC.w #KoEnemies
    STA !kc_src
    LDA.w #KoEnemies>>16
    STA !kc_src+2
    PLY
    PLX
    TYA
    BRA .chars
.item
    LDA $9D
    SEC
    SBC #!item_table
    BCC .orig
    CMP #$0F00
    BCS .orig
    LDY #$0000
-
    CMP #$000F
    BCC +
    SBC #$000F
    INY
    BRA -
+
    CMP #$0002
    BCS .orig           ; only whole names (with or without the icon)
    PHA                 ; 0 = starts at the icon, 1 = name only
    TYA
    ASL
    ASL
    PHA
    ASL
    ASL
    CLC
    ADC $01,S
    STA $01,S
    TYA
    CLC
    ADC $01,S           ; id * 21
    CLC
    ADC.w #KoNames
    STA !kc_src
    LDA.w #KoNames>>16
    STA !kc_src+2
    PLA
    PLA                 ; 0 = icon first
    PLY
    PLX
    CMP #$0000          ; PLX set the flags
    BNE .noicon
    ; icon byte, then the 16-bit characters
    SEP #$20
    LDA [!kc_src]
    STA.l $406800,X
    REP #$20
    INX
    DEY
.noicon
    INC !kc_src
    TYA
.chars                  ; A = characters to write, !kc_src -> u16 chars
    STA !kc_n
    BEQ .done
-
    LDA [!kc_src]
    BMI .dynamic
    SEP #$20
    STA.l $406800,X
    REP #$20
    INX
    BRA .next
.dynamic
    AND #$03FF
    XBA                 ; A = low:esc index
    CLC
    ADC.w #!esc_first
    SEP #$20
    STA.l $406800,X     ; escape
    XBA
    STA.l $406801,X     ; low byte
    REP #$20
    INX
    INX
.next
    INC !kc_src
    INC !kc_src
    DEC !kc_n
    BNE -
.done
    JML $C16C82

assert pc() <= $C40000

org $E2B400
KoNames:
    incbin "../build/names.bin"
KoSkills:
    incbin "../build/skills.bin"
KoEnemies:
    incbin "../build/enemies.bin"
KoDlgNames:
    incbin "../build/dlgnames.bin"
KoParticles:
    incbin "../build/particles.bin"
KoLvSkills:
    incbin "../build/lvskills.bin"
KoLvIga:
    db $28, $91, $29, $60, $00     ; "(이)가" in the dialogue font
!lv_i    = $0091
!lv_ga   = $0060
!lv_eul  = $008F
!lv_reul = $0076

; Replaces SEP #$20 / TDC / LDA $70 at the start of the menu text drawer.
KoSpecialHint:
    SEP #$20
    LDA $70
    CMP #$1C
    BNE .done
    JSR KoHintLines
    PHX
    LDX #$0000
-
    LDA.l $000995,X     ; the name drawn before this text
    CMP #$20
    BEQ +
    INX
    CPX #$0004
    BNE -
+
    REP #$20
    TXA
    SEC
    SBC #$0004          ; empty cells left of the 4-cell name field (-n)
    BEQ +
    PHY
    PHA
    ASL
    CLC
    ADC $62
    STA $62
    ; The text now ends n cells earlier; blank the n old tiles after it.
    LDA.l $FEEF00+($1C*2)
    TAX
    LDY #$0000
-
    LDA.l $FEF000,X
    AND #$00FF
    BEQ ++
    INX
    INY
    BRA -
++
    TYA                 ; text length in cells
    ASL
    CLC
    ADC $62
    TAY
    SEP #$20
    LDA $9D
    ASL
    ASL
    ORA #$20
    XBA
    LDA #$00            ; space tile with the text's attributes
    REP #$20
    PLX                 ; -n
-
    STA $0000,Y
    STA $0040,Y
    INY
    INY
    INX
    BNE -
    PLY
+
    SEP #$20
    PLX
.done
    TDC
    LDA $70
    RTL

; Runs before text $1C, after the name and the level number are drawn.
KoHintLines:
    PHP
    REP #$30
    PHX
    PHY
    LDY #!hint_lv
    LDX.w #KoHintLv-KoNames
    JSL KoDrawStr
    ; Menu-font tile = (code - $20) * 2, so the ones digit is tile / 2 - $10.
    LDA !hint_num+2
    AND #$03FF
    LSR
    SEC
    SBC #$0010
    ASL
    TAX
    LDY #!hint_num+4
    LDA !hint_num
    AND #$03FF
    BNE +
    ; One digit: move it next to "레벨 ".
    LDA !hint_num+2
    STA !hint_num
    LDA !hint_num+$42
    STA !hint_num+$40
    LDY #!hint_num+2
+
    LDA.l KoHintIga,X
    TAX
    JSL KoDrawStr
    LDY #!hint_line3
    LDX.w #KoHintLine3-KoNames
    JSL KoDrawStr
    PLY
    PLX
    PLP
    RTS

; 이/가 after the digit 0-9 (영 일 이 삼 사 오 육 칠 팔 구): string offsets.
KoHintIga:
    dw KoHintI-KoNames, KoHintI-KoNames, KoHintGa-KoNames, KoHintI-KoNames, KoHintGa-KoNames
    dw KoHintGa-KoNames, KoHintI-KoNames, KoHintI-KoNames, KoHintI-KoNames, KoHintGa-KoNames
incsrc "../build/hint.asm"

; In: A = special id. Adds the name's glyphs to the level-up glyph list like
; $C2:D6A3 does for one character (fixed 10 px advance).
KoLvSkill:
    CMP.w #!skill_count
    BCS .done
    ASL
    ASL
    ASL
    ASL
    TAX
    LDA.l KoLvSkills,X
    AND #$00FF
    PHA                 ; bit 7: final consonant
    AND #$007F
    STA $E0             ; bytes left
    INX
.next
    LDA $E0
    BEQ .particle
    LDA.l KoLvSkills,X
    AND #$00FF
    CMP #$001D
    BCC .one
    CMP #$0021
    BCS .one
    XBA                 ; prefix goes in the class byte
    STA $FC
    INX
    DEC $E0
    LDA.l KoLvSkills,X
    AND #$00FF
    ORA $FC
    BRA .put
.one
    ORA $3494
.put
    INX
    DEC $E0
    JSR LvPut
    BRA .next
.particle
    PLA
    BIT #$0080
    BEQ +
    LDA #!lv_eul
    BRA ++
+
    LDA #!lv_reul
++
    JSR LvPut
    RTL
.done
    RTL

; A = glyph list entry: appended at the pen position, which moves 10 px.
LvPut:
    LDY $3492
    STA $7E00,Y
    LDA $EC
    STA $7E02,Y
    TYA
    CLC
    ADC #$0004
    STA $3492
    LDA $EC
    CLC
    ADC #$000A
    STA $EC
    RTS

; Replaces the code after a number is drawn (LDY $EE / INY / INY). When the
; text goes on with "(이)가", only the particle that fits the number's
; reading is drawn: 이 after 1, 3, 6, 7, 8 and tens, 가 after 2, 4, 5, 9.
KoLvAfterNum:
    LDY $EE
    INY
    INY
    LDX #$0000
-
    LDA.l KoLvIga,X
    AND #$00FF
    BEQ .match
    STA $FC
    LDA [$E8],Y
    AND #$00FF
    CMP $FC
    BNE .no
    INX
    INY
    BRA -
.no
    LDY $EE
    INY
    INY
    RTL
.match
    PHY
    LDA $D0
-
    CMP #$000A
    BCC +
    SEC
    SBC #$000A
    BRA -
+
    TAX
    LDA.l .ga,X
    AND #$00FF
    BEQ +
    LDA #!lv_ga
    BRA ++
+
    LDA #!lv_i
++
    JSR LvPut
    PLY
    RTL
.ga                     ; last digit 0-9: 1 = 가
    db 0, 0, 1, 0, 1, 1, 0, 0, 0, 1

; In: Y = glyph list entry, $F0 = its low byte. Out: A = class * 2 for the
; renderer's jump table; a prefix class becomes a 2-byte glyph in $F0
; (prefix $20 = the font extension after index $3DF).
KoLvAttr:
    TYA
    XBA
    AND #$00FF
    CMP #$001D
    BCC .class
    CMP #$0021
    BCS .class
    SEC
    SBC #$001D
    XBA                 ; (prefix - $1D) * 256
    CLC
    ADC $F0
    ADC #$0100          ; + glyph $E0 + code offset $20
    STA $F0
    LDA #$0000          ; fixed width
    RTL
.class
    ASL
    RTL

KoGlyphOffs:
    incbin "../build/glyph_offs.bin"

; SFC-CPU-only hooks (reached by JSL), kept out of the full bank-C3 area.
; Item name for the dialogue engine. Writes the dialogue-encoded name of item
; $0234 to $7E:2D00, its byte length to $0221 (the engine counts bytes, 2 per
; 2-byte glyph) and the substring pointer to $021C, and returns with DB = $7E
; like the original MVN.
; Code $1A inserts the bare name. Code $1B (unused by the game, routed to the
; same handler) is followed by a flag byte:
;   1 = wrap in 「」, 2 = centre the line, 4 = append 을/를 for the name.
; Centring counts the rest of the line (read ahead from the text) and pads the
; front with spaces so the line sits on the same centre as the banners.
!dn_flags = $7E0C14
!dn_suf   = $7E0C16
!dn_hdr   = $7E0C18
!dn_cells = $7E0C1A
!dn_dp    = $0C00
!dn_ptr   = $1C       ; 24-bit pointer into the text, at !dn_dp+$1C
!dn_line  = 22          ; same as BANNER_CELLS in dlg_rewrite.py

KoDlgName:
    PHP
    PHB
    REP #$30
    PHD
    PEA.w !dn_dp
    PLD                 ; direct page on the patch variables for [!dn_ptr],Y
    LDA #$0000
    STA.l !dn_flags
    STA.l !dn_suf
    LDA.l $00021A       ; text pointer, just past the code; bank in $021E
    DEC
    STA.b !dn_ptr
    LDA.l $00021E
    AND #$00FF
    STA.b !dn_ptr+2
    LDY #$0000
    LDA [!dn_ptr],Y
    AND #$00FF
    CMP #$001B
    BNE .flagsdone
    INY
    LDA [!dn_ptr],Y
    AND #$00FF
    STA.l !dn_flags
    LDA.l $00021A
    INC
    STA.l $00021A       ; resume after the flag byte
.flagsdone
    LDA.l !dn_flags
    BIT #$0002
    BEQ .scandone
    LDY #$0002
.scan
    LDA [!dn_ptr],Y
    AND #$00FF
    CMP #$0007
    BCC .scandone       ; $00-$06 end the line
    INY
    LDX #$0002
    CMP #$0008
    BEQ .addx
    INX
    CMP #$0009
    BEQ .addx
    INX
    CMP #$000A
    BEQ .addx
    CMP #$000B
    BEQ .param
    CMP #$000D
    BEQ .param
    LDX #$0002
    CMP #$001C          ; inserted number, followed by a parameter byte
    BEQ .num
    CMP #$001D
    BCC .scan           ; other control codes take no space
    LDX #$0001
    CMP #$0020
    BCS .addx
.param
    INY                 ; 2-byte glyph, or a code with a parameter byte
    CMP #$001D
    BCS .addx
    BRA .scan
.num
    INY
.addx
    TXA
    CLC
    ADC.l !dn_suf
    STA.l !dn_suf
    BRA .scan
.scandone
    PLD
    ; X = item id * 22
    LDA.l $000234
    AND #$00FF
    ASL
    PHA
    ASL
    ASL
    CLC
    ADC $01,S
    ASL
    CLC
    ADC $01,S
    TAX
    PLA
    LDA.l KoDlgNames,X
    AND #$00FF
    STA.l !dn_hdr
    ; glyphs in the name
    PHX
    LDA #$0000
    STA.l !dn_cells
-
    LDA.l KoDlgNames+1,X
    AND #$00FF
    BEQ +
    INX
    CMP #$001D
    BCC ++
    CMP #$0020
    BCS ++
    INX
++
    LDA.l !dn_cells
    INC
    STA.l !dn_cells
    BRA -
+
    PLX
    ; width of the whole line -> leading spaces
    LDA.l !dn_flags
    AND #$0001
    ASL
    CLC
    ADC.l !dn_cells
    ADC.l !dn_suf
    PHA
    LDA.l !dn_flags
    AND #$0004
    BEQ +
    LDA $01,S
    INC
    STA $01,S           ; the particle takes one cell
+
    LDA.l !dn_flags
    BIT #$0002
    BEQ .nopad
    LDA.w #!dn_line
    SEC
    SBC $01,S
    BCC .nopad
    BEQ .nopad
    LSR
    BRA .pad
.nopad
    LDA #$0000
.pad
    STA $01,S           ; leading spaces

    SEP #$20
    LDA #$7E
    PHA
    PLB
    REP #$20
    PLA
    LDY #$0000
    SEP #$20
-
    CMP #$00
    BEQ +
    PHA
    LDA #$20
    STA $2D00,Y
    INY
    PLA
    DEC
    BRA -
+
    LDA.l !dn_flags
    AND #$01
    BEQ +
    LDA #$3B            ; 「
    STA $2D00,Y
    INY
+
-
    LDA.l KoDlgNames+1,X
    BEQ +
    STA $2D00,Y
    INX
    INY
    BRA -
+
    LDA.l !dn_flags
    AND #$01
    BEQ +
    LDA #$3C            ; 」
    STA $2D00,Y
    INY
+
    LDA.l !dn_flags
    AND #$04
    BEQ .end
    LDX #$0000          ; 을 after a final consonant, else 를
    LDA.l !dn_hdr
    BMI +
    LDX #$0003
+
    LDA.l KoParticles,X
    STA.l !dn_cells     ; byte count
-
    LDA.l KoParticles+1,X
    STA $2D00,Y
    INX
    INY
    LDA.l !dn_cells
    DEC
    STA.l !dn_cells
    BNE -
.end
    LDA #$00
    STA $2D00,Y
    TYA
    STA $0221
    REP #$20
    LDA #$2D00
    STA $021C
    SEP #$20
    PLA                 ; drop the saved DB: the dialogue engine reads $2D00 with DB = $7E
    PLP
    RTL


; Battle text names (see org $C156A8). The name is copied to !bt_buf so the
; interpreter's glyph routine can clobber X between characters.
!bt_pos = $7E1100
!bt_len = $7E1102
!bt_tmp = $7E1104
!bt_buf = $7E1110       ; up to 21 bytes

; In: A = item id. A/X/Y 16-bit; X and Y are preserved.
KoBtlItem:
    PHX
    PHY
    AND #$00FF
    ASL
    PHA
    ASL
    ASL
    CLC
    ADC $01,S
    ASL
    CLC
    ADC $01,S           ; id * 22
    TAX
    PLA
    LDA.l KoDlgNames,X
    AND #$007F
    STA.l !bt_len
    LDY #$0000
    SEP #$20
-
    CPY.w #21
    BCS +
    LDA.l KoDlgNames+1,X
    PHX
    TYX
    STA.l !bt_buf,X
    PLX
    INX
    INY
    BRA -
+
    REP #$20
    BRA KoBtlStart

; In: A = special id. Ally specials come from KoLvSkills; enemy attacks keep
; the original entry (already Korean in V1.0), read the way $C1:573C reads it.
KoBtlSkill:
    PHX
    PHY
    AND #$00FF
    CMP.w #!skill_count
    BCS .orig
    ASL
    ASL
    ASL
    ASL
    TAX
    LDA.l KoLvSkills,X
    AND #$007F
    STA.l !bt_len
    LDY #$0000
    SEP #$20
-
    CPY.w #15
    BCS +
    LDA.l KoLvSkills+1,X
    PHX
    TYX
    STA.l !bt_buf,X
    PLX
    INX
    INY
    BRA -
+
    REP #$20
    BRA KoBtlStart
.orig
    STA.l !bt_tmp
    ASL
    ASL
    ASL
    ASL
    SEC
    SBC.l !bt_tmp       ; id * 15
    TAX
    LDY #$0000
    SEP #$20
-
    CPY.w #10
    BCS +
    LDA.l $FA0000+!skill_table+1,X
    BEQ +
    CMP #$20
    BEQ +
    PHX
    TYX
    STA.l !bt_buf,X
    PLX
    INX
    INY
    BRA -
+
    REP #$20
    TYA
    STA.l !bt_len
KoBtlStart:
    LDA #$0000
    STA.l !bt_pos
    PLY
    PLX
    RTL

; Banner text: a space (where the original entries have their icon), then
; 1C 38 A5 <kind> <id>; kind 1 = special, 2 = item. The game copies it to
; $7E:05E0 and draws it with the battle text interpreter, which sends 1C 38 to
; KoBtlBanner. The name goes through KoBtlNext, so 2-byte codes with prefix
; $20 (font extension) are drawn too; the interpreter alone reads $20 as a
; space.
!bn_text = $7E1128      ; 7 bytes

; In: A/X/Y 16-bit, $E0 = special id, $4216 = id * 15 (the original offset).
KoBanSkill:
    LDA $E0
    AND #$00FF
    CMP.w #!skill_count
    BCC +
    LDA $4216           ; enemy attack: original entry, already Korean in V1.0
    CLC
    ADC.l $FA0008
    STA $0B86
    RTL
+
    XBA
    ORA #$0001
    BRA KoBanText

KoBanItem:
    LDA $E0
    AND #$00FF
    XBA
    ORA #$0002
KoBanText:
    STA.l !bn_text+4    ; kind, id
    LDA #$1C20
    STA.l !bn_text
    LDA #$A538
    STA.l !bn_text+2
    LDA #$0000
    STA.l !bn_text+6
    LDA.w #!bn_text
    STA $0B86
    LDA.w #!bn_text>>16
    STA $0B88
    RTL

; Battle text code 1C 38 (from BtlCode38). Interpreter state: A/X/Y 16-bit,
; next byte at [$3D] + $A4, Y = draw position (the interpreter's byte reader
; $C1:55BB keeps it too). Text that is not a banner keeps the original
; meaning of 1C 38.
KoBtlBanner:
    PHY
    LDY $A4
    LDA [$3D],Y
    AND #$00FF
    CMP #$00A5
    BEQ +
    PLY
    JML $C156A3
+
    INY
    LDA [$3D],Y         ; kind | id << 8
    INY
    INY
    STY $A4
    PLY
    XBA
    CMP #$0200
    BCS .item
    AND #$00FF
    JSL KoBtlSkill
    BRA .draw
.item
    AND #$00FF
    JSL KoBtlItem
.draw
-
    JSL KoBtlNext
    BCS +
    JSL BtlGlyph
    BRA -
+
    JML BtlTextRts

; Out: carry set at the end of the name, else A = code for $C1:5769.
KoBtlNext:
    PHX
    LDA.l !bt_pos
    CMP.l !bt_len
    BCS .end
    TAX
    LDA.l !bt_buf,X
    AND #$00FF
    CMP #$001D
    BCC .one
    CMP #$0020
    BCC .two
    BNE .one
    ; $20 is a prefix only before an extension index ($00-$1F); the English
    ; names left for unused items have real spaces ("KILL BOMB").
    LDA.l !bt_buf+1,X
    AND #$00FF
    CMP #$0020
    LDA #$0020
    BCS .one
.two
    SEC
    SBC #$001C
    XBA
    STA.l !bt_tmp
    INX
    LDA.l !bt_buf,X
    AND #$00FF
    ORA.l !bt_tmp
.one
    INX
    PHA
    TXA
    STA.l !bt_pos
    PLA
    PLX
    CLC
    RTL
.end
    PLX
    SEC
    RTL


assert pc() <= $E2FFFF

incsrc "../build/glyphs.asm"
incsrc "../build/dialogue.asm"
incsrc "../build/name_entry_data.asm"
incsrc "name_entry.asm"
