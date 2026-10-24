; v1.3: the Hangul mode of the name entry screen becomes one page of jamo that compose into
; syllables, and names may use any KS X 1001 syllable.
;
; The name stays a list of dialogue-font codes ($1BC9, 6 codes, $1AA3 = count), so saves and
; the dialogue ({20}) are unchanged. The syllable being composed is always the last code in
; the name; a stack of states (initial, medial, final) remembers how it was typed so B takes
; one jamo back at a time. Every write goes through the screen's own routine ($02:B334),
; which stores the code and draws it. The jamo and the syllables the font lacks are one
; extra font group (tools/namefont.py) whose data is in bank $36.
lorom

incsrc "../build/name_defs.asm"

!ne_append = $B334          ; bank $02: A = code, stores it at $1BC9 + $1AA3 * 2, draws it, $1AA3++
!ne_page1  = $02AAB4        ; Hangul page 1: the jamo page (tools/namefont.py)
!ne_rts_a  = $02B2D9        ; an RTS that ends the A-button routine
!ne_rts_b  = $02B254        ; an RTS that ends the delete routine
!ne_count  = $7E1AA3
!ne_name   = $7E1BC9
!ne_max    = 6

; WRAM $7F:E000-$E03F is free (the game uses $7F:0000-$B6FF and $7F:FF00-, v1.2 $7F:C000-$D8FF).
!sp    = $E000              ; states on the stack (0 = not composing)
!stk   = $E002              ; 6 states x 4 bytes: initial, medial, final ($FF = none)
!t0    = $E020
!t1    = $E022
!t2    = $E024
!t3    = $E026
!key   = $E028              ; jamo just chosen
!vowel = $E02A              ; its medial
!lastn = $E02C              ; name count and last code after our last write, to tell
!lastc = $E02E              ; whether the name still ends in the syllable we were composing
!dir   = $7FE030            ; cursor moves: row step ($0100 down, $FF00 up)
!row   = $7FE034
!col   = $7FE036
!dist  = $7FE038

