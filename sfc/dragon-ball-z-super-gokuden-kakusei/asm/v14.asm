; v1.4: names can use all 11,172 syllables, typed by composing jamo.
;
; tools/font16.py puts the new 16x16 glyphs (codes !k16_first-, 1 bpp) in banks $C0- and writes
; the jamo grid of the name entry. This file makes the renderer draw the new codes and turns the
; name entry into a jamo keyboard. The password entry has its own loop and tables and is left
; as it is.
;
; The five names are 25 codes at $0C00, five per name; $022B is the position the cursor of the
; name list is on and $0229 the grid cell. A syllable being composed sits at $022B; a stack of
; states (initial, medial, final), one per jamo typed into it, lets B take back one jamo at a time.
lorom

incsrc "../work/font16_defs.asm"

!names  = $7E0C00
!cell   = $7E0229
!pos    = $7E022B
!blank  = $0272
!done   = $0055             ; grid cell of 입력완료; cells from here on are that button
!buf    = $1600             ; $1600-$161F and $1700-$171F: one glyph in the layout of a sheet row

; WRAM $7F:FF00- holds no game data (written by nothing after boot through new game, password
; and battle play); only the name entry uses it.
!sp    = $FF00              ; states on the stack (0 = not composing)
!stk   = $FF02              ; 6 states x 4 bytes: initial, medial, final
!t0    = $FF20
!t1    = $FF22
!t2    = $FF24
!t3    = $FF26
!key   = $FF28              ; jamo just chosen
!vowel = $FF2A              ; its medial
!lastp = $FF2C              ; position and code of our last write, to tell whether the
!lastc = $FF2E              ; cursor still stands on what we wrote
!here  = $FF30              ; 1: the next character goes at $022B itself, not after it

; ---------------------------------------------------------------------------
; Renderer ($80:9B2C): codes from $0900 take the third sheet; the new codes branch off here.

org $809B7E                 ; SEC / SBC #$0900 / STA $2F
    JML K16Sheet
    NOP #2

; ---------------------------------------------------------------------------
; Name entry ($81:8959 loop)

org $81891A                 ; the help text: LDY #0 / LDA $84A3E0,X with X = $01E0
    LDY #$0000
    LDA.l NeHelp-$01E0,X
org $8189A6                 ; STZ $0229
    JSR NeInit
org $8189DD                 ; A
    JMP NeA
org $8189E5                 ; B
    JMP NeB
org $818A0B                 ; X switched the grid page; it types a space now
    JMP NeSpace
org $818A26                 ; Y cleared every name: STZ $022B
    JSR NeInit2
org $818B70                 ; the grid, either page
    LDA.l NeGrid,X
org $818B82
    LDA.l NeGrid-$00F0,X
; The cursor moves on past empty cells. Each hook replaces STA $0229 / JMP $89BA.
org $818A58                 ; right
    JMP NeMvR
org $818A8D                 ; left
    JMP NeMvL
org $818AAF                 ; down
    JMP NeMvD
org $818AD1                 ; up
    JMP NeMvU

org $81DA60                 ; free in bank $81 (0xFF in the Japanese ROM and v1.3)
K16Sheet:
    CMP.w #!k16_first
    BCS .new
    SEC
    SBC #$0900
    STA $2F
    JML $809B84
.new
    ; The new glyphs live in banks $C0-, which have no low-RAM mirror, and the renderer reads
    ; its variables through the data bank. The glyph is copied to low RAM in the layout of a
    ; sheet row (top tiles, bottom tiles at +$100, plane 1 = plane 0) and drawn from bank $80.
    PHP
    REP #$30
    PHX
    PHY
    SEC
    SBC #$0900
    STA $2F
    SEC
    SBC.w #!k16_first-$0900
    PHA
    AND #$03FF              ; 32 bytes per glyph, $400 glyphs per bank
    ASL
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
    CLC
    ADC.w #!k16_bank0
    SEP #$20
    PHA
    PLB
    LDX #$0000
-
    LDA $8000,Y             ; row y: left, right; row y + 8 is 16 bytes on
    STA.l $7E0000|!buf,X
    STA.l $7E0000|(!buf+1),X
    LDA $8001,Y
    STA.l $7E0000|(!buf+$10),X
    STA.l $7E0000|(!buf+$11),X
    LDA $8010,Y
    STA.l $7E0000|(!buf+$100),X
    STA.l $7E0000|(!buf+$101),X
    LDA $8011,Y
    STA.l $7E0000|(!buf+$110),X
    STA.l $7E0000|(!buf+$111),X
    INY
    INY
    INX
    INX
    CPX #$0010
    BCC -
    LDA #$80
    PHA
    PLB
    REP #$30
    PLY
    PLX
    LDA.w #!buf
    STA $50
    STZ $27
    PLP
    JML $809B9A

; ---------------------------------------------------------------------------

NeInit:
    STZ $0229
    ; fall through
NeReset:
    LDA #$0000
    STA.l $7F0000|!sp
    LDA #$0001
    STA.l $7F0000|!here
    RTS

NeInit2:
    STZ $022B
    BRA NeReset

; In: A = the new cell. An empty cell sends the cursor on in the same direction.
NeMvR:
    STA $0229
    JSR NeEmpty
    BNE +
    JMP $8A2B
+
    JMP $89BA
NeMvL:
    STA $0229
    JSR NeEmpty
    BNE +
    JMP $8A5E
+
    JMP $89BA
NeMvD:
    STA $0229
    JSR NeEmpty
    BNE +
    JMP $8A93
+
    JMP $89BA
NeMvU:
    STA $0229
    JSR NeEmpty
    BNE +
    JMP $8AB5
