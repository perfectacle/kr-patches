; Flowchart (Kamaitachi no Yoru Advance style), included by asm/qol.asm.
; One chapter at a time: the choices and endings seen so far, row by row as tools/flow.py
; laid the chapter out with the unseen ones closed up, branches into other chapters as
; arrow boxes, and the chapter's rows in a minimap on the right. It is drawn straight into
; the text layer's bitmap with the scene layers switched off. Text layer colors: 1 white,
; 2 gray, 3 yellow.
; Routines here run with DB = $7F and 16 bit registers unless noted.

!FNODES = $1C8010           ; 16 bytes per node (tools/flow.py)
!FSCENE = $1CC000           ; 8 bytes per node
!FMUSIC = $1CD000           ; 8 bytes per node
!FCHAP = $1CE000            ; row list address by chapter id - 1

!BITMAP = $0010             ; text layer bitmap: 32 x 32 tiles of 16 bytes
!ITEMS = $D000              ; 8 bytes per shown item: kind, row, column, exit chapter, node
!MAXITEMS = 160
!NODEMAP = $D600            ; item number + 1 by node (bytes), 0 when not shown
!F_CH = $D800
!F_COUNT = $D802
!F_CUR = $D804
!F_TOP = $D806              ; first row on screen
!F_LEFT = $D808             ; first column on screen
!F_ROWS = $D80A
!F_PREV = $D80C             ; pad bits last frame
!F_HOLD = $D80E
!F_ACT = $D810              ; what closed the flowchart: 1 jump, 2 back, 3 chapters, 4 endings
!F_SAVE = $D812             ; $0A0E, $0A13 while the flowchart is up
!F_ROWPTR = $D814
!F_N = $D816
!F_COL = $D818
!F_PENDN = $D81A            ; exits waiting for the next row (bytes used)
!F_PEND = $D81C             ; (parent item, chapter) words, 16 pairs
!F_X = $D860
!F_Y = $D862
!F_C = $D864
!F_T = $D866
!F_T2 = $D868
!F_T3 = $D86A
!F_BIT = $D86C
!F_I = $D86E
!F_K = $D870
!F_PX = $D872
!F_PY = $D874
!F_NODE = $D876
!F_TRY = $D878
!F_STEP = $D87A
!F_END = $D87C              ; line ends
!F_CLIP = $D87E             ; nonzero: plots stay out of the title and minimap
!F_G = $D880                ; SmallChar
!F_GROW = $D882
!F_GN = $D884
!F_NV = $D886               ; SmallNum
!F_NC = $D888
!F_ND = $D88A
!F_NS = $D88C               ; NodeSeen
!F_LP = $D88E               ; line ends: parent and child item
!F_LC = $D890
!F_CX = $D892
!F_CY = $D894
!F_MID = $D896
!F_OPT = $D898
!F_OPTN = $D89A
!F_KIDS = $D89C
!F_KIDP = $D89E
!F_PENDI = $D8A0
!F_OPTB = $D8A2
!F_DIR = $D8A4
!F_CX0 = $D8A6
!F_M = $D8A8
!ROWN = $D900              ; items in each row (bytes)

!COLS = 6                   ; boxes on screen across
!SROWS = 6                  ; and down
!BOXW = 32
!BOXH = 20
!PITCHX = 37
!PITCHY = 32
!GRIDX = 6
!GRIDY = 24
!MAPX = 236

; ------------------------------------------------ entry
; From the key wait (SelCheck) after KeepState, with !BUF set. Ends with a script page
; written and the script pointed at it, as the chapter menu pages do.
FlowOpen:
    PHB
    PEA.w $7F7F
    PLB
    PLB
    REP #$30
    LDA.l !CUR_SLOT
    JSR RecOffset
    STX.w !CHAPREC
    STZ.w !F_HOLD
    STZ.w !F_ACT
    STZ.w !F_CLIP
    LDA.l !SLOTREC+!REC_LAST,X
    AND.w #$00FF
    BNE +
    LDA.w #1
+   STA.w !F_CH
    LDA.w #1
    JSR FindChapter         ; this one or the next with something seen
    BCS +
    LDA.w #3                ; nothing seen yet: the chapter list
    STA.w !F_ACT
    BRA .act
+   SEP #$20
    LDA.l $000A0E
    STA.w !F_SAVE
    LDA.l $000A13
    STA.w !F_SAVE+1
    LDA.b #$04              ; text layer only
    STA.l $000A0E
    LDA.b #$00
    STA.l $000A13
    LDA.l $0000B6
    ORA.b #$40
    STA.l $0000B6
    REP #$20
    LDA.l $000A25
    STA.w !F_PREV
    JSR Redraw
.loop:
    JSR Frame
    JSR FlowInput
    LDA.w !F_ACT
    BEQ .loop
    JSR ClearBitmap
