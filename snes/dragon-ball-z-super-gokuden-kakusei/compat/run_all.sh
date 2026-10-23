#!/bin/zsh
# usage: run_all.sh  -> out/<scenario>-<emulator>-<rom>/ and results.txt
# Every emulator gets the same script: libretro cores through `krpatch snes run`,
# Mesen 2 through the toolkit's script.lua; wram.log follows the scene word
# $7E029C. Cores and Mesen paths are this machine's.
cd "$(dirname $0)"
KRPATCH=${KRPATCH:-${PWD:h:h:h}/.venv/bin/krpatch}
LUA=$($KRPATCH snes lua)
WATCH=(--watch 7E029C:2 --watch-fmt 03x)
MESEN=${MESEN:-/Users/gwonsungyang/kr-patch/smrpg/tools/Mesen.app/Contents/MacOS/Mesen}
MESEN_SAVES=${MESEN_SAVES:-$HOME/Library/Application Support/Mesen2/Saves}
export LRVARS="supafaust_thread_affinity_ppu=0x0,supafaust_thread_affinity_emu=0x0"
# scenario:roms (jp/v12/v13 = plain, v13h = copier header, *d = debug menu on)
SETS=(new:jp,v13,v13h cont:jp,v12,v13,v13h bubble:jpd,v13d narration:jpd,v13d pwjp:jp pwko:v12,v13 pwdebug:v13 phrase:v12,v13 wrong:v13 cheat:v13)
run() {  # emulator scenario rom
  local f=roms/$3.sfc; [[ $3 == v13h ]] && f=roms/v13h.smc
  local d=out/$2-$1-$3; rm -rf $d; mkdir -p $d
  if [[ $1 == mesen2 ]]; then
    [[ $2 == cont ]] && cp roms/save.srm "$MESEN_SAVES/${f:t:r}.srm"
    [[ $2 != cont ]] && rm -f "$MESEN_SAVES/${f:t:r}.srm"
    LIBDIR=$LUA SCRIPT=$PWD/s_$2.txt SHOT_DIR=$PWD/$d WATCH_WRAM=7E029C:2 WATCH_FMT=%03x $MESEN --testrunner $PWD/$f $LUA/script.lua > $d.log 2>&1
    echo "exit=$? $(tail -1 $d/wram.log)"
  elif [[ $2 == cont ]]; then $KRPATCH snes run cores/$1_libretro.dylib $f $d s_$2.txt roms/save.srm $WATCH > $d.log 2>&1; echo "exit=$? $(tail -1 $d.log)"
  else $KRPATCH snes run cores/$1_libretro.dylib $f $d s_$2.txt $WATCH > $d.log 2>&1; echo "exit=$? $(tail -1 $d.log)"; fi
}
: > results.txt
for emu in mesen2 bsnes bsnes_hd_beta snes9x snes9x2010 mednafen_supafaust mesen-s; do
  for s in $SETS; do
    for rom in ${(s:,:)s#*:}; do
      echo "${s%%:*} $emu $rom $(run $emu ${s%%:*} $rom)" >> results.txt
    done
  done
done
