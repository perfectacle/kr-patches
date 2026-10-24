; Load v1.0 and Japanese save files. A save stores script stream positions (the resume
; point and the backlog history), and every v1.1 position differs from both. v1.1 saves
; carry !MAGIC in bytes the game never uses; in a slot without it each position is
; translated through the tables written by tools/savemap.py before the game reads it.
; v1.0 positions are LoROM addresses in banks $20-$35. Japanese ones are a byte address
; in the Huffman text (banks $15-$1D) plus the bit number in the byte after it.
lorom

!MAGIC = $C311
!MARK = $7005B5             ; unused by the game; cleared to 0 when a slot is created
!MAP_V10 = $17              ; table banks: count, then (old 24 bit, new 24 bit) sorted by old
!MAP_JP = $19
!HISTORY = $70002A          ; 4 bytes per entry: position 24 bit, bit number
!HISTMAX = 235              ; entries that fit before $7003D6
!KEYLO = $7FFFE2
!KEYBK = $7FFFE4
!LO = $7FFFE6
!HI = $7FFFE8
!MID = $7FFFEA
!SLOT = $7FFFEC
!TMP = $7FFFEE

org $02A54F                 ; new slot: LDA $13 / STA $7005AF,X (8 bit A)
    JSL MarkNew
    NOP #2

org $02A83B                 ; autosave: LDA $005D / STA $7005B1 (16 bit A)
    JSL MarkSave
    NOP #3

org $02A6D3                 ; load, slot already copied to slot 0: LDA $7005AC
    JSL LoadSave

org $188000
MarkNew:
    LDA $13
    STA.l $7005AF,X
    LDA.b #!MAGIC
    STA.l !MARK,X
    LDA.b #!MAGIC>>8
    STA.l !MARK+1,X
    RTL

MarkSave:
    LDA.w $005D
    STA.l $7005B1
    LDA.w #!MAGIC
    STA.l !MARK
    RTL

LoadSave:
    LDA.l !MARK
    CMP.w #!MAGIC
    BEQ .done
    PHX
    PHY
    LDA.l $7005AE           ; bank of the resume point
    AND.w #$00FF
    SEC
    SBC.w #$0015
    CMP.w #$0009
    BCS +
    JSR SetName             ; Japanese save: its name is in Japanese codes
+   LDX.w #$05AC            ; the bit number follows at $05AF, as in the history entries
    JSR Translate
    LDA.l $70059A
    CMP.w #!HISTMAX
    BCC +
    LDA.w #!HISTMAX
+   TAY
    LDX.w #!HISTORY&$FFFF
-   CPY.w #$0000
    BEQ +
    JSR Translate
    INX #4
    DEY
    BRA -
+   LDA.w #!MAGIC
    STA.l !MARK
    LDA.w #$0000
    JSL $02A8B7             ; slot 0 checksum, as the autosave does
    STA.l $700020
    PLY
    PLX
.done:
    LDA.l $7005AC
    RTL

; X = offset in bank $70 of a saved position; replaced by the v1.1 address of the last
; table entry not above it, which is the start of the page it was on.
Translate:
    PHB
    PHY
    TXA
    STA.l !SLOT
    LDA.l $700000,X
    STA.l !KEYLO
    LDA.l $700002,X
    AND.w #$00FF
    STA.l !KEYBK
    SEC
    SBC.w #$0020
    CMP.w #$0016
    BCS +
    PEA.w !MAP_V10<<8|!MAP_V10
    BRA .search
+   LDA.l !KEYBK
    SEC
    SBC.w #$0015
    CMP.w #$0009
    BCC +
    JMP .skip
    ; bit offset = (file offset - $AE401) * 8 + bit; file offset = bank * $8000 + (addr & $7FFF)
+   LDA.l !KEYBK
    LSR
    STA.l !KEYBK
    LDA.w #$0000
    ROR
    STA.l !TMP
    LDA.l !KEYLO
    AND.w #$7FFF
    ORA.l !TMP
    SEC
    SBC.w #$E401
    STA.l !KEYLO
    LDA.l !KEYBK
    SBC.w #$000A
    STA.l !KEYBK
    LDY.w #$0003
-   LDA.l !KEYLO
    ASL
    STA.l !KEYLO
    LDA.l !KEYBK
    ROL
    STA.l !KEYBK
    DEY
    BNE -
    LDA.l $700003,X
    AND.w #$0007
    ORA.l !KEYLO
    STA.l !KEYLO
    PEA.w !MAP_JP<<8|!MAP_JP
.search:
    PLB
    PLB
    LDA.w #$0000
    STA.l !LO
    LDA.w $8000
    STA.l !HI
.loop:
    LDA.l !HI
    SEC
    SBC.l !LO
    CMP.w #$0002
    BCC .found
    LDA.l !LO
    CLC
    ADC.l !HI
    LSR
    STA.l !MID
    JSR Offset
    LDA.w $8004,X
    AND.w #$00FF
    CMP.l !KEYBK
    BCC .le
    BNE .gt
    LDA.w $8002,X
    CMP.l !KEYLO
    BEQ .le
    BCS .gt
.le:
    LDA.l !MID
    STA.l !LO
    BRA .loop
.gt:
    LDA.l !MID
    STA.l !HI
    BRA .loop
.found:
    LDA.l !LO
    JSR Offset
    LDA.w $8007,X
    AND.w #$00FF
    STA.l !TMP
    LDA.w $8005,X
    PHA
    LDA.l !SLOT
    TAX
    PLA
    STA.l $700000,X
    SEP #$20
    LDA.l !TMP
    STA.l $700002,X
    REP #$20
.skip:
    LDA.l !SLOT
    TAX
    PLY
    PLB
    RTS

; The Japanese default name 公平, as 코헤이, into the name entry buffer ($1BC9) and the
; name the script prints ($5F).
SetName:
    LDX.w #$0000
-   LDA.l DefaultName,X
    STA.l $70057A,X
    STA.l $7005D5,X
    INX
    INX
    CPX.w #DefaultName_end-DefaultName
    BCC -
    RTS

DefaultName:
    dw 1176, 1170, 514, $FFFF, $FFFF, $FFFF, $FFFF
DefaultName_end:

; X = A * 6
Offset:
    ASL
    STA.l !TMP
    ASL
    CLC
    ADC.l !TMP
    TAX
    RTS