-   JSR Frame               ; let go of the keys, or the next key wait takes them
    LDA.l $000A25
    AND.w #$FFF0
    BNE -
    SEP #$20
    LDA.w !F_SAVE
    STA.l $000A0E
    LDA.w !F_SAVE+1
    STA.l $000A13
    LDA.l $0000B6
    ORA.b #$40
    STA.l $0000B6
    REP #$20
.act:
    LDA.w !F_ACT
    CMP.w #1
    BEQ .jump
    CMP.w #2
    BEQ .back
    CMP.w #3
    BEQ .chapters
    LDA.w #0
    JSR BuildEndings
    BRA .done
.chapters:
    LDA.w #$0040
    JSR BuildChapters
    BRA .done
.back:
    LDA.w #0
    STA.l !LEAVETO
    LDA.l !BUF
    TAY
    JSR PutClear
    LDA.w #$1003
    JSR PutW
    LDA.l !RESUME
    STA.w $0000,Y
    LDA.l !RESUME+2
    SEP #$20
    STA.w $0002,Y
    REP #$20
    INY #3
    JSR PageEnd
    BRA .resync
.jump:
    JSR JumpPage
.resync:
    PHB
    PEA.w $0000
    PLB
    PLB
    JSL Resync
    PLB
.done:
    PLB
    RTS

; One frame: upload the text layer if asked, wait for the NMI.
Frame:
    PHB
    PEA.w $0000
    PLB
    PLB
    JSL TextUpload
    JSL $0092DF
    REP #$30
    PLB
    RTS

; The page that leaves for node !F_NODE: page clear, its scene and music, then a jump to
; the start of the page its choice is on.
JumpPage:
    LDA.w !F_NODE
    ASL #4
    TAX
    LDA.l !FNODES+1,X
    AND.w #$00FF
    STA.l !LEAVETO
    LDA.l !FNODES+10,X
    STA.w !F_T
    LDA.l !FNODES+12,X
    STA.w !F_T2
    LDA.w !F_NODE
    ASL #3
    TAX
    LDA.l !FSCENE,X
    STA.w !SCNBUF&$FFFF
    LDA.l !FSCENE+2,X
    STA.w (!SCNBUF&$FFFF)+2
    LDA.l !FSCENE+4,X
    STA.w (!SCNBUF&$FFFF)+4
    LDA.l !FSCENE+6,X
    STA.w (!SCNBUF&$FFFF)+6
    LDA.l !FMUSIC,X
    STA.w !MUSBUF&$FFFF
    LDA.l !FMUSIC+2,X
    STA.w (!MUSBUF&$FFFF)+2
    LDA.l !FMUSIC+4,X
    STA.w (!MUSBUF&$FFFF)+4
    LDA.l !FMUSIC+6,X
    STA.w (!MUSBUF&$FFFF)+6
    LDA.l !BUF
    TAY
    JSR PutClear
    JSR PutScene
    JSR PutMusic
    LDA.w #$1003
    JSR PutW
    LDA.w !F_T
    STA.w $0000,Y
    SEP #$20
    LDA.w !F_T2
    STA.w $0002,Y
    REP #$20
    INY #3
    JMP PageEnd

; ------------------------------------------------ input
; Pad word ($0A25): B Y Sel St Up Down Left Right, A X L R
FlowInput:
    LDA.l $000A25
    STA.w !F_T
    LDA.w !F_PREV
    EOR.w #$FFFF
    AND.w !F_T
    STA.w !F_T3             ; newly pressed
    LDA.w !F_T              ; holding the same direction repeats it
    AND.w #$0F00
    BEQ .nohold
    STA.w !F_T2
    LDA.w !F_PREV
    AND.w #$0F00
    CMP.w !F_T2
    BNE .nohold
    INC.w !F_HOLD
    LDA.w !F_HOLD
    CMP.w #16
    BCC .held
    AND.w #$0003
    BNE .held
    LDA.w !F_T2
    TSB.w !F_T3
    BRA .held
.nohold:
    STZ.w !F_HOLD
.held:
    LDA.w !F_T
    STA.w !F_PREV
    LDA.w !F_T3
    BNE +
    RTS
+   BIT.w #$0800
    BEQ +
    LDA.w #-1
    JMP MoveV
+   BIT.w #$0400
    BEQ +
    LDA.w #1
    JMP MoveV
+   BIT.w #$0200
    BEQ +
    LDA.w #-1
    JMP MoveH
+   BIT.w #$0100
    BEQ +
    LDA.w #1
    JMP MoveH
+   BIT.w #$0020            ; L
    BEQ +
    LDA.w !F_CH
    DEC
    BNE ++
    LDA.w #30
++  STA.w !F_CH
    LDA.w #-1
    JSR FindChapter
    JMP Redraw
+   BIT.w #$0010            ; R
    BEQ +
    LDA.w !F_CH
    INC
    CMP.w #31
    BCC ++
    LDA.w #1
