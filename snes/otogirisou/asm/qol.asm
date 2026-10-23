; Kamaitachi no Yoru style chapter select and ending list, plus the yellow backlog text
; and the last chapter on the bookmark screen.
; Select during a key wait opens a menu written as script into WRAM and shown by the
; engine's own choice code. A chapter entry runs {44:id} and then a plain script jump to
; the chapter start, so the jump works like any choice in the game: the chapter's first
; page sets its own scene. "Back" jumps to the start of the page the menu was opened on.
; Records live in SRAM after the four save slots; data tables come from tools/qol.py.
lorom

!RANGES = $1B8000
!STARTS = $1B8200
!SCENES = $1BF000           ; 8 bytes per chapter: scene code before the jump (tools/qol.py)
!MUSIC = $1BF100            ; 8 bytes per chapter: looping sounds playing at its start, $FF ends
!LOOPS = $1BF200            ; bitmap of the sound numbers that are music or ambient loops
!ENDINGS = $1B8300
!STRPTR = $1B8400
!S_MENU = 0
!S_NEXT = 1
!S_BACK = 2
!S_ENDLIST = 3
!S_CHLIST = 4
!S_ALL = 5
!S_CH = 8
!S_SEEN = 40
!S_UNSEEN = 60
!S_ENDHDR = 80
!NENDINGS = 18
!ENDPERPAGE = 6

!MAGIC = $514C
!SRAM = $701800             ; magic, then the slot records
!SLOTREC = $701810          ; 16 bytes per slot 1-3
!REC_LAP = 0                ; chapters read this playthrough (32 bits)
!REC_ALL = 4                ; chapters ever read
!REC_END = 8                ; endings seen
!REC_LAST = 12              ; last chapter read
!REC_V17 = 13               ; var 17 when chapter with flag 1 was entered
!REC_HAS17 = 14

!MENU = $7FCFF0             ; nonzero while the menu script runs
!BUF = $7FCFF2              ; buffer the next page goes to
!TMP = $7FCFF4
!TMP2 = $7FCFF6
!TMP3 = $7FCFF8
!TMP4 = $7FCFFA
!CHAPLIST = $CF00           ; menu work, bank $7F (DB = $7F while a page is written)
!CHAPCOUNT = $CFE0
!PAGESKIP = $CFE2
!PAGEN = $CFE4
!CHAPREC = $CFE6
!MODE = $CFE8
!CAP = $CFEA
!MASKOFF = $CFEC
!NEXT = $CFEE
!PAGEN2 = $CFDC
!KEEP = $7FCF40            ; engine state the menu's choices change, put back on leaving:
                            ; $1BB1-$1BB8, $1BBF, $1BC1, $1BC5, choice var
!RESUME = $7FCF50           ; start of the page the menu was opened on (24 bit)
!LEAVETO = $7FCF54          ; chapter chosen (1-31) or 0 for "back", acted on at the jump out
!SCENEOF = $7FCF56          ; offset of the scene code that goes before a jump
!SOUNDS = $7FCF60           ; bitmap of the looping sounds now playing (32 bytes)
!SNDNUM = $7FCF58           ; PutMusic's sound number (!TMP-!TMP4 belong to PutOption)
!MUSBUF = $7FCF80           ; the target's loop list for PutMusic, $FF ends (8 bytes)
!SCNBUF = $7FCF88           ; the target's scene code for PutScene, $FFFF ends (8 bytes)
!NOSCENE = !SCENES+(31*8)    ; an empty scene code
!BUFA = $C000               ; page buffers in bank $7F
!BUFB = $C800
!CHOICEVAR = 419            ; var the menu choices keep their memory bits in (unused by the script)

!TEXTCOLOR = $000C9B        ; CGRAM shadow, text palette color 1
!READCOLOR = $23BF          ; pages read again in the backlog are shown in yellow
!SAVEDCOLOR = $7E1FF2
!CUR_SLOT = $700022         ; slot the working copy belongs to
!VAR17 = $001C00            ; $1BEF + 17

; ---------------------------------------------------------------- hooks
org $009CF9                 ; key wait: LDA $CC / AND #$8000 (X opens the backlog)
    JSL SelCheck
    NOP

org $02A79C                 ; autosave: LDA $1BBF / ASL / ASL
    JSL AutoSave
    NOP

org $02C120                 ; jump: $10-$12 -> $52-$54 (8 bit A)
    JML JumpHook

; The layout pass ($00:AB5A) also runs codes below $28 while it reads ahead, so the menu
; action must be one of the codes it skips.
org $00F390+($44*2)         ; {44}, unused by the script, becomes the menu action
    dw Cmd44Tramp
org $00F41E+($44*2)         ; one argument
    dw $0001

