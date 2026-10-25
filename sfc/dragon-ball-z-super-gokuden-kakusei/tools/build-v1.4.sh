#!/bin/zsh
# Build v1.4 (v1.3 plus the jamo name entry and the new 16 px name glyphs) on top of the v1.3 build.
# usage: tools/build-v1.4.sh   (needs tools/asar)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
OUT=super-gokuden-kr-v1.4.smc
zsh tools/build.sh
cp super-gokuden-kr-v1.3.smc $OUT
$PY tools/font16.py $OUT work
# asar takes a .smc file for a headered ROM, so assemble on a .sfc copy
cp $OUT work/v14.sfc
tools/asar --no-title-check asm/v14.asm work/v14.sfc
cp work/v14.sfc $OUT
$KRPATCH sfc checksum --fix --mapper lorom $OUT
mkdir -p release/v1.4
$KRPATCH ips make --rle super-gokuden-jp.smc $OUT "release/v1.4/Dragon Ball Z Super Gokuden - Kakusei Hen (K) v1.4.ips" \
    --headered "release/v1.4/Dragon Ball Z Super Gokuden - Kakusei Hen (K) v1.4 (Headered).ips"
$PY -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('$OUT','rb').read()))"