++  STA.w !F_CH
    LDA.w #1
    JSR FindChapter
    JMP Redraw
+   BIT.w #$0080            ; A
    BEQ +
    JMP Choose
+   BIT.w #$A000            ; B, Select
    BEQ +
    LDA.w #2
    STA.w !F_ACT
    RTS
+   BIT.w #$4000            ; Y
    BEQ +
    LDA.w #3
    STA.w !F_ACT
    RTS
+   BIT.w #$0040            ; X
    BEQ +
    LDA.w #4
    STA.w !F_ACT
+   RTS

Choose:
    JSR CurItem
    LDA.w !ITEMS+0,X
    AND.w #$00FF
    BEQ .node
    LDA.w !ITEMS+3,X        ; an exit: open that chapter
    AND.w #$00FF
    STA.w !F_CH
    LDA.w #1
    JSR FindChapter
    JMP Redraw
.node:
    LDA.w !ITEMS+4,X
    STA.w !F_NODE
    ASL #4
    TAX
    LDA.l !FNODES,X         ; an ending is not a place to go back to
    AND.w #$00FF
    BNE +
    LDA.w #1
    STA.w !F_ACT
+   RTS

; X = offset of the cursor item
CurItem:
    LDA.w !F_CUR
    ASL #3
    TAX
    RTS

; A = -1 / 1: the item in the row above / below nearest to the cursor on screen
MoveV:
    STA.w !F_DIR
    JSR CurItem
    LDA.w !ITEMS+1,X
    AND.w #$00FF
    CLC
    ADC.w !F_DIR
    BMI .none
    CMP.w !F_ROWS
    BCS .none
    STA.w !F_DIR            ; target row
    LDA.w !F_CUR
    JSR ItemPos
    LDA.w !F_PX
    STA.w !F_CX0
    LDA.w #$7FFF
    STA.w !F_T3             ; best distance
    STZ.w !F_I
.item:
    LDA.w !F_I
    CMP.w !F_COUNT
    BCS .pick
    ASL #3
    TAX
    LDA.w !ITEMS+1,X
    AND.w #$00FF
    CMP.w !F_DIR
    BNE .next
    LDA.w !F_I
    JSR ItemPos
    LDA.w !F_PX
    SEC
    SBC.w !F_CX0
    BPL +
    EOR.w #$FFFF
    INC
+   CMP.w !F_T3
    BCS .next
    STA.w !F_T3
    LDA.w !F_I
    STA.w !F_K
.next:
    INC.w !F_I
    BRA .item
.pick:
    LDA.w !F_T3
    CMP.w #$7FFF
    BEQ .none
    LDA.w !F_K
    STA.w !F_CUR
    JSR FixScroll
    JMP Redraw
.none:
    RTS

; A = -1 / 1: the next item left / right in the same row
MoveH:
    CLC
    ADC.w !F_CUR
    BMI .none
    CMP.w !F_COUNT
    BCS .none
    STA.w !F_T
    ASL #3
    TAX
    LDA.w !ITEMS+1,X
    STA.w !F_T2
    JSR CurItem
    LDA.w !ITEMS+1,X
    EOR.w !F_T2
    AND.w #$00FF
    BNE .none
    LDA.w !F_T
    STA.w !F_CUR
    JSR FixScroll
    JMP Redraw
.none:
    RTS

; Keep the cursor item on screen.
FixScroll:
    JSR CurItem
    LDA.w !ITEMS+1,X
    AND.w #$00FF
    CMP.w !F_TOP
    BCS +
    STA.w !F_TOP
+   SEC
    SBC.w #!SROWS-1
    BMI +
    CMP.w !F_TOP
    BCC +
    STA.w !F_TOP
+   LDA.w !ITEMS+2,X
    AND.w #$00FF
    CMP.w !F_LEFT
    BCS +
    STA.w !F_LEFT
+   SEC
    SBC.w #!COLS-1
    BMI +
    CMP.w !F_LEFT
    BCC +
    STA.w !F_LEFT
+   RTS

; ------------------------------------------------ layout
; Lay out !F_CH; when nothing in it was seen, try the chapters after it in direction A
; (1 or -1). Carry set when a chapter with something to show was found.
FindChapter:
    STA.w !F_STEP
    LDA.w #30
    STA.w !F_TRY
.try:
    JSR Layout
    LDA.w !F_COUNT
    BNE .found
    LDA.w !F_CH
    CLC
    ADC.w !F_STEP
    BNE +
    LDA.w #30
+   CMP.w #31
    BCC +
    LDA.w #1
+   STA.w !F_CH
    DEC.w !F_TRY
    BNE .try
    CLC
    RTS
.found:
    STZ.w !F_CUR
    STZ.w !F_TOP
    STZ.w !F_LEFT
    SEC
    RTS

