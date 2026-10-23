#!/bin/zsh
# Build v1.3 from the Japanese ROM and the v1.1 IPS.
# usage: tools/build.sh   (outputs super-gokuden-kr-v1.3.smc and release IPS)
set -e
cd "$(dirname $0)/.."
mkdir -p work release/v1.3
python3 tools/ips.py apply super-gokuden-jp.smc v1.1/v1.1.ips work/build-v1.1.smc
python3 tools/fix_overwrites.py super-gokuden-jp.smc work/build-v1.1.smc work/build-fixed.smc
python3 tools/title.py work/build-fixed.smc work/build-title.smc --no-balls
python3 tools/dialogue_patch.py super-gokuden-jp.smc work/build-title.smc tables/dialogue-v1.3.tsv super-gokuden-kr-v1.3.smc tables/kr-v1.3.txt
python3 tools/bubble_patch.py super-gokuden-kr-v1.3.smc tables/bubbles-v1.3.tsv super-gokuden-kr-v1.3.smc tables/kr-v1.3.txt
python3 tools/password.py super-gokuden-jp.smc super-gokuden-kr-v1.3.smc super-gokuden-kr-v1.3.smc tables/kr-v1.3.txt
python3 tools/credits.py super-gokuden-kr-v1.3.smc
python3 tools/check_width.py super-gokuden-jp.smc super-gokuden-kr-v1.3.smc
python3 tools/fixsum.py super-gokuden-kr-v1.3.smc
python3 tools/ips.py make super-gokuden-jp.smc super-gokuden-kr-v1.3.smc "release/v1.3/Dragon Ball Z Super Gokuden - Kakusei Hen (K) v1.3.ips"
# Copier-headered ROMs: the same patch shifted by the 512-byte header.
python3 -c "import sys; sys.path.insert(0, 'tools'); import ips; h = bytes(0x200); open('release/v1.3/Dragon Ball Z Super Gokuden - Kakusei Hen (K) v1.3 (Headered).ips', 'wb').write(ips.make(h + open('super-gokuden-jp.smc', 'rb').read(), h + open('super-gokuden-kr-v1.3.smc', 'rb').read()))"
python3 -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('super-gokuden-kr-v1.3.smc','rb').read()))"
