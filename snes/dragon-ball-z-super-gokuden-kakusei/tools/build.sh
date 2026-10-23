#!/bin/zsh
# Build v1.3 from the Japanese ROM and the v1.1 IPS.
# usage: tools/build.sh   (outputs super-gokuden-kr-v1.3.smc and release IPS)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
mkdir -p work release/v1.3
$KRPATCH ips apply super-gokuden-jp.smc v1.1/v1.1.ips work/build-v1.1.smc
$PY tools/fix_overwrites.py super-gokuden-jp.smc work/build-v1.1.smc work/build-fixed.smc
$PY tools/title.py work/build-fixed.smc work/build-title.smc --no-balls
$PY tools/dialogue_patch.py super-gokuden-jp.smc work/build-title.smc tables/dialogue-v1.3.tsv super-gokuden-kr-v1.3.smc tables/kr-v1.3.txt
$PY tools/bubble_patch.py super-gokuden-kr-v1.3.smc tables/bubbles-v1.3.tsv super-gokuden-kr-v1.3.smc tables/kr-v1.3.txt
$PY tools/password.py super-gokuden-jp.smc super-gokuden-kr-v1.3.smc super-gokuden-kr-v1.3.smc tables/kr-v1.3.txt
$PY tools/credits.py super-gokuden-kr-v1.3.smc
$PY tools/check_width.py super-gokuden-jp.smc super-gokuden-kr-v1.3.smc
$KRPATCH snes checksum --fix --mapper lorom super-gokuden-kr-v1.3.smc
# Copier-headered ROMs: the same patch shifted by the 512-byte header.
$KRPATCH ips make super-gokuden-jp.smc super-gokuden-kr-v1.3.smc "release/v1.3/Dragon Ball Z Super Gokuden - Kakusei Hen (K) v1.3.ips" \
    --headered "release/v1.3/Dragon Ball Z Super Gokuden - Kakusei Hen (K) v1.3 (Headered).ips"
$PY -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('super-gokuden-kr-v1.3.smc','rb').read()))"