Layout:
    STZ.w !F_COUNT
    STZ.w !F_ROWS
    STZ.w !F_PENDN
    STZ.w !F_COL
    LDX.w #398
-   STZ.w !NODEMAP,X
    DEX
    DEX
    BPL -
    LDA.w !F_CH
    DEC
    ASL
    TAX
    LDA.l !FCHAP,X
    STA.w !F_ROWPTR
.row:
    LDA.w !F_COUNT
    STA.w !F_K              ; first item of this row
    JSR PlaceExits          ; those waiting from the row before go first
    LDX.w !F_ROWPTR
    LDA.l $1C0000,X
    STA.w !F_N
    INX
    INX
    STX.w !F_ROWPTR
    LDA.w !F_N
    BEQ .last
.node:
    LDX.w !F_ROWPTR
    LDA.l $1C0000,X
    INX
    INX
    STX.w !F_ROWPTR
    STA.w !F_NODE
    JSR NodeSeen
    BCC +
    LDX.w !F_NODE
    LDA.w #0
    JSR AddItem
+   DEC.w !F_N
    BNE .node
    JSR RowDone
    BRA .row
.last:
    JMP RowDone             ; exits from the last row of nodes

; A row is closed: if it got items it takes a row number, and the cross-chapter children
; of its nodes wait for the next row.
RowDone:
    LDA.w !F_COL
    BNE +
    RTS
+   LDX.w !F_ROWS
    SEP #$20
    LDA.w !F_COL
    STA.w !ROWN,X
    REP #$20
    INC.w !F_ROWS
    STZ.w !F_COL
    LDA.w !F_K
    STA.w !F_I
.item:
    LDA.w !F_I
    CMP.w !F_COUNT
    BCS .done
    ASL #3
    TAX
    LDA.w !ITEMS+0,X
    AND.w #$00FF
    BNE .next
    LDA.w !ITEMS+4,X
    JSR QueueExits
.next:
    INC.w !F_I
    BRA .item
.done:
    RTS

; Queue the chapters node A branches into (children seen, in another chapter), once each
; per parent item !F_I.
QueueExits:
    ASL #4
    TAX
    LDA.l !FNODES+8,X
    AND.w #$00FF
    STA.w !F_KIDS
    LDA.l !FNODES+6,X
    STA.w !F_KIDP
.kid:
    LDA.w !F_KIDS
    BNE +
    RTS
+   LDX.w !F_KIDP
    LDA.l $1C0000,X
    STA.w !F_T
    JSR NodeSeen
    BCC .next
    LDA.w !F_T
    ASL #4
    TAX
    LDA.l !FNODES+1,X
    AND.w #$00FF
    CMP.w !F_CH
    BEQ .next
    STA.w !F_C              ; chapter
    LDX.w #0
.dup:
    CPX.w !F_PENDN
    BCS .add
    LDA.w !F_PEND,X
    CMP.w !F_I
    BNE +
    LDA.w !F_PEND+2,X
    CMP.w !F_C
    BEQ .next
+   INX #4
    BRA .dup
.add:
    CPX.w #16*4
    BCS .next
    LDA.w !F_I
    STA.w !F_PEND,X
    LDA.w !F_C
    STA.w !F_PEND+2,X
    TXA
    CLC
    ADC.w #4
    STA.w !F_PENDN
.next:
    INC.w !F_KIDP
    INC.w !F_KIDP
    DEC.w !F_KIDS
    BRA .kid

PlaceExits:
    STZ.w !F_PENDI
.item:
    LDX.w !F_PENDI
    CPX.w !F_PENDN
    BCS .done
    LDA.w !F_PEND+2,X
    XBA                     ; chapter in the high byte
    ORA.w #1
    PHA
    LDA.w !F_PEND,X         ; parent item
    TAX
    PLA
    JSR AddItem
    LDA.w !F_PENDI
    CLC
    ADC.w #4
    STA.w !F_PENDI
    BRA .item
.done:
    STZ.w !F_PENDN
    RTS

; Add an item to the current row: A low byte = kind (0 node, 1 exit), high byte = exit
; chapter; X = node (kind 0) or parent item (kind 1).
AddItem:
    PHA
    LDA.w !F_COUNT
    CMP.w #!MAXITEMS
    BCC +
    PLA
    RTS
+   ASL #3
    TAY
    PLA
    STA.w !ITEMS+0,Y        ; kind; the high byte lands on the row, set next
    XBA
    SEP #$20
    STA.w !ITEMS+3,Y
    LDA.w !F_ROWS
    STA.w !ITEMS+1,Y
    LDA.w !F_COL
    STA.w !ITEMS+2,Y
    REP #$20
    TXA
    STA.w !ITEMS+4,Y
    LDA.w !ITEMS+0,Y
    AND.w #$00FF
    BNE +
    SEP #$20                ; a node: remember its item for the lines
    LDA.w !F_COUNT
    INC
    STA.w !NODEMAP,X
    REP #$20
