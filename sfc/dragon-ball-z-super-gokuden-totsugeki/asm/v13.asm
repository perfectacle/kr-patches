; v1.3: names in 8 px glyphs for all 11,172 syllables, typed by composing jamo.
;
; tools/font8.py redraws the 8 px Hangul, puts the new 8 px glyphs (codes !f8_first-) in
; banks $C0- and writes the jamo grid of the name entry screen. This file makes the renderer
; draw the new codes like kana-slot codes and turns the name entry into a jamo keyboard.
;
; A name is 5 codes and a space at $0B01 + person * 13 (person = $0231); $10 is the byte
; offset of the next character. The syllable being composed is always the last character;
; a stack of states (initial, medial, final), one per jamo typed into it, lets B take back
; one jamo at a time.
lorom

incsrc "../work/font8_defs.asm"

!name    = $7E0B01
!person  = $7E0231
!max     = 5
!blank   = $02C5            ; space
!star    = $026A            ; the placeholder of an empty position
!spacekey = $02C8           ; the grid's space key
!f8_buf  = $4000            ; $7E:4000-$410F: one 8 px glyph for the renderer (unused after boot)

; WRAM $7F:FF00- holds no game data during the name entry (written by nothing after boot
; through the first scenes); only the name entry uses this.
!sp    = $FF00              ; states on the stack (0 = not composing)
!stk   = $FF02              ; 6 states x 4 bytes: initial, medial, final
!t0    = $FF20
!t1    = $FF22
!t2    = $FF24
!t3    = $FF26
!key   = $FF28              ; jamo just chosen
!vowel = $FF2A              ; its medial
!lastn = $FF2C              ; name length and last code after our last write, to tell
!lastc = $FF2E              ; whether the name still ends in the syllable we were composing
!full  = $FF30              ; set when a key would start a sixth character: the name ends
!row8  = $FF32

; ---------------------------------------------------------------------------
; Renderer ($B7:9763): codes !f8_first-!f8_end are 8 px glyphs like the kana slots.

org $B7FA00                 ; entered with A = code & $7FFF for codes >= $07F0
    JML F8Sheet

org $B797F0                 ; advance: LDA $0200 / BIT #$8000
    JSL F8Kind
    NOP #2
org $B798DA                 ; the same test for the second advance
    JSL F8Kind
    NOP #2
org $B79977                 ; one tile or two: LDA $0200 / AND #$7FFF / CMP #$0500
    JSL F8Kind15
    NOP #2
org $B7986E                 ; next line: $020E * $20 through the multiplier
    JSL F8Wrap
    BRA $B79883

; ---------------------------------------------------------------------------
; Name entry ($80:958E loop)

org $8095A7                 ; LDA $84 / BIT #$0080: A
    JML NeLoop
    NOP
org $809739                 ; LDA $80F005,X: the grid cell under the cursor
    JML NeA
org $809789                 ; LDA $10 / BNE: B
    JML NeB
org $809688                 ; down stops at the second grid row
    CMP #$0001
org $809941                 ; the down arrow shows while the grid can scroll; it no longer does
    dw $0000
; The cursor moves past empty cells. Each hook replaces STA $021A or $021C and the first
; byte of the JSR $A3A7 that follows.
org $809624                 ; right
    JML NeRight
org $80967C                 ; left
    JML NeLeft
org $8096A7                 ; down
    JML NeDown
org $8096EE                 ; up
    JML NeUp

org $80F590                 ; free in bank $80 (0xFF in the Japanese ROM and v1.2)
; Redraws the name of the current person.
NeRedraw:
    PHB
    PHK
    PLB
    PHP
    REP #$30
    LDA $0231
    STA $4D
    JSR $94DD
    PLP
    PLB
    RTL

; The rest of the cursor steps that the move hooks cover.
NeMoved:
    JSR $A3A7
    JMP $95A3
NeMovedDown:
    JSR $A3A7
    JMP $96AD
NeMovedUp:
    JSR $A3A7
    JMP $96F4
assert pc() <= $80FF7F

org $E08000
F8Sheet:
    CMP.w #!f8_first
    BCS .new
    CMP #$0C00
    BCS .ext
    JML $B7FA05             ; $07F0-$0BEF: the original sheet at $BF:8000
.ext
    JML $B7FA23             ; $0C00-: the v1.1 blocks
