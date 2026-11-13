"""DS 메뉴에 나오는 배너(아이콘과 제목)를 버전 3 으로 만든다.

    banner.make(배너 바이트) -> 0xA40 바이트

제목은 UTF-16 문자열이고, DS 메뉴는 펌웨어에 든 글꼴로 그린다. 한국판이 아닌 펌웨어의 글꼴에는
한글이 없어 v1.1 이 넣은 「고스트 트릭」이 「@@@ @@」로 나온다. 그래서 일·영·프·독·이·스 칸
(버전 1)과 중국어 칸(버전 2)에는 라틴 문자 제목을, 한국판 펌웨어가 읽는 한국어 칸(버전 3)에만
한글 제목을 넣는다. 아이콘(비트맵·팔레트)은 받은 배너 그대로다.
"""
import struct

from kr_patch.nds.rom import crc16

SIZE = 0xA40
TITLE = 0x240
SLOT = 0x100
LATIN = "Ghost Trick (K)\nCAPCOM"
KOREAN = "고스트 트릭\nCAPCOM"
# 버전 1 은 0x840, 2 는 0x940, 3 은 0xA40 까지를 덮는 CRC 를 각각 둔다
CRCS = ((0x02, 0x840), (0x04, 0x940), (0x06, 0xA40))


def make(old):
    b = bytearray(SIZE)
    b[:TITLE] = old[:TITLE]
    struct.pack_into("<HHHHH", b, 0, 3, 0, 0, 0, 0)
    for i in range(8):
        text = (KOREAN if i == 7 else LATIN).encode("utf-16le")
        if len(text) >= SLOT:
            raise ValueError("banner title too long")
        b[TITLE + i * SLOT:TITLE + i * SLOT + len(text)] = text
    for off, end in CRCS:
        struct.pack_into("<H", b, off, crc16(b[0x20:end]))
    return bytes(b)
