#!/bin/zsh
# Build v1.1 and write the release IPS files (plain and 512-byte header), verify both
# round-trip, and print the hashes.
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
tools/build.sh
R=release/v1.1
JP="Otogirisou (Japan).sfc"
OUT=build/otogirisou-kr-v1.1.sfc
mkdir -p $R
$KRPATCH ips make "$JP" $OUT "$R/Otogirisou (K) v1.1.ips"
"$PY" - <<'PY'
d = bytes(512)
open('build/jp_headered.sfc', 'wb').write(d + open('Otogirisou (Japan).sfc', 'rb').read())
open('build/kr_headered.sfc', 'wb').write(d + open('build/otogirisou-kr-v1.1.sfc', 'rb').read())
PY
$KRPATCH ips make build/jp_headered.sfc build/kr_headered.sfc "$R/Otogirisou (K) v1.1 (Headered).ips"
$KRPATCH ips apply "$JP" "$R/Otogirisou (K) v1.1.ips" build/check.sfc && cmp build/check.sfc $OUT
$KRPATCH ips apply build/jp_headered.sfc "$R/Otogirisou (K) v1.1 (Headered).ips" build/check_h.sfc && cmp build/check_h.sfc build/kr_headered.sfc
"$PY" - <<'PY'
import hashlib, re, zlib
d = open('build/otogirisou-kr-v1.1.sfc', 'rb').read()
crc, md5 = '%08X' % zlib.crc32(d), hashlib.md5(d).hexdigest().upper()
print('release ok: CRC32', crc, 'MD5', md5)
PY