.new
    ; The renderer reads its variables ($0200-) through the data bank, and banks $C0- have
    ; no low-RAM mirror, so the glyph is copied to a WRAM buffer laid out like a sheet row
    ; (top tile, bottom tile at +$100) and drawn from bank $7E.
    PHX
    SEC
    SBC.w #!f8_first
    STA $2E
    PHA
    AND #$07FF              ; 16 bytes per code, $800 codes per bank
    ASL
    ASL
    ASL
    ASL
    TAY
    PLA
    XBA
    AND #$00FF
    LSR
    LSR
    LSR                     ; bank index = index >> 11
    CLC
    ADC.w #!f8_bank0
    SEP #$20
    PHA
    PLB
    REP #$20
    LDX #$0000
-
    LDA $8000,Y
    STA.l $7E0000|!f8_buf,X
    LDA $8100,Y
    STA.l $7E0000|(!f8_buf+$100),X
    INY
    INY
    INX
    INX
    CPX #$0010
    BCC -
    SEP #$20
    LDA #$7E
    PHA
    PLB
    REP #$20
.copied
    PLX
    STZ $26
    LDA.w #!f8_buf
    STA $4F
    JML $B797D6

; Out: A = the code at $0200, or a kana-slot code with the same $8000 bit for the new codes;
; flags as BIT #$8000.
F8Kind:
    LDA $0200
    PHA
    AND #$7FFF
    CMP.w #!f8_first
    BCC .keep
    CMP.w #!f8_end
    BCS .keep
    PLA
    AND #$8000
    ORA #$0100
    BRA .out
.keep
    PLA
.out
    BIT #$8000
    RTL

F8Kind15:
    JSL F8Kind
    AND #$7FFF
    RTL

; The new glyphs are drawn with DB = $7E, which has no I/O registers.
F8Wrap:
    SEP #$20
    LDA $020E
    STA.l $004202
    LDA #$20
    STA.l $004203
    NOP
    NOP
    NOP
    REP #$20
    LDA.l $004216
    RTL

; ---------------------------------------------------------------------------

NeLoop:
    REP #$30
    LDA $84
    BIT #$1000
    BNE .start
    BIT #$0080
    BEQ .notA
    JML $809714
.notA
    JML $8095B1
.start
    LDA $10
    BEQ .notA2              ; nothing typed yet: Start does nothing
    LDA $84
    AND #$7FFF              ; the caller would take B in the same frame as going back a person
    STA $84
    LDA $10
    JML NeFinish
.notA2
    LDA $84
    JML $8095B1

; In: A = the new column. An empty cell sends it back through the game's own step, which
; also jumps over the gaps between groups.
NeRight:
    STA.l $7E021A
    JSR NeEmpty
    BEQ .skip
    JML NeMoved
.skip
    LDA.l $7E021A
    JML $8095E8

NeLeft:
    STA.l $7E021A
    JSR NeEmpty
    BEQ .skip
    JML NeMoved
.skip
    LDA.l $7E021A           ; the step branches on Z from this load
    JML $809643

; In: A = the new row. An empty cell moves the cursor left; column 0 is never empty.
NeDown:
    STA.l $7E021C
    JSR NeLeftmost
    JML NeMovedDown

NeUp:
    STA.l $7E021C
    JSR NeLeftmost
    JML NeMovedUp

NeLeftmost:
-
    LDA.l $7E021A
    JSR NeEmpty
    BNE .done
    LDA.l $7E021A
    DEC A
    STA.l $7E021A
    BRA -
.done
    RTS

; In: A = column. Out: Z set when the grid cell at row $021C and this column is empty.
NeEmpty:
    PHA
    LDA.l $7E021C
    ASL
    ASL
    ASL
    STA.l $7F0000+!row8
    ASL
    CLC
    ADC.l $7F0000+!row8     ; 24 cells per row
    ADC 1,S
    ASL
    TAX
    PLA
    LDA.l $80F005,X
    AND #$7FFF
    CMP.w #!blank
    RTS

; Ends the name: the positions left become spaces. In: A = $10, not 0.
NeFinish:
-
    CMP.w #!max*2
    BCS .done
    JSR NeIndex
    LDA.w #!blank
    STA.l !name,X
    INC $10
    INC $10
    LDA $10
    BRA -
.done
    LDA #$0000
    STA.l $7F0000+!sp
    JSL NeRedraw
    JML $80977E             ; RTS: the caller moves to the next person