+
    JMP $89BA

; In: A = cell. Out: Z set when it is empty.
NeEmpty:
    CMP.w #!done
    BCS .button
    TAX
    LDA.l NeCell,X
    AND #$00FF
    CMP #$00FF
    RTS
.button
    LDA #$0001
    RTS

NeA:
    REP #$30
    LDA.l !cell
    CMP.w #!done
    BCC +
    JMP $8B20               ; 입력완료: on to the next name, or the end
+
    TAX
    LDA.l NeCell,X
    AND #$00FF
    CMP #$00FF
    BEQ .out
    PHB
    PEA $7F7F
    PLB
    PLB
    JSR NeJamo
    PLB
.out
    JMP $89BA

NeB:
    REP #$30
    PHB
    PEA $7F7F
    PLB
    PLB
    JSR NeGuard
    LDA !here
    BNE .plain
    LDA !sp
    BEQ .delete
    DEC !sp
    BEQ .delete             ; the syllable's first jamo: delete the character
    JSR NeTopCode
    JSR NeWrite
    BRA .out
.delete
    STZ !sp
    LDA.w #!blank
    JSR NeWrite
    LDA.l !pos
    JSR NeMod5
    BEQ .first
    LDA.l !pos
    DEC
    STA.l !pos
    JSR NeMark              ; continue after the previous character
    BRA .out
.first
    LDA #$0001
    STA !here
.out
    PLB
    JMP $89BA
.plain
    ; Not on our last write: like the game's B the cursor goes back one position, then on
    ; past the trailing spaces of that name, so typing continues after its last character.
    LDA.l !pos
    BEQ .out
    DEC
-
    STA.l !pos
    JSR NeMod5
    BEQ .out
    LDA.l !pos
    ASL
    TAX
    LDA.l !names-2,X
    CMP.w #!blank
    BNE .out
    LDA.l !names,X
    CMP.w #!blank
    BNE .out
    LDA.l !pos
    DEC
    BRA -

NeSpace:
    REP #$30
    PHB
    PEA $7F7F
    PLB
    PLB
    JSR NeGuard
    JSR NeRoom
    BCS +                   ; no room: keep the syllable and its stack
    STZ !sp
    LDA.w #!blank
    JSR NeStart
+
    PLB
    JMP $89BA

; DB = $7F from here on; game variables are read long.

; Forget the stack and write at the cursor when it no longer stands on our last write
; (moved by B, 입력완료 or Y, or a new screen).
NeGuard:
    LDA !sp
    CMP #$0007
    BCS .clear              ; WRAM is not cleared at power-on
    LDA.l !pos
    CMP !lastp
    BNE .clear
    ASL
    TAX
    LDA.l !names,X
    CMP !lastc
    BEQ .ok
.clear
    STZ !sp
    LDA #$0001
    STA !here
.ok
    RTS

; In: A = position.
NeMark:
    STA !lastp
    ASL
    TAX
    LDA.l !names,X
    STA !lastc
    RTS

; A = A mod 5, flags as CMP #0. A < 30.
NeMod5:
-
    CMP #$0005
    BCC +
    SBC #$0005
    BRA -
+
    CMP #$0000
    RTS

; Carry clear when a new character fits: at the cursor, or after it in the same name.
NeRoom:
    LDA !here
    BNE .yes
    LDA.l !pos
    JSR NeMod5
    CMP #$0004
    BEQ .no
.yes
    CLC
    RTS
.no
    SEC
    RTS

; A = code: replaces the character at the cursor.
NeWrite:
    PHA
    LDA.l !pos
    ASL
    TAX
    PLA
    STA.l !names,X
    LDA.l !pos
    JSR NeMark
    ; fall through

NeRedraw:
    PHB
    PHK
    PLB
    JSR $8BAA
    PLB
    REP #$30
    RTS

; A = code: a new character, at the cursor or after it; the rest of the name is cleared.
; Carry set when the name is full.
NeStart:
    PHA
    JSR NeRoom
    BCS .full
    LDA !here
    BNE +
    LDA.l !pos
    INC
    STA.l !pos
+
    STZ !here
    LDA.l !pos
    INC
    STA !t3
-
    LDA !t3
    JSR NeMod5
    BEQ +
    LDA !t3
    ASL
    TAX
    LDA.w #!blank
    STA.l !names,X
    INC !t3
    BRA -
+
    PLA
    JSR NeWrite
    CLC
    RTS
.full
    PLA
    SEC
    RTS

; A = jamo index.
NeJamo:
    STA !key
    TAX
    LDA.l NeJJung,X
    AND #$00FF
    STA !vowel
    JSR NeGuard
    LDA !here
    BNE .new
    LDA !sp
    BNE .compose
.new
    JSR NeRoom
    BCS .ret
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
    JMP NeStart
.ret
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
    JMP NeWrite

; A vowel after a final: the final (its last consonant if double) starts the next syllable.
.split
    JSR NeRoom
    BCC +
    RTS                     ; no room for the next syllable
+
    LDX !t2
    LDA.l NeJongRest,X
    AND #$00FF
    STA !t2
    LDA.l NeJongMove,X
    AND #$00FF
    PHA
    JSR NeStateCode2        ; the syllable without what moves; NeStart below redraws
    PHA
    LDA.l !pos
    ASL
    TAX
    PLA
    STA.l !names,X
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
    JMP NeStart

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

; In: X = offset of a state. Out: A = its code.
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
    ASL
    TAX
    LDA.l NeSylCode,X
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

incsrc "../work/font16_data.asm"
assert pc() <= $81FFFF

org $E08000
incsrc "../work/font16_syl.asm"
assert pc() <= $E0FFFF