; Sound codes, to know which loops play when the menu jumps elsewhere
org $00F390+($39*2)
    dw Snd39
org $00F390+($3A*2)
    dw Snd3A
org $00F390+($3B*2)
    dw Snd3B
org $00F390+($3C*2)
    dw Snd3C
org $00F390+($3D*2)
    dw Snd3D

org $02A56F                 ; scenario pick at a new playthrough: REP #$30 / AND #$00FF
    JSL LapHook
    NOP

org $02A4D1                 ; new slot: AND #$00FF / STA $30
    JSL NewSlot
    NOP

org $01F3BB                 ; backlog (X) entered: REP #$30 / LDA $1BBF
    JSL BacklogIn
    NOP
org $01F421                 ; backlog left: LDA #$00C0 / STA $0A2D
    JSL BacklogOut
    NOP
    NOP

org $02B955                 ; bookmark screen, one slot: name, playthrough, pages, choices
    JSL ShioriSlot
    NOP #8

org $00CE3F                 ; boot: logo
    JSL BootLogo

; ---------------------------------------------------------------- bank $00
org $00FAB0
Cmd44Tramp:
    JSR $ADE1
    JSL Cmd44
    RTS

RemoveCursor:
    JSR $9C6B
    RTL

TextUpload:
    JSR $A426
    RTL

; What the engine does after a jump code: copy $52 to the look-ahead's position, forget
; what it loaded ahead and restart it. A scene code waits for the look-ahead to have
; loaded its scene, so a page put in place outside a jump or a choice needs this.
Resync:
    REP #$30
    JSR $9A5A
    RTL

; The sound code handlers ($A8F1, $A8FE, $A8F8, $A908, $A926) with the sound number
; reported to the loop record on the way.
Snd39:
    JSR $ADE1
    JSL SoundOn
    JSR $CD60
    RTS
Snd3A:
    JSR $ADE1
    TAX
    JSR $ADE1
    JSL SoundOn
    JMP $CD69
Snd3B:
    JSR $ADE1
    JSL SoundOff
    JMP $CD45
Snd3C:
    JSR $ADE1
    TAX
    JSR $ADE1
    JSL SoundOff
    JMP $CD4E
Snd3D:
    REP #$30
    JSR $ADE1
    JSL SoundOn
    PHA
    JSR $CD60
    PLA
    JMP $CDF2

; ---------------------------------------------------------------- bank $1A
org $1A8000

; X = slot record offset in bank $70 for slot A (1-3); carry set if A is not a slot
RecOffset:
    AND.w #$00FF
    BEQ .no
    CMP.w #$0004
    BCS .no
    DEC
    ASL #4
    TAX
    CLC
    RTS
.no:
    SEC
    RTS

; ------------------------------------------------ boot
BootLogo:
    PHP
    REP #$30
    LDA.l !SRAM
    CMP.w #!MAGIC
    BEQ +
    LDX.w #$004E
-   LDA.w #$0000
    STA.l !SRAM,X
    DEX
    DEX
    BPL -
    LDA.w #!MAGIC
    STA.l !SRAM
+   LDA.w #$0000
    STA.l !MENU
    LDX.w #$001E
-   STA.l !SOUNDS,X
    DEX
    DEX
    BPL -
    PLP
    JML $028000

; The NMI uploads the CGRAM shadow when $B5 bit 3 is set.
BacklogIn:
    REP #$30
    LDA.l !TEXTCOLOR
    STA.l !SAVEDCOLOR
    LDA.w #!READCOLOR
    BRA SetTextColor

BacklogOut:
    REP #$30
    LDA.l !SAVEDCOLOR
    JSR SetTextColor_set
    LDA.w #$00C0
    STA.l $000A2D
    RTL

SetTextColor:
    JSR .set
    LDA.l $001BBF
    RTL
.set:
    STA.l !TEXTCOLOR
    SEP #$20
    LDA.l $0000B5
    ORA.b #$08
    STA.l $0000B5
    REP #$20
    RTS

; ------------------------------------------------ bookmark screen
; One slot ($1A9F = 0-2) as the game draws it, except that the second line shows the
; last chapter read instead of the page and choice counts once there is one.
ShioriSlot:
    REP #$30
    LDA.w #$004A            ; name
    STA.l $001A7F
    LDA.w #$0017
    JSR SlotY
    JSR SlotOffset
    TXA
    CLC
    ADC.w #$057A
    JSL $02B685
    LDA.w #$00D0            ; "n 번째"
    STA.l $001A7F
    LDA.w #$0017
    JSR SlotY
    LDX.w #$A9BC
    JSR DrawStr02
    LDA.w #$00A8
    STA.l $001A7F
    JSR SlotOffset
    LDA.l $700024,X
    INC
    JSR DrawNum4
    LDA.l $001A9F
    INC
    JSR RecOffset
    BCS .counts
    LDA.l !SLOTREC+!REC_LAST,X
    AND.w #$00FF
    BEQ .counts
    CLC
    ADC.w #!S_CH
    PHA
    LDA.w #$004A
    STA.l $001A7F
    LDA.w #$0030
    JSR SlotY
    PLA
    JSR DrawStr1B
    RTL