; Font decoder: the bank of the glyph data was always $1F (LDA #$1F / STA $16).
org $00A56C
    JSL NeBank

; Left/right on the menu no longer turn Hangul pages; right enters the grid.
org $02B114
    db $80                  ; BNE $B123 -> BRA: left does nothing
org $02B12F
    db $80                  ; BNE $B15D -> BRA: right enters the grid

; The 한글 button lost its page number: no digit, and the ◀ ▶ tiles of the button picture
; (BG1 map, run-length data of the Japanese ROM) become plain button face.
org $02B5C5
    NOP #3                  ; was JSR $B6AF: draw the page number
org $07E4F7
    db $27                  ; ◀ upper half
org $07E4FA
    db $2C                  ; ▶ upper half
org $07E513
    db $27                  ; ◀ lower half
org $07E516
    db $2C                  ; ▶ lower half

; Menu order 한글, 영문자, 숫자, so the screen opens on the jamo page: the page tables (the
; menu index is the page number) and the labels swap places. 한글 lines up with 숫자, whose
; string starts with a blank.
org $02B18E
    dw !ne_page1, $A9E4, $AA4C
org $02B849
    dw !ne_page1, $A9E4, $AA4C
org $02B5CC
    dw !ne_page1            ; first page drawn
org $02B586
    dw $0044                ; x of the top label
org $02B592
    dw $A9DE                ; 한글
org $02B598
    dw $0035
org $02B5A4
    dw $A9CA                ; 영문자
org $02B5AA
    dw $0038
org $02B5B6
    dw $A9D4                ; 숫자

; The grid cursor skips empty cells on every page.
org $02B15D
    JML NeEnter             ; entering the grid
    NOP
org $02B1D8
    JML NeUp
org $02B1ED
    JML NeDown
org $02B20A
    JML NeRight
org $02B220
    JML NeLeft

; A on the grid, after its sound (JSL $00965D)
org $02B282
    JML NeA

; Delete (B, and ← on the bottom row): LDA $1AA3 / BEQ
org $02B23F
    JML NeDel
    NOP

org $02D8BD                 ; free in bank $02 (FF in the Japanese ROM and in v1.2)
NeCallAppend:
    PHB
    PHK
    PLB
    JSR !ne_append
    PLB
    RTL
assert pc() <= $02DA00

org $36D000
; In: stack = return address, then the group offset (X, 5 bytes per group). M 8-bit.
NeBank:
    REP #$20
    LDA $04,S
    CMP.w #!ne_new_group*5
    SEP #$20
    LDA #$1F
    BCC +
    LDA #!ne_font_bank
+
    STA $16
    RTL

NeA:
    JSL $00965D
    REP #$30
    LDA $1AA7
    BNE .orig               ; page 0 = the jamo page
    LDA $1A9F
    CMP #$0A00
    BCS .orig               ; bottom row: ← 한칸 띄어쓰기 END
    XBA
    AND #$00FF
    STA $10
    ASL
    ASL
    CLC
    ADC $10                 ; row * 5
    STA $10
    LDA $1A9F
    AND #$00FF
    CLC
    ADC $10
    ASL
    TAX
    LDA.l !ne_page1,X
    BEQ .done               ; empty cell
    SEC
    SBC.w #!ne_jamo_first
    PHB
    PEA $7F7F
    PLB
    PLB
    JSR NeJamo
    PLB
.done
    REP #$30
    JML !ne_rts_a
.orig
    JML $02B286

NeDel:
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
    JML !ne_rts_b
.plain
    STZ !sp
    PLB
    LDA $1AA3
    JML $02B242             ; BEQ / DEC / ... of the original

; Cursor moves. $1A9F = column, $1AA0 = row; row $0A is the command row (columns 1-4).
; In: A = row/column like $1A9F. Out: carry set if the cursor may stop there. A is kept.
NeCell:
    PHA
    CMP #$0A00
    BCC .grid
    AND #$00FF
    CMP #$0001
    PLA
    RTS
.grid
    XBA
    AND #$00FF
    STA $10
    ASL
    ASL
    ADC $10
    STA $10
    LDA $01,S
    AND #$00FF
    CLC
    ADC $10
    ASL
    TAY
    LDA $1AA7
    ASL
    TAX
    LDA.l $02B849,X
    STA $10
    SEP #$20
    LDA #$02
    STA $12
    REP #$20
    LDA [$10],Y
    CMP #$0001
    PLA
    RTS

NeEnter:
    INC $1AA1
    STZ $CC
    LDA $1A9F
    JSR NeCell
    BCS +
    STZ $1A9F               ; the cell is empty on this page: start at the top left
+
    JML $02B162             ; RTS

NeRight:
    LDA $1A9F
-
    INC
    PHA
    AND #$00FF
    CMP #$0005
    PLA
    BCS .stay
    JSR NeCell
    BCC -
    STA $1A9F
.stay
    JML $02B1D0             ; RTS

NeLeft:
    LDA $1A9F
-
    BIT #$00FF
    BEQ .menu               ; nothing to the left: back to the menu, as from column 0
    DEC
    JSR NeCell
    BCC -
    STA $1A9F
    BIT #$00FF
    BNE +
    JSL $0092F7
+
    JML $02B1D0
.menu
    JML $02B260

NeUp:
    LDA #$FF00
    BRA NeVert
NeDown:
    LDA #$0100
; The next cell in the same column; if the column has none, the nearest cell of the next
; row that has one (left first on a tie).
NeVert:
    STA.l !dir
    LDA $1A9F
-
    CLC
    ADC.l !dir
    CMP #$0B00
    BCS .near               ; past the command row, or above row 0
    JSR NeCell
    BCC -
    BRA .found
.near
    LDA $1A9F
    AND #$00FF
    STA.l !col
    LDA $1A9F
.row
    AND #$FF00
    CLC
    ADC.l !dir
    CMP #$0B00
    BCS .stay
    STA.l !row
    LDA #$0001
    STA.l !dist
.try
    LDA.l !col
    SEC
    SBC.l !dist
    BMI +
    ORA.l !row
    JSR NeCell
    BCS .found
+
    LDA.l !col
    CLC
    ADC.l !dist
    CMP #$0005
    BCS +
    ORA.l !row
    JSR NeCell
    BCS .found
+
    LDA.l !dist
    INC
    STA.l !dist
    CMP #$0005
    BCC .try
    LDA.l !row
    BRA .row
.found
    STA $1A9F
.stay
    JML $02B1D0

; DB = $7F from here on; game variables are read long.

; Forget the composing stack if the name no longer ends in the syllable we wrote.
NeGuard:
    LDA !sp
    BEQ .ok
    CMP #$0007
    BCS .clear              ; WRAM is not cleared at power-on
    LDA.l !ne_count
    AND #$00FF
    CMP !lastn
    BNE .clear
    DEC
    ASL
    TAX
    LDA.l !ne_name,X
    CMP !lastc
    BEQ .ok
.clear
    STZ !sp
.ok
    RTS

NeMark:
    LDA.l !ne_count
    AND #$00FF
    STA !lastn
    JSR NeTopCode
    STA !lastc
    RTS

NeAppend:
    JSL NeCallAppend
    RTS

; A = code: replaces the last character.
NeRewrite:
    PHA
    LDA.l !ne_count
    DEC
    STA.l !ne_count
    PLA
    JSL NeCallAppend
    RTS

; A = jamo.
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
    LDA.l !ne_count
    AND #$00FF
    CMP.w #!ne_max
    BCS .refuse
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
.refuse
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
    BCS .refuse2
    BRA .replace
+
    LDA !t2
    BNE .split
    JSR NeFindJungMix
    BCS .new2
    STA !t1
    JSR NePush
    BCS .refuse2
    BRA .replace
.refuse2
    RTS
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
    BEQ .new2                ; ㄸ ㅃ ㅉ are never finals
    STA !t2
    JSR NePush
    BCS .new2
    BRA .replace
.double
    JSR NeFindJongMix
    BCS .new2
    STA !t2
    JSR NePush
    BCS .new2
.replace
    JSR NeTopCode
    JSR NeRewrite
    JMP NeMark

; A vowel after a final: the final (its last consonant if double) starts the next syllable.
.split
    LDA.l !ne_count
    AND #$00FF
    CMP.w #!ne_max
    BCS .refuse2
    LDX !t2
    LDA.l NeJongRest,X
    AND #$00FF
    STA !t2
    LDA.l NeJongMove,X
    AND #$00FF
    PHA
    JSR NeStateCode2        ; the syllable without what moves
    BCS .drop1
    PHA
    LDA $03,S
    STA !t0
    LDA !vowel
    STA !t1
    STZ !t2
    JSR NeStateCode2        ; the next syllable
    BCS .drop2
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
.drop2
    PLA
.drop1
    PLA
    RTS

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

; In: X = offset of a state. Out: A = its code, carry set if no glyph has it.
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
    CLC
    ADC.w #!ne_jamo_first
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
    STZ !t0                 ; binary search in NeKsSyl: low
    LDA.w #!ne_ks_count
    STA !t1                 ; high (exclusive)
.search
    LDA !t0
    CMP !t1
    BCS .missing
    CLC
    ADC !t1
    LSR
    STA !t3
    ASL
    TAX
    LDA.l NeKsSyl,X
    CMP !t2
    BEQ .found
    BCS .lower
    LDA !t3
    INC
    STA !t0
    BRA .search
.lower
    LDA !t3
    STA !t1
    BRA .search
.missing
    SEC
    RTS
.found
    LDA.l NeKsCode,X
    CLC
    RTS

; Pushes (!t0, !t1, !t2) if a glyph has it. Out: carry set, nothing pushed, if none does.
NePush:
    JSR NeStateCode2
    BCS +
    INC !sp
+
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

incsrc "../build/name_data.asm"
assert pc() <= $36FFFF