+   INC.w !F_COUNT
    INC.w !F_COL
    RTS

; Carry set if node A was seen: a choice with an option taken, an ending recorded.
NodeSeen:
    PHX
    ASL #4
    TAX
    LDA.l !FNODES+2,X
    STA.w !F_NS
    LDA.l !FNODES,X
    AND.w #$00FF
    BNE .ending
    LDX.w !F_NS
    LDA.l $001BEF,X
    AND.w #$00F8
    CLC
    BEQ +
    SEC
+   PLX
    RTS
.ending:
    LDA.w !F_NS
    JSR TestEnd
    PLX
    RTS

; ------------------------------------------------ drawing
Redraw:
    JSR ClearBitmap
    LDA.w #1
    STA.w !F_CLIP
    JSR DrawLines
    STZ.w !F_I
-   LDA.w !F_I
    CMP.w !F_COUNT
    BCS +
    JSR DrawItem
    INC.w !F_I
    BRA -
+   STZ.w !F_CLIP
    JSR DrawMap
    JSR DrawTitle
    ; fall through

UploadAll:
    LDA.w #1
    STA.l $0019CE
    LDA.w #0
    STA.l $0019C4
    STA.l $0019C8
    LDA.w #27
    STA.l $0019C6
    LDA.w #31
    STA.l $0019CA
    RTS

ClearBitmap:
    LDA.w #0
    LDX.w #$3FFE
-   STA.w !BITMAP,X
    DEX
    DEX
    BPL -
    JMP UploadAll

; !F_PX, !F_PY = top left of item A on screen (signed, may be off screen); X = its offset.
; A row that fits on the screen is centered in the grid area; a wider one starts at the
; left and scrolls with !F_LEFT.
ItemPos:
    ASL #3
    TAX
    LDA.w !ITEMS+1,X
    AND.w #$00FF
    PHX
    TAX
    LDA.w !ROWN,X
    AND.w #$00FF
    PLX
    CMP.w #!COLS+1
    BCS .wide
    JSR Times37             ; row width n * 37 - 5, centered in 234 pixels
    EOR.w #$FFFF
    SEC
    ADC.w #!MAPX-2+5
    LSR
    STA.w !F_PX
    LDA.w !ITEMS+2,X
    AND.w #$00FF
    BRA .x
.wide:
    LDA.w #!GRIDX
    STA.w !F_PX
    LDA.w !ITEMS+2,X
    AND.w #$00FF
    SEC
    SBC.w !F_LEFT
.x:
    JSR Times37
    CLC
    ADC.w !F_PX
    STA.w !F_PX
    LDA.w !ITEMS+1,X
    AND.w #$00FF
    SEC
    SBC.w !F_TOP
    ASL #5                  ; * !PITCHY
    CLC
    ADC.w #!GRIDY
    STA.w !F_PY
    RTS

; A * !PITCHX (37), signed
Times37:
    STA.w !F_M
    ASL #5
    CLC
    ADC.w !F_M
    ADC.w !F_M
    ADC.w !F_M
    ADC.w !F_M
    ADC.w !F_M
    RTS

DrawItem:
    LDA.w !F_I
    JSR ItemPos
    LDA.w !F_PX             ; whole boxes only
    CMP.w #!MAPX-!BOXW+1
    BCC +
    RTS
+   LDA.w !F_PY
    CMP.w #!GRIDY
    BCS +
    RTS
+   CMP.w #224-!BOXH+1
    BCC +
    RTS
+   LDA.w #1
    LDY.w !F_I
    CPY.w !F_CUR
    BNE +
    LDA.w #3
+   JSR Box
    LDA.w !F_I
    ASL #3
    TAX
    LDA.w !ITEMS+0,X
    AND.w #$00FF
    BEQ .node
    LDA.w !ITEMS+3,X        ; exit: arrow and the chapter's number
    AND.w #$00FF
    TAX
    LDA.l ChapterNums-1,X
    AND.w #$00FF
    STA.w !F_NV
    LDA.w #4
    LDY.w #7
    JSR TextAt
    LDA.w #16
    LDY.w #1
    JSR SmallChar
    LDA.w !F_NV
    LDY.w #1
    JMP SmallNum
.node:
    LDA.w !ITEMS+4,X
    STA.w !F_NODE
    ASL #4
    TAX
    LDA.l !FNODES,X
    AND.w #$00FF
    BEQ .choice
    LDA.l !FNODES+2,X       ; ending: END and its number
    INC
    STA.w !F_NV
    LDA.w #3
    LDY.w #7
    JSR TextAt
    LDY.w #3
    LDA.w #14
    JSR SmallChar
    LDA.w #15
    JSR SmallChar
    LDA.w #13
    JSR SmallChar
    LDA.w !F_NV
    JMP SmallNum