.counts:
    LDA.w #$0068            ; "n 페이지"
    STA.l $001A7F
    LDA.w #$0030
    JSR SlotY
    LDX.w #$A9C2
    JSR DrawStr02
    LDA.w #$004A
    STA.l $001A7F
    JSR SlotOffset
    LDA.l $700028,X
    INC
    JSR DrawNum3
    LDA.w #$00A8            ; choices tried
    STA.l $001A7F
    LDA.w #$0030
    JSR SlotY
    JSR SlotOffset
    LDA.l $700026,X
    JSR DrawNum4
    RTL

SlotY:                      ; $1A81 = slot * $48 + A
    PHA
    LDA.l $001A9F
    ASL #3
    STA.l !TMP
    ASL #3
    CLC
    ADC.l !TMP
    CLC
    ADC $01,S
    STA.l $001A81
    PLA
    RTS

SlotOffset:                 ; X = offset of slot $1A9F + 1 in bank $70
    LDA.l $001A9F
    INC
    JSL $02A95E
    RTS

Glyph:                      ; A = character code, drawn at $1A7F/$1A81
    STA.l $001A7D
    JSL $009595
    JSL $00958D
    JSL $00959D
    JSL $00957D
    RTS

DrawStr02:                  ; X = string in bank $02 (little endian, ends in $FFFF)
-   LDA.l $020000,X
    CMP.w #$FFFF
    BEQ +
    PHX
    JSR Glyph
    PLX
    INX
    INX
    BRA -
+   RTS

DrawStr1B:                  ; A = string id (script order, big endian)
    ASL
    TAX
    LDA.l !STRPTR,X
    TAX
-   LDA.l $1B0000,X
    CMP.w #$FFFF
    BEQ +
    XBA
    PHX
    JSR Glyph
    PLX
    INX
    INX
    BRA -
+   RTS

; Right-aligned numbers as the game draws them: leading zeros leave an 8 pixel gap.
DrawNum4:
    CMP.w #10000
    BCC +
    LDA.w #9999
+   STA.l !TMP2
    LDA.w #0
    STA.l !TMP3
    LDA.w #1000
    JSR NumDigit
    BRA DrawNum3_rest
DrawNum3:
    STA.l !TMP2
    LDA.w #0
    STA.l !TMP3
DrawNum3_rest:
    LDA.w #100
    JSR NumDigit
    LDA.w #10
    JSR NumDigit
    LDA.w #1
NumDigit:
    STA.l !TMP4
    LDX.w #0
    LDA.l !TMP2
-   CMP.l !TMP4
    BCC +
    SEC
    SBC.l !TMP4
    INX
    BRA -
+   STA.l !TMP2
    TXA
    BNE .draw
    LDA.l !TMP4
    DEC
    BEQ .draw
    LDA.l !TMP3
    BNE .draw
    LDA.l $001A7F
    CLC
    ADC.w #8
    STA.l $001A7F
    RTS
.draw:
    LDA.w #1
    STA.l !TMP3
    TXA
    ASL
    TAX
    LDA.l $02A992,X
    JMP Glyph

; ------------------------------------------------ looping sounds
; A = sound number; registers are kept. Only numbers marked in !LOOPS are recorded.
SoundOn:
    PHP
    REP #$30
    PHA
    PHX
    JSR SoundBit
    SEP #$20
    ORA.l !SOUNDS,X
    STA.l !SOUNDS,X
    REP #$30
    PLX
    PLA
    PLP
    RTL

SoundOff:
    PHP
    REP #$30
    PHA
    PHX
    JSR SoundBit
    SEP #$20
    EOR.b #$FF
    AND.l !SOUNDS,X
    STA.l !SOUNDS,X
    REP #$30
    PLX
    PLA
    PLP
    RTL

; A = sound number -> X = its byte in the bitmaps, A = its bit there if it is a loop, else 0
SoundBit:
    AND.w #$00FF
    PHA
    LSR #3
    TAX
    PLA
    AND.w #$0007
    PHX
    TAX
    LDA.l BitMask,X
    PLX
    AND.l !LOOPS,X
    AND.w #$00FF
    RTS

