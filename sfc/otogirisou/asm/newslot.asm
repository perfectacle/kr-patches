; MarkNew from asm/savecompat.asm, assembled over it with 16 bit immediates.
; A is 16 bit at $02:A54F: the REP #$20 at $02:A505 is still in effect, and $02:A569
; returns with the caller's flags. 8 bit immediates decode as other instructions there,
; leaving the new slot without the marker, so LoadSave would translate its start as a
; v1.0 position. savecompat.asm keeps its bytes so that v1.1-v1.3 build as released.
lorom

!MAGIC = $C311
!MARK = $7005B5

org $188000
MarkNew:
    LDA $13
    STA.l $7005AF,X
    LDA.w #!MAGIC
    STA.l !MARK,X
    RTL
warnpc $188013              ; MarkSave
