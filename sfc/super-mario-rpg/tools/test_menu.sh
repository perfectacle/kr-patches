#!/bin/zsh
# Regression test for Korean item names in the field menu.
# usage: tools/test_menu.sh [rom]   (default build/test.sfc)
cd "$(dirname $0)/.."
ROM=${1:-build/test.sfc}
STATE=${STATE:-$PWD/test/states/keep_control.mss}
OUT=$PWD/test/out
mkdir -p $OUT
fail=0

# poke_list BASE IDS... -> "7FF8xx=id;..." for the 30-slot list starting at BASE
poke_list() {
  local base=$1; shift
  local p="" i=0
  for id in "$@"; do p="$p;$(printf '7FF8%02X=%s' $((base + i)) $id)"; i=$((i + 1)); done
  echo "${p#;}"
}

ids_range() {   # hex start, count, step
  local i; for i in $(seq 0 $(($2 - 1))); do printf '%02X ' $((0x$1 + i * ${3:-1})); done
}

ITEM_SEQ="x:3,wait:60,a:3,wait:60"
EQUIP_SEQ="x:3,wait:60,down:3,wait:10,down:3,wait:10,down:3,wait:10,a:3,wait:60,a:3,wait:60"

run_case() {   # name seq verify-ids poke
  local name=$1 seq=$2 ids=$3 poke=$4
  POKE="003112=FF;$poke" tools/run_seq.sh $ROM ${STATE_OVERRIDE:-$STATE} $OUT/$name "$seq" 1000 30 >/dev/null 2>&1
  if ${PYTHON:-${PWD:h:h}/.venv/bin/python} -I tools/py/verify_menu.py $OUT/$name ${=ids} > $OUT/$name/verify.txt; then
    echo "PASS $name ($(head -1 $OUT/$name/verify.txt))"
  else
    echo "FAIL $name"; sed 's/^/    /' $OUT/$name/verify.txt; fail=1
  fi
}

A=$(ids_range 60 30); B=$(ids_range 7E 30); C=$(ids_range 05 30); D=$(ids_range 23 30)
run_case A_items1 "$ITEM_SEQ" "$A" "$(poke_list 0x82 ${=A})"
run_case B_items2 "$ITEM_SEQ" "$B" "$(poke_list 0x82 ${=B})"
run_case C_equip1 "$EQUIP_SEQ" "$C" "$(poke_list 0x64 ${=C})"
run_case D_equip2 "$EQUIP_SEQ" "$D" "$(poke_list 0x64 ${=D})"
run_case E_items_then_equip "x:3,wait:60,a:3,wait:60,b:3,wait:40,down:3,wait:10,down:3,wait:10,down:3,wait:10,a:3,wait:60,a:3,wait:60" "$D" "$(poke_list 0x82 ${=A});$(poke_list 0x64 ${=D})"
# Names that had spaces in the official spelling
F="6F 7B 7E 94 99 9A 9B"; G="1D 20 4F 50 58"
run_case F_items_nospace "$ITEM_SEQ" "$F" "$(poke_list 0x82 ${=F})"
run_case G_equip_nospace "$EQUIP_SEQ" "$G" "$(poke_list 0x64 ${=G})"
# The 30 items with the most syllables missing from the menu font (63 glyph slots).
H="A6 8D 94 97 99 71 9D 63 73 76 77 7A 7D 88 8A 8E 92 9E A2 AE 64 69 6A 6C 79 7B 7E 83 84 89"
run_case H_items_most_glyphs "$ITEM_SEQ" "$H" "$(poke_list 0x82 ${=H})"
# Toad's item tutorial (all NMI task slots busy): glyphs must still upload.
TUT="a:3"; for i in $(seq 1 6); do TUT="$TUT,wait:30,a:3"; done; TUT="$TUT,wait:40,x:3"; for i in $(seq 1 11); do TUT="$TUT,wait:40,a:3"; done; TUT="$TUT,wait:40"
STATE_OVERRIDE=$PWD/test/states/user_4.mss run_case T_toad_tutorial "$TUT" "60" ""
# Shop (buy list and sell lists); the shop's tilemap buffer differs, so only glyph bitmaps are checked.
# Starts outside the menu: a state saved inside it keeps glyphs uploaded by the ROM that saved it.
SHOP_OPEN="wait:5,a:3,wait:40,a:3,wait:40,a:3,wait:40,a:3,wait:40"
STATE_OVERRIDE=$PWD/test/states/shop.mss run_case S_shop_buy "$SHOP_OPEN,a:3,wait:60" "" ""
STATE_OVERRIDE=$PWD/test/states/shop.mss run_case S_shop_sell "$SHOP_OPEN,down:3,wait:15,a:3,wait:80" "" ""
exit $fail