; ------------------------------------------------ records
NewSlot:
    AND.w #$00FF
    STA $30
    PHA
    PHX
    JSR RecOffset
    BCS +
    LDA.w #$0000
    STA.l !SLOTREC+0,X
    STA.l !SLOTREC+2,X
    STA.l !SLOTREC+4,X
    STA.l !SLOTREC+6,X
    STA.l !SLOTREC+8,X
    STA.l !SLOTREC+10,X
    STA.l !SLOTREC+12,X
    STA.l !SLOTREC+14,X
+   PLX
    PLA
    RTL

; A new playthrough starts when the script reaches the {1D} that ends a scenario (the
; engine checks for it itself; the code is never dispatched), so that is where the
; ending is recorded.
LapHook:
    REP #$30
    PHA
    PHX
    PHY
    JSL Ending
    PLY
    LDA $03,S
    JSR RecOffset
    BCS +
    LDA.w #$0000
    STA.l !SLOTREC+!REC_LAP,X
    STA.l !SLOTREC+!REC_LAP+2,X
+   PLX
    PLA
    AND.w #$00FF
    RTL

; A = bit number; sets it in the 32 bits at !SLOTREC+offset in Y, slot record X
SetBit:
    PHX
    PHA
    LSR #3
    STA.l !TMP
    TXA
    CLC
    ADC.l !TMP
    STA.l !TMP
    TYA
    CLC
    ADC.l !TMP
    TAX
    PLA
    AND.w #$0007
    PHX
    TAX
    LDA.l BitMask,X
    PLX
    SEP #$20
    ORA.l !SLOTREC,X
    STA.l !SLOTREC,X
    REP #$20
    PLX
    RTS

BitMask:
    db $01,$02,$04,$08,$10,$20,$40,$80

; Mark the chapter the script position $52-$54 belongs to.
CheckPos:
    LDA.l !MENU
    BEQ +
    RTS
+   LDA $54
    AND.w #$00FF
    STA.l !TMP2             ; bank
    SEC
    SBC.w #$0020
    CMP.w #$0016
    BCC +
    RTS
+
    LDA.l !RANGES
    STA.l !TMP3             ; entries left
    LDX.w #$0000
    LDA.w #$0000
    STA.l !TMP4             ; chapter of the last range at or before the position
-   LDA.l !TMP3
    BEQ .found
    LDA.l !RANGES+4,X       ; bank
    AND.w #$00FF
    CMP.l !TMP2
    BCC .le
    BNE .found
    LDA.l !RANGES+2,X
    CMP $52
    BEQ .le
    BCS .found
.le:
    LDA.l !RANGES+5,X
    AND.w #$00FF
    STA.l !TMP4
    INX #4
    LDA.l !TMP3
    DEC
    STA.l !TMP3
    BRA -
.found:
    LDA.l !TMP4
    BEQ .done
    JSR Register
.done:
    RTS

; A = chapter id
Register:
    STA.l !TMP4
    LDA.l !CUR_SLOT
    JSR RecOffset
    BCS .done
    LDA.l !TMP4
    DEC
    LDY.w #!REC_LAP
    JSR SetBit
    LDA.l !TMP4
    DEC
    LDY.w #!REC_ALL
    JSR SetBit
    SEP #$20
    LDA.l !TMP4
    STA.l !SLOTREC+!REC_LAST,X
    REP #$20
    LDA.l !TMP4
    ASL #2
    PHX
    TAX
    LDA.l !STARTS+3,X
    PLX
    AND.w #$0001
    BEQ .done
    SEP #$20
    LDA.l !VAR17
    STA.l !SLOTREC+!REC_V17,X
    LDA.b #$01
    STA.l !SLOTREC+!REC_HAS17,X
    REP #$20
.done:
    RTS

AutoSave:
    LDA.l !MENU
    BEQ +
    ; inside the menu nothing is saved: leave the autosave through its own exit
    PLA
    SEP #$20
    PLA
    REP #$20
    JML $02A7C5
+   PHB
    JSR CheckPos
    PLB
    LDA $1BBF
    ASL
    ASL
    RTL

JumpHook:                   ; 8 bit A, 16 bit X
    LDA $10
    STA $52
    LDA $11
    STA $53
    LDA $12
    STA $54
    PHP
    REP #$30
    PHA
    PHX
    PHY
    LDA.l !MENU
    BEQ +
    TDC                     ; the layout pass reads ahead with D = $0180; only the
    BNE +                   ; script reader itself (D = 0) leaves the menu
    LDA $54
    AND.w #$00FF
    CMP.w #$007F
    BEQ +
    JSR LeaveMenu
+   JSR CheckPos
    PLY
    PLX
    PLA
    PLP
    JML $02C12C

Ending:
    PHP
    REP #$30
    PHA
    PHX
    PHY
    LDX.w #$0000
