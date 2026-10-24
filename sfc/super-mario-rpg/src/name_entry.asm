; Name entry by jamo, and names with syllables outside the menu font.
;
; The name buffer ($0995, 8 bytes, saved at $7F:F8B5 and slot offset $B5)
; keeps menu-font codes as single bytes, so names from older saves read as
; before. Any other character takes two bytes: $01-$0A and a low byte give a
; name glyph (tools/py/name_entry.py). Both screens that show the name draw it
; through the hooks below: the name entry screen on BG1 with fixed slots in
; VRAM $6000-$7FFF (BG2 there only uses tiles from $8000), the file select
; screen on BG3 with slots in tiles $1C0-$1DF, just past its 2bpp menu font.
;
; The name entry state lives in !ne_* (main.asm): the committed characters and
; a stack of composing states, one per jamo typed into the current syllable,
; so that B takes back one jamo at a time.

!ne_grid_pos  = $4248   ; tilemap offset of the first grid cell (page 1)
!ne_name_pos  = $4158   ; tilemap offset of the name
!ne_name_slot = $0060   ; first BG1 slot of the 8 name cells; the grid takes slots from 0
!ne_jamo      = 51      ; name glyphs below this are jamo
!ne_cmd_space = $FFF0
!ne_cmd_back  = $FFF1
!ne_cmd_done  = $FFF2
!ne_sfx_ok    = $01
!ne_sfx_back  = $02
!ne_sfx_move  = $03
!ne_sfx_no    = $58     ; the sound this screen plays when it refuses an empty name
!fs_slot_tile = $01C0
!fs_slots     = 16

!ne_done      = $4413   ; original "done" handler: moves the cursor to 완료, or finishes
!ne_fly       = $434F   ; original: sends the sprite tiles at $7E:F580 flying to name cell $0929
!ne_fly_tiles = $F580   ; two 4bpp sprite tiles (upper, lower) the original builds from $7E:8000
!menu_font    = $8000   ; converted menu font, 32 bytes per code from $20
!play_sfx     = $7A47

org $C340C1
    JSR NeInit          ; was JSR $4162: both pages of the syllable grid

org $C34126
    JSR NeInput         ; was JSR $422E

