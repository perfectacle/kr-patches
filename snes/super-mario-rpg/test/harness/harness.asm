; Test-only additions on top of build/test.sfc (never shipped).
; Dialogue override: while $7E17F0 = $A55A, the first dialogue that opens
; shows dialogue $7E17F2 instead (poke both every frame from run_seq);
; $7E17F4 records that it was used, so later dialogues are left alone.
sa1rom

org $C05809
    JSL TestDlgId

org $E2FE00
TestDlgId:
    REP #$20
    LDA.l $7E17F0
    CMP #$A55A
    BNE +
    LDA.l $7E17F4
    BNE +
    INC
    STA.l $7E17F4
    LDA.l $7E17F2
    STA $80
+
    LDA $80
    RTL
assert pc() <= $E2FF00