; Out: X = name index of the position $10 points at.
NeIndex:
    LDA.l !person
    AND #$00FF
    STA.l $7F0000+!t3
    ASL
    ASL
    ASL                     ; 8p
    CLC
    ADC.l $7F0000+!t3       ; 9p
    ADC.l $7F0000+!t3
    ADC.l $7F0000+!t3
    ADC.l $7F0000+!t3       ; 12p
    ADC.l $7F0000+!t3       ; 13p
    CLC
    ADC $10
    TAX
    RTS

NeA:
    REP #$30
    LDA.l $80F005,X
    AND #$7FFF
    PHB
    PEA $7F7F
    PLB
    PLB
    CMP.w #!spacekey
    BEQ .space
    SEC
    SBC.w #!f8_jamo_first
    BCC .done
    STA !t0                 ; jamo index = (t >> 5) * 16 + (t & 15)
    AND #$FFE0
    LSR
    STA !t1
    LDA !t0
    AND #$000F
    ORA !t1
    CMP.w #51
    BCS .done
    STZ !full
    JSR NeJamo
    LDA !full
    BEQ .done
    PLB
    LDA $10
    JML NeFinish            ; like the original, a full name moves on to the next person
.space
    STZ !sp
    LDA $10
    CMP.w #!max*2
    BCS .full
    LDA.w #!blank
    JSR NeAppend
    JSR NeMark
.done
    PLB
    JML $8095A3
.full
    PLB
    JML NeFinish

NeB:
    REP #$30
    PHB
    PEA $7F7F
    PLB
    PLB
    JSR NeGuard
    LDA !sp
    BEQ .plain
    DEC !sp
    BEQ .plain              ; the syllable's first jamo: delete the character
    JSR NeTopCode
    JSR NeRewrite
    JSR NeMark
    PLB
    JML $8095A3
.plain
    STZ !sp
    PLB
    LDA $10
    BEQ +
    JML $809790             ; delete the last character
+
    JML $8097BE             ; empty name: back to the previous person

; DB = $7F from here on; game variables are read long, $10 through the direct page.

; Forget the composing stack if the name no longer ends in the syllable we wrote.
NeGuard:
    LDA !sp
    BEQ .ok
    CMP #$0007
    BCS .clear              ; WRAM is not cleared at power-on
    LDA $10
    BEQ .clear
    CMP !lastn
    BNE .clear
    DEC
    DEC
    STA $10
    JSR NeIndex
    INC $10
    INC $10
    LDA.l !name,X
    CMP !lastc
    BEQ .ok
.clear
    STZ !sp
.ok
    RTS

NeMark:
    LDA $10
    STA !lastn
    DEC
    DEC
    STA $10
    JSR NeIndex
    INC $10
    INC $10
    LDA.l !name,X
    STA !lastc
    RTS

; A = code: becomes the next character.
NeAppend:
    PHA
    JSR NeIndex
    PLA
    STA.l !name,X
    INC $10
    INC $10
    JSL NeRedraw
    RTS

; A = code: replaces the last character.
NeRewrite:
    DEC $10
    DEC $10
    JMP NeAppend

; A = jamo index.
NeJamo:
    STA !key
    TAX
    LDA.l NeJJung,X
    AND #$00FF
    STA !vowel
    JSR NeGuard
    LDA !sp
    BNE .compose
.new
    LDA $10
    CMP.w #!max*2
    BCS .isfull
    STZ !sp
    LDX !key
    LDA.l NeJCho,X
    AND #$00FF
    STA !t0
    LDA !vowel
    STA !t1
    STZ !t2
    JSR NePush
    JSR NeTopCode
    JSR NeAppend
    JMP NeMark
.isfull
    INC !full
    RTS
.compose
    JSR NeTop
    LDA !stk,X
    AND #$00FF
    STA !t0
    LDA !stk+1,X
    AND #$00FF
    STA !t1
    LDA !stk+2,X
    AND #$00FF
    STA !t2
    LDA !vowel
    CMP #$00FF
    BEQ .consonant
    LDA !t1
    CMP #$00FF
    BNE +
    LDA !vowel              ; an initial alone takes the medial
    STA !t1
    JSR NePush
    BRA .replace
+
    LDA !t2
    BNE .split
    JSR NeFindJungMix
    BCS .new2
    STA !t1
    JSR NePush
    BRA .replace
.new2
    JMP .new