-   LDA.l !ENDINGS,X
    CMP $52
    BNE +
    LDA.l !ENDINGS+2,X
    EOR $54
    AND.w #$00FF
    BEQ .found
+   INX #4
    CPX.w #!NENDINGS*4
    BCC -
    BRA .done
.found:
    TXA
    LSR #2
    PHA
    LDA.l !CUR_SLOT
    JSR RecOffset
    PLA
    BCS .done
    LDY.w #!REC_END
    JSR SetBit
.done:
    PLY
    PLX
    PLA
    PLP
    RTL

; ------------------------------------------------ menu
; Key wait hook: Select opens the menu. Z set skips the backlog check that follows.
SelCheck:
    LDA.l !MENU
    BNE .block
    LDA $CC
    BIT.w #$0020
    BNE .open
    AND.w #$8000
    RTL
.open:
    LDA.l !CUR_SLOT
    JSR RecOffset
    BCS .block
    LDA.w #$0001
    STA.l !MENU
    JSR KeepState
    JSL RemoveCursor
    REP #$30
    LDA.w #$0000
    STA.l $001A95
    STA.l $001A9D
    STA.l $001A93
    LDA.w #!BUFA
    STA.l !BUF
    JSR FlowOpen
.block:
    LDA.w #$0000
    RTL

; {44:arg}: 1-31 chapter, $40+n / $50+n chapter page n, $60+n ending page n, $7F back.
; For a chapter and for "back" the script then clears the page and jumps out by itself
; (see PutOption); the menu ends at that jump (JumpHook), so the page clear saves nothing.
Cmd44:
    PHP
    PHB
    REP #$30
    PHA
    LDA.w #$0000
    PHA
    PLB
    PLB
    PLA
    AND.w #$00FF
    CMP.w #$007F
    BEQ .back
    CMP.w #$0060
    BCS .endpage
    CMP.w #$0040
    BCS .chpage
    STA.l !LEAVETO
    JSL Resync              ; the look-ahead goes on into the stub and loads the scene
    BRA .done
.back:
    LDA.w #$0000
    STA.l !LEAVETO
    BRA .done
.chpage:
    JSR BuildChapters
    BRA .done
.endpage:
    AND.w #$001F
    JSR BuildEndings
.done:
    PLB
    PLP
    RTL

; The menu's own choices count as choices to the engine: they clear the backlog count,
; add to the choices-tried count and reset a few scene fields. Page clears add pages.
KeepState:
    LDX.w #$0006
-   LDA.l $001BB1,X
    STA.l !KEEP,X
    DEX
    DEX
    BPL -
    LDA.l $001BBF
    STA.l !KEEP+8
    LDA.l $001BC1
    STA.l !KEEP+10
    LDA.l $001BC5
    STA.l !KEEP+12
    LDA.l $001BEF+!CHOICEVAR
    STA.l !KEEP+14
    LDA.l $7005AC           ; the autosave at the start of this page
    STA.l !RESUME
    LDA.l $7005AE
    AND.w #$00FF
    STA.l !RESUME+2
    RTS

PutBackState:
    LDX.w #$0006
-   LDA.l !KEEP,X
    STA.l $001BB1,X
    DEX
    DEX
    BPL -
    LDA.l !KEEP+8
    STA.l $001BBF
    LDA.l !KEEP+10
    STA.l $001BC1
    LDA.l !KEEP+12
    STA.l $001BC5
    SEP #$20
    LDA.l !KEEP+14
    STA.l $001BEF+!CHOICEVAR
    LDA.b #$00
    STA.l !MENU
    REP #$20
    RTS

; The menu's jump back into the script: put the engine state back, and for a chapter
; start a fresh backlog and set the route variable.
LeaveMenu:
    JSR PutBackState
    LDA.l !LEAVETO
    BEQ +
    PHA
    LDA.w #$0000
    STA.l $001BBF
    PLA
    JSR SetChapterVars
+   RTS

; Var 17 decides the route right after some chapter starts; put back the value it had
; when the chapter was entered.
SetChapterVars:
    STA.l !TMP4
    ASL #2
    TAX
    LDA.l !STARTS+3,X
    AND.w #$0001
    BEQ +
    LDA.l !CUR_SLOT
    JSR RecOffset
    BCS +
    LDA.l !SLOTREC+!REC_HAS17,X
    AND.w #$00FF
    BEQ +
    SEP #$20
    LDA.l !SLOTREC+!REC_V17,X
    STA.l !VAR17
    REP #$20
+   RTS

; ---- page writer: DB = $7F, Y = write position
PutW:                       ; A = symbol
    XBA
    STA.w $0000,Y
    XBA
    INY
    INY
    RTS

