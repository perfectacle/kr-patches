#!/bin/zsh
# usage: run_seq.sh rom state outdir "seq" [every] [tail]
# env: POKE="addr=val;..."  WATCH="name=addr[:len];..."  SHOTS=0 (skip periodic q*.png)
cd "$(dirname $0)/.."
rm -rf "$3" && mkdir -p "$3"
POKE="$POKE" WATCH="$WATCH" SHOTS="$SHOTS" LIBDIR=$PWD/test STATE=$2 SEQ="$4" EVERY=${5:-60} TAIL=${6:-120} SHOT_DIR=$3 \
  tools/Mesen.app/Contents/MacOS/Mesen --testrunner "$1" test/seq.lua 2>&1 | grep -v Uninit | tail -3
[[ -f "$3/watch.txt" ]] && cat "$3/watch.txt"
qs=("$3"/q*.png(N))
(( $#qs )) && .venv/bin/python -I tools/py/contact.py "$3/q*.png" "$3/contact.png" 8 >/dev/null; true
