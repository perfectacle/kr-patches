#!/bin/zsh
# Build v1.3 from the Japanese ROM and the v1.1 xdelta.
# usage: tools/build.sh   (outputs ghost-trick-kr-v1.3.nds and the release xdelta)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
mkdir -p work release/v1.3
$KRPATCH xdelta apply ghost-trick-jp.nds v1.1/v1.1.xdelta work/build-v1.1.nds
$PY tools/check.py ghost-trick-jp.nds work/build-v1.1.nds tables/v1.2/script.tsv
$PY tools/build.py ghost-trick-jp.nds work/build-v1.1.nds ghost-trick-kr-v1.3.nds tables/v1.2/script.tsv
$KRPATCH xdelta make ghost-trick-jp.nds ghost-trick-kr-v1.3.nds "release/v1.3/Ghost Trick (K) v1.3.xdelta"
$PY -c "import zlib;print('CRC32 %08X'%zlib.crc32(open('ghost-trick-kr-v1.3.nds','rb').read()))"