PutRef:                     ; A = address in bank $7F
    STA.w $0000,Y
    INY
    INY
    SEP #$20
    LDA.b #$7F
    STA.w $0000,Y
    REP #$20
    INY
    RTS

PutStr:                     ; A = string id
    ASL
    TAX
    LDA.l !STRPTR,X
    TAX
-   LDA.l $1B0000,X
    CMP.w #$FFFF
    BEQ +
    STA.w $0000,Y
    INX
    INX
    INY
    INY
    BRA -
+   RTS

; Page start: {25}, header string A, {00}, then {1A} with !TMP3 options whose refs are
; patched by PutOption. Leaves !TMP2 = position of the first ref.
PageStart:
    PHA
    LDA.l !BUF
    TAY
    JSR PutClear
    PLA
    JSR PutStr
    LDA.w #$1000
    JSR PutW
    LDA.w #$101A
    JSR PutW
    LDA.l !TMP3
    INC
    JSR PutW
    LDA.w #$0000
    JSR PutW
    LDA.w #!CHOICEVAR
    JSR PutW
    TYA
    STA.l !TMP2
    LDA.l !TMP3
    STA.l !TMP
-   LDA.w #$0000
    JSR PutRef
    LDA.l !TMP
    DEC
    STA.l !TMP
    BNE -
    RTS

; Option: string A, action X. Writes "{03:@stub} text {1C} stub: {44:action}".
PutOption:
    PHX
    PHA
    PHY                     ; this option's address goes into the next ref slot
    LDA.l !TMP2
    TAX
    PLA
    PHA
    STA.w $0000,X
    INX
    INX
    SEP #$20
    LDA.b #$7F
    STA.w $0000,X
    REP #$20
    INX
    TXA
    STA.l !TMP2
    PLY
    LDA.w #$1003
    JSR PutW
    TYA
    STA.l !TMP              ; where the stub ref goes
    LDA.w #$0000
    JSR PutRef
    PLA
    JSR PutStr
    LDA.w #$101C
    JSR PutW
    LDA.l !TMP
    TAX
    TYA
    STA.w $0000,X         ; stub address (bank byte already $7F)
    LDA.w #$1044
    JSR PutW
    PLA
    PHA
    JSR PutW
    PLA
    CMP.w #$007F
    BEQ .back
    CMP.w #$0040
    BCC +
    RTS
+   DEC                     ; chapter: its scene code, then a jump to its start
    ASL #3
    STA.l !SCENEOF
    LSR
    CLC
    ADC.w #4
    TAX
    LDA.l !STARTS,X
    STA.l !TMP
    LDA.l !STARTS+2,X
    BRA .jump
.back:
    LDA.w #!NOSCENE-!SCENES
    STA.l !SCENEOF
    LDA.l !RESUME
    STA.l !TMP
    LDA.l !RESUME+2
.jump:
    PHA
    LDA.w #$1025
    JSR PutW
    LDA.l !SCENEOF          ; the chapter's scene code, if its first page sets none
    TAX
    PHX
    LDA.l !SCENES,X
    STA.w !SCNBUF&$FFFF
    LDA.l !SCENES+2,X
    STA.w (!SCNBUF&$FFFF)+2
    LDA.l !SCENES+4,X
    STA.w (!SCNBUF&$FFFF)+4
    LDA.l !SCENES+6,X
    STA.w (!SCNBUF&$FFFF)+6
    JSR PutScene
    PLX
    CPX.w #!NOSCENE-!SCENES
    BEQ +                   ; "back" keeps the music as it is
    LDA.l !MUSIC,X
    STA.w !MUSBUF&$FFFF
    LDA.l !MUSIC+2,X
    STA.w (!MUSBUF&$FFFF)+2
    LDA.l !MUSIC+4,X
    STA.w (!MUSBUF&$FFFF)+4
    LDA.l !MUSIC+6,X
    STA.w (!MUSBUF&$FFFF)+6
    JSR PutMusic
+   LDA.w #$1003
    JSR PutW
    LDA.l !TMP
    STA.w $0000,Y
    PLA
    SEP #$20
    STA.w $0002,Y
    REP #$20
    INY
    INY
    INY
.done:
    RTS

; The scene code in !SCNBUF, at Y (DB = $7F).
PutScene:
    LDX.w #0
-   LDA.l !SCNBUF,X
    CMP.w #$FFFF
    BEQ +
    STA.w $0000,Y
    INY
    INY
    INX
    INX
    CPX.w #8
    BCC -
+   RTS

; Sound codes that turn the loops playing now into the ones listed in !MUSBUF:
; {3B:n} for each loop that should stop, {3A:20,n} (fade in) for each that should start.
PutMusic:
    LDA.w #0
    STA.l !SNDNUM
