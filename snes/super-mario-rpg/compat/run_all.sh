#!/bin/zsh
# usage: run_all.sh  -> out/<scenario>-<core>-<rom>/ and results.txt
# new: power on, new game, tap A through the opening to Bowser's Keep.
# cont: continue a v1.1 save (Yoshi Cookie in the first 6 item slots), walk into
#       the Spikey group, use Yoshi Cookie on three turns.
# cont_long: the same with Yoshi Cookie on 30 turns, for cores where three turns
#       never turn a monster into an item.
# roms/save_pre.srm is the save RAM of a Mesen 2 save state (dumpsrm.lua from `krpatch snes lua`);
# make_save.py turns it into roms/save_cookie.srm.
# libretro cores run through `krpatch snes run`, Mesen 2 through the toolkit's
# script.lua, both logging the script pointer $7E0052-54. Mesen 2 keeps its own
# save file per ROM name (Saves/<name>.srm) and loads it on power-on, so the
# ROMs are copied under names only this script uses and those saves are deleted.
cd "$(dirname $0)"
KRPATCH=${KRPATCH:-${PWD:h:h:h}/.venv/bin/krpatch}
LUA=$($KRPATCH snes lua)
export LRVARS="supafaust_thread_affinity_ppu=0x0,supafaust_thread_affinity_emu=0x0"
: > results.txt
run() { # scenario core rom [save]
  local d=out/$1-$2-$3 f=roms/$3.sfc
  rm -rf $d; mkdir -p $d
  $KRPATCH snes run cores/$2_libretro.dylib $f $d s_$1.txt ${4:+roms/$4.srm} --watch 7E0052:3 > $d.log 2>&1
  echo "$1 $2 $3 exit=$? $(grep -E '^OK|LOAD FAILED|terminat|Segmentation' $d.log | tail -1)" >> results.txt
}
for core in bsnes bsnes_hd_beta snes9x snes9x2010 mednafen_supafaust mesen-s; do
  for rom in jp v11 v12; do
    run new $core $rom
    run cont $core $rom save_cookie
  done
done
for core in snes9x snes9x2010 mednafen_supafaust; do
  for rom in jp v11 v12; do run cont_long $core $rom save_cookie; done
done
MESEN=${MESEN:-$HOME/kr-patch/smrpg/tools/Mesen.app/Contents/MacOS/Mesen}
SAVES="$HOME/Library/Application Support/Mesen2/Saves"
mkdir -p roms/mesen
for sc in new cont; do
  for rom in jp v11 v12; do
    d=out/$sc-mesen2-$rom
    rm -rf $d; mkdir -p $d; rm -f "$SAVES"/smrpg_compat_*.srm(N)
    cp roms/$rom.sfc roms/mesen/smrpg_compat_$rom.sfc
    env LIBDIR=$LUA SCRIPT=$PWD/s_$sc.txt SHOT_DIR=$PWD/$d WATCH_WRAM=7E0052:3 ${${sc:#new}:+SRM=$PWD/roms/save_cookie.srm} \
      $MESEN --testrunner --timeout=600 $PWD/roms/mesen/smrpg_compat_$rom.sfc $LUA/script.lua > $d.log 2>&1
    echo "$sc mesen2 $rom exit=$? shots=$(ls $d | wc -l | tr -d ' ')" >> results.txt
  done
done
rm -f "$SAVES"/smrpg_compat_*.srm(N)
