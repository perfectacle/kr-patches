#!/bin/zsh
# Build v1.3 (v1.2 plus the 8 px name glyphs and the jamo name entry) on top of the v1.2 build.
# usage: tools/build-v1.3.sh   (needs tools/asar)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
OUT=super-gokuden-kr-v1.3.smc
zsh tools/build.sh
cp super-gokuden-kr-v1.2.smc $OUT
$PY tools/font8.py $OUT work
# asar takes a .smc file for a headered ROM, so assemble on a .sfc copy
cp $OUT work/v13.sfc
tools/asar --no-title-check asm/v13.asm work/v13.sfc
cp work/v13.sfc $OUT
$KRPATCH sfc checksum --fix --mapper lorom $OUT
mkdir -p release/v1.3
$KRPATCH ips make --rle super-gokuden-jp.smc $OUT "release/v1.3/Dragon Ball Z Super Gokuden - Totsugeki Hen (K) v1.3.ips" \
    --headered "release/v1.3/Dragon Ball Z Super Gokuden - Totsugeki Hen (K) v1.3 (Headered).ips"
$PY -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('$OUT','rb').read()))"
