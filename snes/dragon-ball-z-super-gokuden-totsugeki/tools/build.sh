#!/bin/zsh
# Build v1.2 from the Japanese ROM and the v1.0 IPS.
# usage: tools/build.sh   (outputs super-gokuden-kr-v1.2.smc)
set -e
cd "$(dirname $0)/.."
mkdir -p work
python3 tools/ips.py apply super-gokuden-jp.smc v1.0/v1.0.ips work/build-v1.0.smc
python3 tools/title.py work/build-v1.0.smc work/build-title.smc --no-balls
python3 tools/text_patch1.py super-gokuden-jp.smc work/build-title.smc super-gokuden-kr-v1.2.smc tables/kr-v1.2.txt \
    tables/v1.1/*.tsv tables/ui-fixes.tsv
python3 tools/pwglyph1.py super-gokuden-kr-v1.2.smc tables/kr-v1.2.txt
python3 tools/endpw1.py super-gokuden-kr-v1.2.smc tables/kr-v1.2.txt
python3 tools/fixsum.py super-gokuden-kr-v1.2.smc
python3 -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('super-gokuden-kr-v1.2.smc','rb').read()))"
