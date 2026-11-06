#!/bin/zsh
# Build v1.4 (v1.3 plus name-list labels of equal width) on top of the v1.3 build.
# usage: tools/build-v1.4.sh   (needs tools/asar)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
OUT=super-gokuden-kr-v1.4.smc
zsh tools/build-v1.3.sh
cp super-gokuden-kr-v1.3.smc $OUT
$PY tools/namelabels1.py $OUT tables/kr-v1.2.txt
$KRPATCH sfc checksum --fix --mapper lorom $OUT
mkdir -p release/v1.4
$KRPATCH ips make --rle super-gokuden-jp.smc $OUT "release/v1.4/Dragon Ball Z Super Gokuden - Totsugeki Hen (K) v1.4.ips" \
    --headered "release/v1.4/Dragon Ball Z Super Gokuden - Totsugeki Hen (K) v1.4 (Headered).ips"
$PY -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('$OUT','rb').read()))"
