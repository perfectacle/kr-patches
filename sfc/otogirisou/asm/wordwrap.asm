; Word wrap for the dialogue. The engine wraps per character ($00:A777), which is fine for
; Japanese but breaks Korean words in half. Before a space, or after a wide comma, period
; or exclamation mark (glyphs that already contain the gap), measure the following word from the script stream
; and break the line before it if it would not fit.
; A space that breaks the line is placed left of the margin so the new line is not indented.
; After such a mark the break is deferred to the next character through !PENDING.
lorom

!SPACE = 1247
!COMMA = 1478
!PERIOD = 1479
!EXCLAIM = 1482
!WIDTHS = $1EF000           ; glyph width per code (1 byte), written by tools/mkfont.py
!PENDING = $7FFFE0          ; == !MAGIC: start a new line before the next character
!MAGIC = $5A3C              ; WRAM is not cleared at power-on, so a plain flag could start set
!LOOKAHEAD = 80             ; bytes; a word longer than this is left to the per-character wrap

org $00A777                 ; REP #$30 / CLC / LDA $1A83 at the head of the wrap check
    JSL WordWrap
    NOP #2

org $1E8000
WordWrap:
    REP #$30
    LDA.l !PENDING
    CMP.w #!MAGIC
    BNE +
    LDA #$0000
    STA.l !PENDING
    JSR NewLine
+
    LDA $1A7D
    CMP.w #!SPACE
    BNE .mark
    LDA $5D                 ; a space inside the player name buffer: the stream at [$52]
    AND #$00FF              ; is not what follows it, so leave that space to the engine
    BEQ .measure
    JMP .done
.mark:
    LDA $1A7D
    CMP.w #!COMMA
    BEQ .measure
    CMP.w #!PERIOD
    BEQ .measure
    CMP.w #!EXCLAIM
    BEQ .measure
    JMP .done
.measure:
    PHX
    PHY
    LDA $1A83               ; x after this character
    CLC
    ADC $18DB
    CLC
    ADC $1A7F
    PHA
    LDY #$0000
.next:
    TYA
    CLC
    ADC $52
    BCS .measured           ; do not follow the stream across a bank boundary
    CPY.w #!LOOKAHEAD
    BCS .measured
    LDA [$52],Y             ; symbols are stored big-endian
    XBA
    AND #$1FFF
    CMP #$1000
    BCS .measured
    CMP.w #!SPACE
    BEQ .measured
    TAX
    LDA.l !WIDTHS,X
    AND #$00FF
    BEQ .skip               ; hanging punctuation (width 0 in the table) takes no room
    CLC
    ADC $18DB
    CLC
    ADC $01,S
    STA $01,S
.skip:
    INY
    INY
    BRA .next
.measured:
    PLA
    CPY #$0000
    BEQ .fits               ; nothing follows (control code next)
    SEC
    SBC $18DB               ; no spacing after the last character
    CMP $18CF
    BCC .fits
    LDA $1A7D
    CMP.w #!SPACE
    BNE .defer
    JSR NewLine
    LDA $1A7F               ; draw the space left of the margin
    SEC
    SBC $1A83
    SEC
    SBC $18DB
    STA $1A7F
    BRA .fits
.defer:
    LDA.w #!MAGIC
    STA.l !PENDING
.fits:
    PLY
    PLX
.done:
    REP #$30
    CLC
    LDA $1A83
    RTL

NewLine:
    LDA $18CB
    STA $1A7F
    LDA $1A81
    CLC
    ADC $18D3
    STA $1A81
    RTS