-   LDA.l !SNDNUM
    JSR SoundBit
    BEQ .next
    AND.l !SOUNDS,X
    AND.w #$00FF
    BEQ .next
    LDA.l !SNDNUM
    JSR InTarget
    BCS .next
    LDA.w #$103B
    JSR PutW
    LDA.l !SNDNUM
    JSR PutW
.next:
    LDA.l !SNDNUM
    INC
    STA.l !SNDNUM
    CMP.w #256
    BCC -
    LDX.w #0
-   LDA.l !MUSBUF,X
    AND.w #$00FF
    CMP.w #$00FF
    BEQ .done
    PHX
    PHA
    JSR SoundBit
    AND.l !SOUNDS,X
    AND.w #$00FF
    BNE +
    LDA.w #$103A
    JSR PutW
    LDA.w #20
    JSR PutW
    LDA $01,S
    JSR PutW
+   PLA
    PLX
    INX
    CPX.w #8
    BCC -
.done:
    RTS

; Carry set if sound A is in !MUSBUF
InTarget:
    STA.l !TMP4
    LDX.w #0
-   LDA.l !MUSBUF,X
    AND.w #$00FF
    CMP.w #$00FF
    BEQ +
    CMP.l !TMP4
    BEQ ++
    INX
    CPX.w #8
    BCC -
+   CLC
    RTS
++  SEC
    RTS

; {17:5}{25}: the pause lets the choice code finish taking its options off the screen
; before the page is cleared; clearing at once can stop the next page from printing.
PutClear:
    LDA.w #$1017
    JSR PutW
    LDA.w #$0005
    JSR PutW
    LDA.w #$1025
    JMP PutW

; Point the script at the page just written and flip buffers. The engine keeps four
; copies of the script position (print, layout and two more) and reloads $52 from them,
; so all four are set, as loading a save does.
PageEnd:
    LDA.l !BUF
    STA.l $000052
    STA.l $00195B
    STA.l $001972
    STA.l $001989
    STA.l $0019A0
    LDA.w #$007F
    STA.l $000054
    STA.l $00195D
    STA.l $001974
    STA.l $00198B
    STA.l $0019A2
    LDA.w #$0000
    STA.l $000055
    STA.l $00195E
    STA.l $001975
    STA.l $00198C
    STA.l $0019A3
    STA.l $00005D
    STA.l $001960
    STA.l $001977
    STA.l $00198E
    STA.l $0019A5
    LDA.l !BUF
    EOR.w #!BUFA^!BUFB
    STA.l !BUF
    RTS

; Bit A of the chapter mask at offset !MASKOFF in slot record X: carry set if read
TestChap:
    PHX
    PHA
    LSR #3
    STA.l !TMP4
    TXA
    CLC
    ADC.l !TMP4
    CLC
    ADC.w !MASKOFF
    TAX
    PLA
    PHA
    AND.w #$0007
    PHX
    TAX
    LDA.l BitMask,X
    PLX
    AND.l !SLOTREC,X
    AND.w #$00FF
    CLC
    BEQ +
    SEC
+   PLA
    PLX
    RTS

; Chapter page: A = $40 + page (this playthrough) or $50 + page (every playthrough).
; The choice code shows at most five options. A page that is not the last holds three
; chapters, "next" and "back"; the last page of this playthrough's list holds up to two
; chapters, "all chapters", "endings" and "back", the last page of the other list up to
; four chapters and "back".
BuildChapters:
    PHB
    PEA.w $7F7F
    PLB
    PLB
    JSR .page
    PLB
    RTS
.page:
    STA.w !MODE
    AND.w #$000F
    STA.w !PAGESKIP         ; page * 3
    ASL
    CLC
    ADC.w !PAGESKIP
    STA.w !PAGESKIP
    LDX.w #2                ; chapters that fit on the last page
    LDA.w #!REC_LAP
    STA.w !MASKOFF
    LDA.w !MODE
    AND.w #$0010
    BEQ +
    LDX.w #4
    LDA.w #!REC_ALL
    STA.w !MASKOFF
+   STX.w !CAP
    LDA.l !CUR_SLOT
    JSR RecOffset
    STX.w !CHAPREC
    LDY.w #$0000
    LDA.w #$0000
-   JSR TestChap
    BCC +
    PHA
    INC
    STA.w !CHAPLIST,Y
    PLA
    INY
+   INC
    CMP.w #32
    BCC -
    STY.w !CHAPCOUNT
    LDA.w #0
    STA.w !NEXT
    LDA.w !CHAPCOUNT
    SEC
    SBC.w !PAGESKIP
    BPL +
    LDA.w #$0000
+   CMP.w !CAP
    BEQ .last
    BCC .last
    LDA.w #1
    STA.w !NEXT
    LDA.w #3
    STA.w !PAGEN2
    LDA.w #5                ; three chapters, "next", "back"
    BRA .count