.choice:
    LDA.w #3                ; number, then the options: taken ones bright
    LDY.w #3
    JSR TextAt
    LDA.w !F_NODE
    INC
    LDY.w #1
    JSR SmallNum
    LDA.w #3
    LDY.w #12
    JSR TextAt
    LDA.w !F_NODE
    ASL #4
    TAX
    LDA.l !FNODES+4,X
    AND.w #$00FF
    STA.w !F_OPTN
    LDA.l !FNODES+2,X
    TAX
    LDA.l $001BEF,X
    AND.w #$00FF
    LSR #3
    STA.w !F_OPTB
    STZ.w !F_OPT
.opt:
    LDA.w !F_OPT
    CMP.w !F_OPTN
    BCS .done
    LDY.w #2
    LSR.w !F_OPTB
    BCC +
    LDY.w #3
+   CLC
    ADC.w #10               ; A-E
    JSR SmallChar
    INC.w !F_OPT
    BRA .opt
.done:
    RTS

; !F_X, !F_Y = item corner + (A, Y)
TextAt:
    CLC
    ADC.w !F_PX
    STA.w !F_X
    TYA
    CLC
    ADC.w !F_PY
    STA.w !F_Y
    RTS

; A = color: outline of the item box at !F_PX/!F_PY
Box:
    STA.w !F_C
    LDA.w !F_PX
    STA.w !F_X
    LDA.w !F_PY
    STA.w !F_Y
    LDA.w !F_PX
    CLC
    ADC.w #!BOXW-1
    STA.w !F_END
    JSR HLine
    LDA.w !F_PX
    STA.w !F_X
    LDA.w !F_PY
    CLC
    ADC.w #!BOXH-1
    STA.w !F_Y
    JSR HLine
    LDA.w !F_PX
    STA.w !F_X
    LDA.w !F_PY
    STA.w !F_Y
    CLC
    ADC.w #!BOXH-1
    STA.w !F_END
    JSR VLine
    LDA.w !F_PX
    CLC
    ADC.w #!BOXW-1
    STA.w !F_X
    LDA.w !F_PY
    STA.w !F_Y
    JMP VLine

; Lines from each shown node to its shown children in this chapter, and to its exits.
DrawLines:
    STZ.w !F_I
.item:
    LDA.w !F_I
    CMP.w !F_COUNT
    BCC +
    RTS
+   ASL #3
    TAX
    LDA.w !ITEMS+0,X
    AND.w #$00FF
    BEQ .node
    LDA.w !ITEMS+4,X        ; exit: from its parent
    STA.w !F_LP
    LDA.w !F_I
    STA.w !F_LC
    JSR Connect
    BRA .next
.node:
    LDA.w !ITEMS+4,X
    ASL #4
    TAX
    LDA.l !FNODES+8,X
    AND.w #$00FF
    STA.w !F_KIDS
    LDA.l !FNODES+6,X
    STA.w !F_KIDP
.kid:
    LDA.w !F_KIDS
    BEQ .next
    LDX.w !F_KIDP
    LDA.l $1C0000,X
    TAX
    LDA.w !NODEMAP,X
    AND.w #$00FF
    BEQ +
    DEC
    STA.w !F_LC
    LDA.w !F_I
    STA.w !F_LP
    JSR Connect
+   INC.w !F_KIDP
    INC.w !F_KIDP
    DEC.w !F_KIDS
    BRA .kid
.next:
    INC.w !F_I
    BRA .item

; Line from the bottom of item !F_LP down to the top of item !F_LC, bending halfway
; through the gap under the parent. Children not below the parent get no line.
Connect:
    LDA.w !F_LC
    JSR ItemPos
    LDA.w !F_PX
    CLC
    ADC.w #!BOXW/2
    STA.w !F_CX
    LDA.w !F_PY
    STA.w !F_CY
    LDA.w !F_LP
    JSR ItemPos
    LDA.w !F_PY
    CMP.w !F_CY
    BMI +
    RTS
+   LDA.w #1
    STA.w !F_C
    LDA.w !F_PY
    CLC
    ADC.w #!BOXH+6           ; half the gap
    STA.w !F_MID
    LDA.w !F_PX             ; down from the parent
    CLC
    ADC.w #!BOXW/2
    STA.w !F_X
    STA.w !F_T
    LDA.w !F_PY
    CLC
    ADC.w #!BOXH
    STA.w !F_Y
    LDA.w !F_MID
    STA.w !F_END
    JSR VLine
    LDA.w !F_MID            ; across
    STA.w !F_Y
    LDA.w !F_T
    CMP.w !F_CX
    BMI +
    LDA.w !F_CX
    STA.w !F_X
    LDA.w !F_T
    STA.w !F_END
    BRA ++
+   STA.w !F_X
    LDA.w !F_CX
    STA.w !F_END