org $C344D2
    JMP NeDrawName      ; was the name drawing (LDX #$4158 / STX $62 / JSR $79C5 / ...)

; End of the flying character: was JSR $43F3 (next position) / JSR $4409 (draw).
org $C3452D
    JSR NeLanded
    NOP #3

; File select: the two places that draw a file's name after copying it to $0995.
org $C34A8F
    JSR FsPutName
org $C34AB8
    JSR FsPutName

org $C3E240
; ---------------------------------------------------------------------------
; Drawing

; Sets !attr from $9D and $72 to the lower-row offset, like $79C5.
NeAttr:
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
    STA $72
    RTS

; In: X = offset in $0995. Out: A = code ($20 past the end), X = next offset.
NeDecode:
    CPX #$0008
    BCS .space
    LDA $0995,X
    AND #$00FF
    BEQ .space1
    CMP #$0020
    BCS .one
    CPX #$0007
    BCS .space
    DEC
    XBA
    STA !ne_t4
    LDA $0996,X
    AND #$00FF
    ORA !ne_t4
    ORA #$8000
    INX
    INX
    RTS
.space1
    INX
.space
    LDA #$0020
    RTS
.one
    INX
    RTS

; In: A = name glyph. Out: font_tmp = the glyph through the outline routine.
NeLoadGlyph:
    CMP #!ne_chunk3
    BCS .c3
    CMP #!ne_chunk2
    BCS .c2
    CMP #!ne_chunk1
    BCS .c1
    JSR .times12
    TAX
    LDY #$0000
-
    LDA.l NeGlyphs0,X
    JSR .row
    BCC -
    BRA .outline
.c1
    SEC
    SBC #!ne_chunk1
    JSR .times12
    TAX
    LDY #$0000
-
    LDA.l NeGlyphs1,X
    JSR .row
    BCC -
    BRA .outline
.c2
    SEC
    SBC #!ne_chunk2
    JSR .times12
    TAX
    LDY #$0000
-
    LDA.l NeGlyphs2,X
    JSR .row
    BCC -
    BRA .outline
.c3
    SEC
    SBC #!ne_chunk3
    JSR .times12
    TAX
    LDY #$0000
-
    LDA.l NeGlyphs3,X
    JSR .row
    BCC -
.outline
    LDA #$0000
-
    STA !font_tmp,Y
    INY
    INY
    CPY #$0040
    BCC -
    JMP !outline_glyph

; Stores one 1bpp row as the menu font's (row, 0) pair. Carry set after 12 rows.
.row
    AND #$00FF
    STA !font_tmp,Y
    INX
    INY
    INY
    CPY #$0018
    RTS

.times12
    ASL
    ASL
    STA !ne_t4
    ASL
    CLC
    ADC !ne_t4
    RTS

; Name entry: draws the name buffer into the 8 name cells. Replaces $44D2.
NeDrawName:
    PHP
    REP #$30
    PHX
    PHY
    LDA $70
    PHA
    LDA $72
    PHA
    JSR NeAttr
    LDY #!ne_name_pos
    LDX #$0000
    STZ !ne_t0          ; cell
.loop
    PHY
    JSR NeDecode
    PLY
    PHX
    BIT #$8000
    BNE .dynamic
    JSR PutStatic
    BRA .next
.dynamic
    AND #$7FFF
    PHA
    LDA !ne_t0
    ASL
    TAX
    PLA
    CMP !ne_cellg,X
    BEQ .cached
    STA !ne_cellg,X
    PHY
    JSR NeLoadGlyph
    LDA !ne_t0
    CLC
    ADC #!ne_name_slot
    JSR NeSlotWord
    LDY #$0040
    JSR QueueTmp
    PLY
.cached
    LDA !ne_t0
    CLC
    ADC #!ne_name_slot
    ASL
    ORA #!slot_tile
    JSR PutTile
.next
    PLX
    INC !ne_t0
    LDA !ne_t0
    CMP #$0008
    BCC .loop
    STY $62
    PLA
    STA $72
    PLA
    STA $70
    SEP #$20
    LDA #$01
    STA $94
    REP #$30
    PLY
    PLX
    PLP
    RTS

; In: A = BG1 slot. Out: A = its VRAM word address.
NeSlotWord:
    ASL
    ASL
    ASL
    ASL
    ASL
    CLC
    ADC #!slot_vram_word
    RTS

; File select: draws the name in $0995 ($0994 cells) at $62. Replaces $79C5.
FsPutName:
    PHP
    REP #$30
    PHX
    PHY
    LDA $70
    PHA
    LDA $72
    PHA
    JSR NeAttr
    LDA $0994
    AND #$00FF
    STA !ne_t0
    LDY $62
    LDX #$0000
.loop
    PHY
    JSR NeDecode
    PLY
    PHX
    BIT #$8000
    BNE .dynamic
    JSR PutStatic
    BRA .next
.dynamic
    AND #$7FFF
    PHY
    JSR FsAlloc
    PLY
    ASL
    CLC
    ADC #!fs_slot_tile
    JSR PutTile
.next
    PLX
    DEC !ne_t0
    BNE .loop
    STY $62
    PLA
    STA $72
    PLA
    STA $70
    PLY
    PLX
    PLP
    RTS

; In: A = name glyph. Out: A = file-select slot holding it.
FsAlloc:
    STA !ne_t1
    LDX #$0000
.find
    CPX !fs_cnt
    BCS .new
    LDA !fs_tab,X
    CMP !ne_t1
    BEQ .hit
    INX
    INX
    BRA .find
.hit
    TXA
    LSR
    RTS
.new
    CPX.w #!fs_slots*2
    BCC .room
    LDX #$0000          ; three names hold at most 12 such glyphs
.room
    LDA !fs_cnt
    BNE +
    LDA !fs_keepst
    CMP #$A55A
    BEQ +
    LDA #$5AA5
    STA !fs_keepst
+
    LDA !ne_t1
    STA !fs_tab,X
    TXA
    INC
    INC
    STA !fs_cnt
    TXA
    LSR
    PHA
    LDA !ne_t1
    JSR NeLoadGlyph
    PLA
    PHA
    ASL
    ASL
    ASL
    ASL
    CLC
    ADC #!fs_slot_word
    LDY #$0020
    JSR QueueTmp
    PLA
    RTS

; ---------------------------------------------------------------------------
; Name entry screen

; New game goes from the file select to this screen without reloading BG3
; tiles $1C0-$1DF, which hold this screen's window frame: put back what the
; file select's slots covered.
FsRestore:
    LDA !fs_keepst
    CMP #$A55A
    BNE .done
    STZ !fs_keepst
    LDX #$0000          ; offset in !fs_keep
.slot
    LDY #$0000
-
    LDA !fs_keep,X
    STA !font_tmp,Y
    INX
    INX
    INY
    INY
    CPY #$0020
    BCC -
    PHX
    TXA
    SEC
    SBC #$0020
    LSR
    CLC
    ADC #!fs_slot_word
    LDY #$0020
    JSR QueueTmp
    PLX
    CPX #$0200
    BCC .slot
.done
    RTS

; Replaces the syllable grid with the jamo grid and resets the state.
NeInit:
    PHP
    REP #$30
    PHX
    PHY
    LDA $70
    PHA
    LDA $72
    PHA
    JSR FsRestore
    STZ !ne_n
    STZ !ne_sp
    STZ !ne_gslot
    SEP #$20
    STZ $092A           ; cursor on ㅂ
    LDA #$01
    STA $092B
    REP #$20
    LDA #$FFFF
    LDX #$000E
-
    STA !ne_cellg,X
    DEX
    DEX
    BPL -
    JSR NeAttr

    ; Clear the grid area, labels included: 8 rows of two tile rows, x 4-30.
    LDY #!ne_grid_pos
    LDA #$0010
    STA !ne_t0
.clear_row
    LDX #$001B
    PHY
-
    LDA !attr
    STA $0000,Y
    INY
    INY
    DEX
    BNE -
    PLY
    TYA
    CLC
    ADC #$0040
    TAY
    DEC !ne_t0
    BNE .clear_row

    LDX #$0000          ; offset in NeGrid
    STZ !ne_t0          ; row
.row
    STZ !ne_t1          ; column
.cell
    LDA !ne_t0
    XBA
    LSR                 ; row * $80
    STA !ne_t2
    LDA !ne_t1
    ASL
    ASL
    CLC
    ADC !ne_t2
    ADC #!ne_grid_pos
    TAY
    LDA.l NeGrid,X
    BEQ .skip
    PHX
    CMP #!ne_cmd_space
    BCC .glyph
    BNE +
    LDX.w #NeLabelSpace-NeLabelSpace
    BRA .label
+
    CMP #!ne_cmd_back
    BNE +
    LDX.w #NeLabelBack-NeLabelSpace
    BRA .label
+
    LDX.w #NeLabelDone-NeLabelSpace
.label
    LDA.l NeLabelSpace,X
    BEQ .done_cell
    PHX
    JSR NeGridPut
    PLX
    INX
    INX
    BRA .label
.glyph
    JSR NeGridPut
.done_cell
    PLX
.skip
    INX
    INX
    INC !ne_t1
    LDA !ne_t1
    CMP #$000B
    BCC .cell
    INC !ne_t0
    LDA !ne_t0
    CMP #$0008
    BCC .row

    PLA
    STA $72
    PLA
    STA $70
    PLY
    PLX
    PLP
    RTS

; In: A = code, Y = tilemap offset. Dynamic glyphs take the next grid slot.
NeGridPut:
    BIT #$8000
    BNE +
    JMP PutStatic
+
    AND #$7FFF
    PHY
    JSR NeLoadGlyph
    LDA !ne_gslot
    JSR NeSlotWord
    LDY #$0040
    JSR QueueTmp
    LDA !ne_gslot
    INC !ne_gslot
    ASL
    ORA #!slot_tile
    PLY
    JMP PutTile

; Replaces $422E: cursor and buttons.
NeInput:
    REP #$30
    LDA $18
    BIT #$0800
    BNE .up
    BIT #$0400
    BNE .down
    BIT #$0200
    BNE .left
    BIT #$0100
    BNE .right
    LDA $14
    BIT #$4080
    BEQ +
    JMP NeSelect
+
    BIT #$8000
    BEQ +
    JMP NeBack
+
    BIT #$1000
    BEQ .none
    SEP #$20
    JMP !ne_done
.none
    SEP #$20
    RTS

.up
    SEP #$20
    DEC $092B
    BPL +
    LDA #$07
    STA $092B
+
    JSR NeCellCode
    SEP #$20
    BEQ .up
    BRA .moved
.down
    SEP #$20
    INC $092B
    LDA $092B
    CMP #$08
    BCC +
    STZ $092B
+
    JSR NeCellCode
    SEP #$20
    BEQ .down
    BRA .moved
.left
    SEP #$20
    DEC $092A
    BPL +
    LDA #$0A
    STA $092A
+
    JSR NeCellCode
    SEP #$20
    BEQ .left
    BRA .moved
.right
    SEP #$20
    INC $092A
    LDA $092A
    CMP #$0B
    BCC +
    STZ $092A
+
    JSR NeCellCode
    SEP #$20
    BEQ .right
.moved
    STZ $092F
    LDA #!ne_sfx_move
    STA $70
    JMP !play_sfx

; Out: A (16-bit) = code of the cell under the cursor, Z set for a gap. M/X 16-bit.
NeCellCode:
    REP #$30
    LDA $092B
    AND #$00FF
    STA !ne_t4
    ASL
    ASL
    CLC
    ADC !ne_t4
    ASL
    CLC
    ADC !ne_t4          ; row * 11
    STA !ne_t4
    LDA $092A
    AND #$00FF
    CLC
    ADC !ne_t4
    ASL
    TAX
    LDA.l NeGrid,X
    RTS

NeSelect:
    JSR NeCellCode
    BNE +
    SEP #$20
    RTS
+
    STA !ne_key
    CMP #!ne_cmd_done
    BNE +
    STZ !ne_sp
    SEP #$20
    JMP !ne_done
+
    CMP #!ne_cmd_back
    BNE +
    JMP NeBack
+
    CMP #!ne_cmd_space
    BNE +
    LDA #$0020
    BRA .char
+
    BIT #$8000
    BEQ .char
    AND #$7FFF
    JSR NeSaveState
    JSR NeJamo
    BRA .check
.char
    JSR NeSaveState
    JSR NeAddChar
.check
    BCS .refuse
    JSR NeLength
    CMP #$0009
    BCS .refuse
    PHA
    JSR NeSerialize
    PLA
    CMP #$0008
    BNE .fly
    LDA !ne_sp
    BNE .fly
    SEP #$20            ; full: go to 완료, as the original screen does
    LDA #$0A
    STA $092A
    LDA #$07
    STA $092B
.fly
    REP #$30
    LDA !ne_key
    CMP #!ne_cmd_space
    BNE NeFly
    JSR NeDrawName      ; a space does not fly, as in the original
    SEP #$20
    LDA #!ne_sfx_ok
    STA $70
    JMP !play_sfx
.refuse
    JMP NeRefuse

; Sends the chosen key flying to the cell that changed; the name is drawn when
; it lands (NeLanded). The original routine plays the sound.
NeFly:
    LDA !ne_n           ; target cell: the syllable being composed, else the last character
    LDX !ne_sp
    BNE +
    DEC
+
    SEP #$20
    STA $0929
    REP #$20
    LDA !ne_key
    BIT #$8000
    BNE .dynamic
    SEC
    SBC #$0020
    ASL
    ASL
    ASL
    ASL
    ASL
    TAY
    LDX #$0000
-
    LDA !menu_font,Y
    STA !ne_fly_tiles,X
    STZ !ne_fly_tiles+16,X
    LDA !menu_font+16,Y
    STA !ne_fly_tiles+32,X
    STZ !ne_fly_tiles+48,X
    INY
    INY
    INX
    INX
    CPX #$0010
    BCC -
    BRA .go
.dynamic
    AND #$7FFF
    JSR NeLoadGlyph
    LDX #$0000
-
    LDA !font_tmp,X
    STA !ne_fly_tiles,X
    STZ !ne_fly_tiles+16,X
    LDA !font_tmp+16,X
    STA !ne_fly_tiles+32,X
    STZ !ne_fly_tiles+48,X
    INX
    INX
    CPX #$0010
    BCC -
.go
    SEP #$20
    JMP !ne_fly

NeLanded:
    PHP
    JSR NeRefresh
    PLP
    RTS

NeRefuse:
    JSR NeLoadState
    SEP #$20
    LDA #!ne_sfx_no
    STA $70
    JMP !play_sfx

; B or 지우기: one jamo of the syllable being composed, else the last character.
NeBack:
    REP #$30
    LDA !ne_sp
    BEQ +
    DEC !ne_sp
    BRA .done
+
    LDA !ne_n
    BEQ .done
    DEC !ne_n
.done
    JSR NeRefresh
    SEP #$20
    LDA #!ne_sfx_back
    STA $70
    JMP !play_sfx

; Writes the state to $0995, sets the arrow ($0929) and redraws the name.
NeRefresh:
    JSR NeSerialize
    REP #$30
    JMP NeDrawName

; Writes the state to $0995 and sets the arrow ($0929).
NeSerialize:
    REP #$30
    LDX #$0000
    LDY #$0000
.chars
    CPY !ne_n
    BCS .composing
    PHY
    TYA
    ASL
    TAY
    LDA !ne_ch,Y
    JSR NeEmit
    PLY
    INY
    BRA .chars
.composing
    LDA !ne_sp
    BEQ .pad
    PHX
    JSR NeTopCode
    PLX
    JSR NeEmit
.pad
    SEP #$20
    LDA #$20
-
    CPX #$0008
    BCS +
    STA $0995,X
    INX
    BRA -
+
    LDA !ne_n
    CMP #$08
    BCC +
    LDA #$07
+
    STA $0929
    REP #$30
    RTS

; In: A = code, X = offset in $0995 (known to fit). Out: X advanced.
NeEmit:
    BIT #$8000
    BNE .two
    SEP #$20
    STA $0995,X
    REP #$20
    INX
    RTS
.two
    AND #$7FFF
    XBA
    SEP #$20
    INC
    STA $0995,X
    XBA
    STA $0996,X
    REP #$20
    INX
    INX
    RTS

; Out: A = bytes the name takes, composing syllable included.
NeLength:
    REP #$30
    STZ !ne_len
    LDY #$0000
.chars
    CPY !ne_n
    BCS .composing
    PHY
    TYA
    ASL
    TAY
    LDA !ne_ch,Y
    JSR .count
    PLY
    INY
    BRA .chars
.composing
    LDA !ne_sp
    BEQ +
    JSR NeTopCode
    JSR .count
+
    LDA !ne_len
    RTS
.count
    INC !ne_len
    BIT #$8000
    BEQ +
    INC !ne_len
+
    RTS

; Keeps A.
NeSaveState:
    PHA
    LDX.w #!ne_state_end-!ne_n-2
-
    LDA !ne_n,X
    STA !ne_save,X
    DEX
    DEX
    BPL -
    PLA
    RTS

NeLoadState:
    REP #$30
    LDX.w #!ne_state_end-!ne_n-2
-
    LDA !ne_save,X
    STA !ne_n,X
    DEX
    DEX
    BPL -
    RTS

; In: A = code. Commits the syllable being composed, then adds the character.
; Out: carry set if there is no room.
NeAddChar:
    PHA
    JSR NeCommit
    PLA
    BCS +
    JSR NeAppend
+
    RTS

; Out: carry set if there is no room for another character.
NeCommit:
    LDA !ne_sp
    BEQ .none
    JSR NeTopCode
    STZ !ne_sp
    JMP NeAppend
.none
    CLC
    RTS

; In: A = code. Out: carry set if 8 characters are already there.
NeAppend:
    PHA
    LDA !ne_n
    CMP #$0008
    BCS .full
    ASL
    TAX
    PLA
    STA !ne_ch,X
    INC !ne_n
    CLC
    RTS
.full
    PLA
    SEC
    RTS

; Out: X = offset of the top state in !ne_stk.
NeTop:
    LDA !ne_sp
    DEC
    ASL
    ASL
    TAX
    RTS

NeTopCode:
    JSR NeTop
    ; fall through

; In: X = offset of a state. Out: A = its code, carry set if no glyph has it.
NeStateCode:
    LDA !ne_stk+1,X
    AND #$00FF
    CMP #$00FF
    BNE .medial
    LDA !ne_stk,X       ; an initial alone
    AND #$00FF
    TAX
    LDA.l NeChoJ,X
.jamo
    AND #$00FF
    ORA #$8000
    CLC
    RTS
.medial
    STA !ne_t1
    LDA !ne_stk,X
    AND #$00FF
    CMP #$00FF
    BNE .syllable
    LDX !ne_t1          ; a medial alone
    LDA.l NeJungJ,X
    BRA .jamo
.syllable
    STA !ne_t0          ; s = (initial * 21 + medial) * 28 + final
    ASL
    ASL
    STA !ne_t2
    ASL
    ASL
    CLC
    ADC !ne_t2
    ADC !ne_t0
    ADC !ne_t1
    STA !ne_t2
    ASL
    ASL
    ASL
    ASL
    ASL
    SEC
    SBC !ne_t2
    SBC !ne_t2
    SBC !ne_t2
    SBC !ne_t2
    STA !ne_t2
    LDA !ne_stk+2,X
    AND #$00FF
    CLC
    ADC !ne_t2
    ; binary search in NeKsSyl
    STA !ne_t2
    STZ !ne_t0          ; low
    LDA.w #!ne_ks_count
    STA !ne_t1          ; high (exclusive)
.search
    LDA !ne_t0
    CMP !ne_t1
    BCS .missing
    CLC
    ADC !ne_t1
    LSR
    STA !ne_t3
    ASL
    TAX
    LDA.l NeKsSyl,X
    CMP !ne_t2
    BEQ .found
    BCS .lower
    LDA !ne_t3
    INC
    STA !ne_t0
    BRA .search
.lower
    LDA !ne_t3
    STA !ne_t1
    BRA .search
.missing
    SEC
    RTS
.found
    LDX !ne_t3
    LDA.l NeKsStatic,X
    AND #$00FF
    BNE +
    TXA
    CLC
    ADC.w #!ne_jamo
    ORA #$8000
+
    CLC
    RTS

; Pushes (!ne_t0 initial, !ne_t1 medial, !ne_t2 final; $FF = none) if a glyph
; has it. Out: carry set, and nothing pushed, if none does.
NePush:
    LDA !ne_sp
    ASL
    ASL
    TAX
    SEP #$20
    LDA !ne_t0
    STA !ne_stk,X
    LDA !ne_t1
    STA !ne_stk+1,X
    LDA !ne_t2
    STA !ne_stk+2,X
    REP #$20
    JSR NeStateCode
    BCS +
    INC !ne_sp
+
    RTS

; In: A = jamo. Starts a new syllable with it (sp must be 0).
NeStart:
    TAX
    LDA.l NeJCho,X
    AND #$00FF
    STA !ne_t0
    LDA.l NeJJung,X
    AND #$00FF
    STA !ne_t1
    STZ !ne_t2
    JMP NePush

; In: A = jamo. Out: carry set if the jamo cannot be typed here.
NeJamo:
    STA !ne_t4
    LDA !ne_sp
    BNE +
    LDA !ne_t4
    JMP NeStart
+
    JSR NeTop
    LDA !ne_stk,X
    AND #$00FF
    STA !ne_t0
    LDA !ne_stk+1,X
    AND #$00FF
    STA !ne_t1
    LDA !ne_stk+2,X
    AND #$00FF
    STA !ne_t2
    LDX !ne_t4
    LDA.l NeJJung,X
    AND #$00FF
    CMP #$00FF
    BEQ .consonant
    JMP .vowel

.consonant
    LDA !ne_t1
    CMP #$00FF
    BEQ .new            ; an initial alone: it stays one
    LDA !ne_t0
    CMP #$00FF
    BEQ .new            ; a medial alone
    LDA !ne_t2
    BNE .double
    LDX !ne_t4
    LDA.l NeJJong,X
    AND #$00FF
    BEQ .new            ; ㄸ ㅃ ㅉ are never finals
    STA !ne_t2
    JSR NePush
    BCS .new
    RTS
.double
    JSR NeFindJongMix
    BCS .new
    STA !ne_t2
    JSR NePush
    BCS .new
    RTS
.new
    JSR NeCommit
    BCS +
    LDA !ne_t4
    JMP NeStart
+
    RTS

.vowel
    STA !ne_vowel          ; medial of the new jamo
    LDA !ne_t1
    CMP #$00FF
    BNE +
    LDA !ne_vowel          ; an initial alone takes the medial
    STA !ne_t1
    JMP NePush
+
    LDA !ne_t2
    BNE .split
    JSR NeFindJungMix
    BCS .new
    STA !ne_t1
    JMP NePush
.split
    ; The final moves on to the next syllable (only its last consonant if double).
    TAX
    LDA.l NeJongRest,X
    AND #$00FF
    STA !ne_t2
    LDA.l NeJongMove,X
    AND #$00FF
    PHA
    JSR NeStateCode2    ; the syllable without what moves
    BCS .drop1
    PHA
    LDA $03,S
    STA !ne_t0
    LDA !ne_vowel
    STA !ne_t1
    STZ !ne_t2
    JSR NeStateCode2    ; the next syllable
    BCS .drop2
    PLA
    STZ !ne_sp
    JSR NeAppend
    PLA
    BCS .refuse
    STA !ne_t0
    LDA #$00FF
    STA !ne_t1
    STZ !ne_t2
    JSR NePush          ; the moved initial alone, so B can take the medial back
    LDA !ne_vowel
    STA !ne_t1
    STZ !ne_t2
    JMP NePush
.drop2
    PLA
.drop1
    PLA
.refuse
    SEC
    RTS

; (!ne_t0, !ne_t1, !ne_t2) -> code without touching the stack.
NeStateCode2:
    LDA !ne_sp
    ASL
    ASL
    TAX
    SEP #$20
    LDA !ne_t0
    STA !ne_stk,X
    LDA !ne_t1
    STA !ne_stk+1,X
    LDA !ne_t2
    STA !ne_stk+2,X
    REP #$20
    JMP NeStateCode

; Medial !ne_t1 + jamo !ne_t4 -> A = compound medial, carry set if none.
NeFindJungMix:
    LDX #$0000
-
    LDA.l NeJungMix,X
    AND #$00FF
    CMP #$00FF
    BEQ .none
    CMP !ne_t1
    BNE +
    LDA.l NeJungMix+1,X
    AND #$00FF
    CMP !ne_t4
    BNE +
    LDA.l NeJungMix+2,X
    AND #$00FF
    CLC
    RTS
+
    INX
    INX
    INX
    BRA -
.none
    SEC
    RTS

; Final !ne_t2 + jamo !ne_t4 -> A = double final, carry set if none.
NeFindJongMix:
    LDX #$0000
-
    LDA.l NeJongMix,X
    AND #$00FF
    CMP #$00FF
    BEQ .none
    CMP !ne_t2
    BNE +
    LDA.l NeJongMix+1,X
    AND #$00FF
    CMP !ne_t4
    BNE +
    LDA.l NeJongMix+2,X
    AND #$00FF
    CLC
    RTS
+
    INX
    INX
    INX
    BRA -
.none
    SEC
    RTS

assert pc() <= $C3F000
