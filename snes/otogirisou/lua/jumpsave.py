"""Write a .srm whose slot 1 resumes at a given script address, for capturing scenes deep
in the game. The template slot supplies everything else; the name is set to NAME codes.
usage: jumpsave.py template.srm out.srm ADDR [--v11]"""
import sys
NAME = [1176, 1170, 514, 0xFFFF]     # 코헤이, the Japanese default name 公平
tpl, out, addr = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
d = bytearray(open(tpl, 'rb').read())
b = 0x5E3
d[b + 0x5AC:b + 0x5AF] = addr.to_bytes(3, 'little')
d[b + 0x5AF:b + 0x5B1] = bytes(2)
d[b + 0x59A:b + 0x59C] = bytes(2)
d[b + 0x5B5:b + 0x5B7] = (0xC311 if '--v11' in sys.argv else 0).to_bytes(2, 'little')
for base in (0x5D5, 0x57A):
    for i, c in enumerate(NAME):
        d[b + base + 2 * i:b + base + 2 * i + 2] = c.to_bytes(2, 'little')
d[b + 0x20:b + 0x22] = (sum(d[b + 0x22:b + 0x22 + 0x5E1]) & 0xFFFF).to_bytes(2, 'little')
d[0x20:0x20 + b] = d[b + 0x20:b + 0x20 + b]    # slot 0 is the working copy
d[0x22] = 1
d[0x20:0x22] = (sum(d[0x22:0x22 + 0x5E1]) & 0xFFFF).to_bytes(2, 'little')
open(out, 'wb').write(d)