.last:
    STA.w !PAGEN2
    INC                     ; "back"
    LDX.w !CAP
    CPX.w #4
    BEQ .count
    INC                     ; "all chapters", "endings"
    INC
.count:
    STA.l !TMP3
    LDA.w #!S_MENU
    JSR PageStart
    LDX.w !PAGESKIP
-   LDA.w !PAGEN2
    BEQ +
    DEC
    STA.w !PAGEN2
    LDA.w !CHAPLIST,X
    AND.w #$00FF
    PHX
    PHA
    TAX
    PLA
    CLC
    ADC.w #!S_CH
    JSR PutOption
    PLX
    INX
    BRA -
+   LDA.w !NEXT
    BEQ +
    LDA.w !MODE
    INC
    TAX
    LDA.w #!S_NEXT
    JSR PutOption
    BRA .back
+   LDA.w !CAP
    CMP.w #4
    BEQ .back
    LDX.w #$0050
    LDA.w #!S_ALL
    JSR PutOption
    LDX.w #$0060
    LDA.w #!S_ENDLIST
    JSR PutOption
.back:
    LDX.w #$007F
    LDA.w #!S_BACK
    JSR PutOption
    JMP PageEnd

; Ending page A: header, !ENDPERPAGE endings, then "next" or "chapters", and "back".
BuildEndings:
    PHB
    PEA.w $7F7F
    PLB
    PLB
    JSR .page
    PLB
    RTS
.page:
    STA !PAGEN
    LDA.l !CUR_SLOT
    JSR RecOffset
    STX.w !CHAPREC
    ; count seen endings
    LDA.w #$0000
    STA !CHAPCOUNT
    LDX.w #$0000
-   TXA
    JSR TestEnd
    BCC +
    INC !CHAPCOUNT
+   INX
    CPX.w #!NENDINGS
    BCC -
    LDA.w #2
    STA.l !TMP3
    LDA !CHAPCOUNT
    CLC
    ADC.w #!S_ENDHDR
    JSR PageStart0
    ; the ending lines go before the choice code, so the choice is written afterwards
    LDA !PAGEN
    ASL
    CLC
    ADC !PAGEN
    ASL                     ; * !ENDPERPAGE
    STA !PAGESKIP
    LDA.w #!ENDPERPAGE
    STA !CHAPCOUNT
-   LDA !PAGESKIP
    CMP.w #!NENDINGS
    BCS +
    JSR TestEnd
    LDA !PAGESKIP
    BCC .unseen
    ADC.w #!S_SEEN-1        ; carry set
    BRA .put
.unseen:
    ADC.w #!S_UNSEEN
.put:
    JSR PutStr
    LDA.w #$1000
    JSR PutW
    INC !PAGESKIP
    DEC !CHAPCOUNT
    BNE -
+   JSR ChoiceHead
    LDA !PAGESKIP
    CMP.w #!NENDINGS
    BCS .tochap
    LDA !PAGEN
    INC
    ORA.w #$0060
    TAX
    LDA.w #!S_NEXT
    BRA .opt
.tochap:
    LDX.w #$0040
    LDA.w #!S_CHLIST
.opt:
    JSR PutOption
    LDX.w #$007F
    LDA.w #!S_BACK
    JSR PutOption
    JMP PageEnd

; Like PageStart without the choice: {25}, header A, {00}.
PageStart0:
    PHA
    LDA.l !BUF
    TAY
    JSR PutClear
    PLA
    JSR PutStr
    LDA.w #$1000
    JSR PutW
    RTS

; The choice code with !TMP3 option refs at Y (see PageStart).
ChoiceHead:
    LDA.w #$101A
    JSR PutW
    LDA.l !TMP3
    INC
    JSR PutW
    LDA.w #$0000
    JSR PutW
    LDA.w #!CHOICEVAR
    JSR PutW
    TYA
    STA.l !TMP2
    LDA.l !TMP3
    STA.l !TMP
-   LDA.w #$0000
    JSR PutRef
    LDA.l !TMP
    DEC
    STA.l !TMP
    BNE -
    RTS

; Ending A seen in slot record !CHAPREC: carry set if so
TestEnd:
    PHX
    PHA
    LDX.w !CHAPREC
    LSR #3
    STA.l !TMP4
    TXA
    CLC
    ADC.l !TMP4
    TAX
    PLA
    PHA
    AND.w #$0007
    PHX
    TAX
    LDA.l BitMask,X
    PLX
    AND.l !SLOTREC+!REC_END,X
    AND.w #$00FF
    CLC
    BEQ +
    SEC
+   PLA
    PLX
    RTS

incsrc "flow.asm"
