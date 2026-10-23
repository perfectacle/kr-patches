#!/bin/zsh
# Build v1.2 from the Japanese ROM and the v1.0 IPS.
# usage: tools/build.sh   (outputs super-gokuden-kr-v1.2.smc and release IPS)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
mkdir -p work release/v1.2
$KRPATCH ips apply super-gokuden-jp.smc v1.0/v1.0.ips work/build-v1.0.smc
$PY tools/title.py work/build-v1.0.smc work/build-title.smc --no-balls
$PY tools/text_patch1.py super-gokuden-jp.smc work/build-title.smc super-gokuden-kr-v1.2.smc tables/kr-v1.2.txt \
    tables/v1.1/*.tsv tables/ui-fixes.tsv
$PY tools/pwglyph1.py super-gokuden-kr-v1.2.smc tables/kr-v1.2.txt
$PY tools/endpw1.py super-gokuden-kr-v1.2.smc tables/kr-v1.2.txt
$KRPATCH snes checksum --fix --mapper lorom super-gokuden-kr-v1.2.smc
# The second patch is for ROMs with a 512-byte copier header.
$KRPATCH ips make super-gokuden-jp.smc super-gokuden-kr-v1.2.smc "release/v1.2/Dragon Ball Z Super Gokuden - Totsugeki Hen (K) v1.2.ips" \
    --headered "release/v1.2/Dragon Ball Z Super Gokuden - Totsugeki Hen (K) v1.2 (Headered).ips"
$PY -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('super-gokuden-kr-v1.2.smc','rb').read()))"