++  JSR HLine
    LDA.w !F_CX             ; down to the child
    STA.w !F_X
    LDA.w !F_MID
    STA.w !F_Y
    LDA.w !F_CY
    DEC
    STA.w !F_END
    JMP VLine

; Lines from (!F_X, !F_Y) to !F_END, color !F_C; signed ends, clipped to the screen
HLine:
    LDA.w !F_END
    BMI .none
    CMP.w #256
    BCC +
    LDA.w #255
    STA.w !F_END
+   LDA.w !F_X
    BPL .go
    STZ.w !F_X
.go:
    LDA.w !F_C
    JSR Plot
    LDA.w !F_X
    CMP.w !F_END
    BCS .none
    INC.w !F_X
    BRA .go
.none:
    RTS

VLine:
    LDA.w !F_END
    BMI .none
    CMP.w #224
    BCC +
    LDA.w #223
    STA.w !F_END
+   LDA.w !F_Y
    BPL .go
    STZ.w !F_Y
.go:
    LDA.w !F_C
    JSR Plot
    LDA.w !F_Y
    CMP.w !F_END
    BCS .none
    INC.w !F_Y
    BRA .go
.none:
    RTS

PlotOut:
    RTS

; A = color, pixel at !F_X/!F_Y; nothing off screen, or outside the grid with !F_CLIP
Plot:
    STA.w !F_T2
    LDA.w !F_X
    CMP.w #256
    BCS PlotOut
    LDA.w !F_Y
    CMP.w #224
    BCS PlotOut
    LDA.w !F_CLIP
    BEQ +
    LDA.w !F_Y
    CMP.w #!GRIDY
    BCC .out
    LDA.w !F_X
    CMP.w #!MAPX-2
    BCS PlotOut
+   LDA.w !F_X
    AND.w #$0007
    TAX
    LDA.l PixBit,X
    AND.w #$00FF
    STA.w !F_BIT
    LDA.w !F_Y
    AND.w #$00F8
    ASL #6
    STA.w !F_T3
    LDA.w !F_X
    AND.w #$00F8
    ASL
    CLC
    ADC.w !F_T3
    STA.w !F_T3
    LDA.w !F_Y
    AND.w #$0007
    ASL
    CLC
    ADC.w !F_T3
    TAX
    SEP #$20
    LDA.w !F_BIT
    EOR.b #$FF
    STA.w !F_BIT+1          ; mask to clear
    LSR.w !F_T2
    LDA.w !BITMAP,X
    BCC +
    ORA.w !F_BIT
    BRA ++
+   AND.w !F_BIT+1
++  STA.w !BITMAP,X
    LSR.w !F_T2
    LDA.w !BITMAP+1,X
    BCC +
    ORA.w !F_BIT
    BRA ++
+   AND.w !F_BIT+1
++  STA.w !BITMAP+1,X
    REP #$20
.out:
    RTS

PixBit:
    db $80,$40,$20,$10,$08,$04,$02,$01

; A = glyph (0-9 digits, 10-14 A-E, 15 N, 16 arrow), Y = color; drawn at !F_X/!F_Y,
; then !F_X moves on by 5. X and Y are kept.
SmallChar:
    PHX
    PHY
    STY.w !F_C
    ASL
    STA.w !F_G
    ASL
    CLC
    ADC.w !F_G              ; * 6
    STA.w !F_GN
    LDA.w !F_Y
    PHA
    LDA.w #6
    STA.w !F_GROW
.row:
    LDX.w !F_GN
    LDA.l SmallFont,X
    AND.w #$00FF
    STA.w !F_G
    LDA.w !F_X
    PHA
    LDY.w #4
.px:
    ASL.w !F_G
    LDA.w !F_G
    BIT.w #$0100
    BEQ +
    LDA.w !F_C
    JSR Plot
+   INC.w !F_X
    DEY
    BNE .px
    PLA
    STA.w !F_X
    INC.w !F_Y
    INC.w !F_GN
    DEC.w !F_GROW
    BNE .row
    PLA
    STA.w !F_Y
    LDA.w !F_X
    CLC
    ADC.w #5
    STA.w !F_X
    PLY
    PLX
    RTS

; A = number (0-999), Y = color, no leading zeros
SmallNum:
    STY.w !F_NC
    STA.w !F_NV
    STZ.w !F_ND             ; a digit was drawn
    LDA.w #100
    JSR .digit
    LDA.w #10
    JSR .digit
    LDA.w #1
.digit:
    STA.w !F_T
    LDX.w #0
    LDA.w !F_NV
-   CMP.w !F_T
    BCC +
    SEC
    SBC.w !F_T
    INX
    BRA -
+   STA.w !F_NV
    TXA
    BNE .draw
    LDY.w !F_ND
    BNE .draw
    LDY.w !F_T
    CPY.w #1
    BEQ .draw
    RTS
.draw:
    LDY.w #1
    STY.w !F_ND
    LDY.w !F_NC
    JMP SmallChar

