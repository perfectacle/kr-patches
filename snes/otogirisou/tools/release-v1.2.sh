#!/bin/zsh
# Build v1.2 and write the release IPS files (plain and 512-byte header), verify both
# round-trip, and print the hashes. Needs build/otogirisou-kr-v1.1.sfc.
set -e
cd "$(dirname $0)/.."
tools/build-v1.2.sh
R=release/v1.2
JP="Otogirisou (Japan).sfc"
OUT=build/otogirisou-kr-v1.2.sfc
mkdir -p $R
python3 tools/ips.py make "$JP" $OUT "$R/Otogirisou (K) v1.2.ips"
python3 - <<'PY'
d = bytes(512)
open('build/jp_headered.sfc', 'wb').write(d + open('Otogirisou (Japan).sfc', 'rb').read())
open('build/kr12_headered.sfc', 'wb').write(d + open('build/otogirisou-kr-v1.2.sfc', 'rb').read())
PY
python3 tools/ips.py make build/jp_headered.sfc build/kr12_headered.sfc "$R/Otogirisou (K) v1.2 (Headered).ips"
python3 tools/ips.py apply "$JP" "$R/Otogirisou (K) v1.2.ips" build/check.sfc && cmp build/check.sfc $OUT
python3 tools/ips.py apply build/jp_headered.sfc "$R/Otogirisou (K) v1.2 (Headered).ips" build/check_h.sfc && cmp build/check_h.sfc build/kr12_headered.sfc
python3 - <<'PY'
import hashlib, re, zlib
d = open('build/otogirisou-kr-v1.2.sfc', 'rb').read()
crc, md5 = '%08X' % zlib.crc32(d), hashlib.md5(d).hexdigest().upper()
print('release ok: CRC32', crc, 'MD5', md5)
PY