.consonant
    LDA !t1
    CMP #$00FF
    BEQ .new2
    LDA !t0
    CMP #$00FF
    BEQ .new2
    LDA !t2
    BNE .double
    LDX !key
    LDA.l NeJJong,X
    AND #$00FF
    BEQ .new2               ; ㄸ ㅃ ㅉ are never finals
    STA !t2
    JSR NePush
    BRA .replace
.double
    JSR NeFindJongMix
    BCS .new2
    STA !t2
    JSR NePush
.replace
    JSR NeTopCode
    JSR NeRewrite
    JMP NeMark

; A vowel after a final: the final (its last consonant if double) starts the next syllable.
.split
    LDA $10
    CMP.w #!max*2
    BCC +
    INC !full               ; no room for the next syllable
    RTS
+
    LDX !t2
    LDA.l NeJongRest,X
    AND #$00FF
    STA !t2
    LDA.l NeJongMove,X
    AND #$00FF
    PHA
    JSR NeStateCode2        ; the syllable without what moves
    PHA
    LDA $03,S
    STA !t0
    LDA !vowel
    STA !t1
    STZ !t2
    JSR NeStateCode2        ; the next syllable
    PLA
    JSR NeRewrite
    PLA
    STA !t0
    STZ !sp
    LDA #$00FF
    STA !t1
    STZ !t2
    JSR NePush              ; the moved initial alone, so B can take the medial back
    LDA !vowel
    STA !t1
    STZ !t2
    JSR NePush
    JSR NeTopCode
    JSR NeAppend
    JMP NeMark

; Out: X = offset of the top state.
NeTop:
    LDA !sp
    DEC
    ASL
    ASL
    TAX
    RTS

NeTopCode:
    JSR NeTop
    ; fall through

; In: X = offset of a state. Out: A = its code, carry clear.
NeStateCode:
    LDA !stk+1,X
    AND #$00FF
    CMP #$00FF
    BNE .medial
    LDA !stk,X              ; an initial alone
    AND #$00FF
    TAX
    LDA.l NeChoJ,X
.jamo
    AND #$00FF
    ASL
    TAX
    LDA.l NeJamoCode,X
    CLC
    RTS
.medial
    STA !t1
    LDA !stk,X
    AND #$00FF
    CMP #$00FF
    BNE .syllable
    LDX !t1                 ; a medial alone
    LDA.l NeJungJ,X
    BRA .jamo
.syllable
    STA !t0                 ; s = (initial * 21 + medial) * 28 + final
    ASL
    ASL
    STA !t2
    ASL
    ASL
    CLC
    ADC !t2
    ADC !t0
    ADC !t1
    STA !t2
    ASL
    ASL
    ASL
    ASL
    ASL
    SEC
    SBC !t2
    SBC !t2
    SBC !t2
    SBC !t2
    STA !t2
    LDA !stk+2,X
    AND #$00FF
    CLC
    ADC !t2
    STA !t2
    ASL
    TAX
    LDA.l NeSylCode,X
    CLC
    RTS

; Pushes (!t0, !t1, !t2).
NePush:
    JSR NeStateCode2
    INC !sp
    RTS

; (!t0, !t1, !t2) -> A = code, using the slot above the top of the stack.
NeStateCode2:
    LDA !sp
    ASL
    ASL
    TAX
    SEP #$20
    LDA !t0
    STA !stk,X
    LDA !t1
    STA !stk+1,X
    LDA !t2
    STA !stk+2,X
    REP #$20
    JMP NeStateCode

; Medial !t1 + jamo !key -> A = compound medial, carry set if none.
NeFindJungMix:
    LDX #$0000
-
    LDA.l NeJungMix,X
    AND #$00FF
    CMP #$00FF
    BEQ .none
    CMP !t1
    BNE +
    LDA.l NeJungMix+1,X
    AND #$00FF
    CMP !key
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

; Final !t2 + jamo !key -> A = double final, carry set if none.
NeFindJongMix:
    LDX #$0000
-
    LDA.l NeJongMix,X
    AND #$00FF
    CMP #$00FF
    BEQ .none
    CMP !t2
    BNE +
    LDA.l NeJongMix+1,X
    AND #$00FF
    CMP !key
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

incsrc "../work/font8_data.asm"
assert pc() <= $E0FFFF

org $E18000
incsrc "../work/font8_syl.asm"
assert pc() <= $E1FFFF