; The chapter title on top; over an exit, an arrow and the chapter it leads to.
DrawTitle:
    JSR CurItem
    LDA.w !ITEMS+0,X
    AND.w #$00FF
    BEQ .own
    LDA.w #6
    STA.w !F_X
    LDA.w #9
    STA.w !F_Y
    LDA.w #16
    LDY.w #3
    JSR SmallChar
    JSR CurItem
    LDA.w !ITEMS+3,X
    AND.w #$00FF
    BRA .title
.own:
    LDA.w !F_CH
.title:
    CLC
    ADC.w #!S_CH
    PHA
    LDA.w #16
    STA.l $001A7F
    LDA.w #4
    STA.l $001A81
    PLA
    PHB
    PEA.w $0000
    PLB
    PLB
    JSR DrawStr1B
    REP #$30
    PLB
    RTS

; The chapter's rows as dots, the cursor yellow, the rows on screen marked by a gray bar.
DrawMap:
    LDA.w !F_ROWS
    BNE +
    RTS
+   LDA.w #192              ; pixels per row, 1 to 8
    LDX.w #0
-   CMP.w !F_ROWS
    BCC +
    SEC
    SBC.w !F_ROWS
    INX
    BRA -
+   TXA
    BNE +
    INC
+   CMP.w #8
    BCC +
    LDA.w #8
+   STA.w !F_STEP
    STZ.w !F_I
.item:
    LDA.w !F_I
    CMP.w !F_COUNT
    BCS .bar
    ASL #3
    TAX
    LDA.w !ITEMS+1,X        ; rows narrower than the screen centered, as on the grid
    AND.w #$00FF
    PHX
    TAX
    LDA.w !ROWN,X
    AND.w #$00FF
    PLX
    CMP.w #!COLS
    BCC +
    LDA.w #!COLS
+   EOR.w #$FFFF
    SEC
    ADC.w #!COLS
    STA.w !F_T
    ASL
    CLC
    ADC.w !F_T
    LSR
    STA.w !F_T2             ; (6 - n) * 3 / 2
    LDA.w !ITEMS+2,X
    AND.w #$00FF
    CMP.w #6
    BCC +
    LDA.w #5
+   STA.w !F_T
    ASL
    CLC
    ADC.w !F_T
    CLC
    ADC.w !F_T2
    CLC
    ADC.w #!MAPX+3
    STA.w !F_X
    LDA.w !ITEMS+1,X
    AND.w #$00FF
    JSR MapY
    STA.w !F_Y
    LDA.w #1
    LDY.w !F_I
    CPY.w !F_CUR
    BNE +
    LDA.w #3
+   STA.w !F_C
    JSR Plot
    INC.w !F_X
    LDA.w !F_C
    JSR Plot
    INC.w !F_I
    JMP .item
.bar:
    LDA.w #!MAPX
    STA.w !F_X
    LDA.w !F_TOP
    JSR MapY
    STA.w !F_Y
    LDA.w !F_TOP
    CLC
    ADC.w #!SROWS
    JSR MapY
    DEC
    STA.w !F_END
    LDA.w #2
    STA.w !F_C
    JMP VLine

; A = row -> y of its dots
MapY:
    STA.w !F_T
    LDA.w #!GRIDY
    LDX.w !F_STEP
-   CLC
    ADC.w !F_T
    DEX
    BNE -
    RTS

; 제N장 number by chapter id (tables/qol-chapters.tsv)
ChapterNums:
    db 1,2,3,4,5,6,2,6,2,6,1,2,4,5,2,6,1,7,1,2,6,1,3,4,5,7,2,5,1,7

; 4 x 6 glyphs, one byte per row (high nibble): 0-9, A-E, N, arrow
SmallFont:
    db $60,$90,$90,$90,$90,$60      ; 0
    db $20,$60,$20,$20,$20,$70      ; 1
    db $60,$90,$10,$20,$40,$F0      ; 2
    db $E0,$10,$60,$10,$10,$E0      ; 3
    db $20,$60,$A0,$F0,$20,$20      ; 4
    db $F0,$80,$E0,$10,$10,$E0      ; 5
    db $60,$80,$E0,$90,$90,$60      ; 6
    db $F0,$10,$20,$40,$40,$40      ; 7
    db $60,$90,$60,$90,$90,$60      ; 8
    db $60,$90,$90,$70,$10,$60      ; 9
    db $60,$90,$90,$F0,$90,$90      ; A
    db $E0,$90,$E0,$90,$90,$E0      ; B
    db $70,$80,$80,$80,$80,$70      ; C
    db $E0,$90,$90,$90,$90,$E0      ; D
    db $F0,$80,$E0,$80,$80,$F0      ; E
    db $90,$D0,$D0,$B0,$B0,$90      ; N
    db $00,$20,$F0,$20,$00,$00      ; arrow
