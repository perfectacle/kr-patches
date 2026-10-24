# 고스트 트릭(NDS) 한글패치 v1.2

[English](README.md) | 한국어

일본판 닌텐도 DS *고스트 트릭* 한글패치 v1.2 의 소스입니다. 일본판 롬에
한글패치 v1.1 을 적용한 롬에서 시작해, 대사 스크립트를 일본판 스크립트에서
다시 만듭니다. 폰트와 그래픽은 v1.1 그대로입니다.

패치 페이지: <https://perfectacle.github.io/games/kr-patches/nds/ghost-trick/>

롬 구조, 스크립트·폰트 형식, v1.1 에서 찾은 문제, 대화창 폭 실측은
[docs/ANALYSIS.ko.md](docs/ANALYSIS.ko.md) 에 정리했습니다.

## 원본 롬

롬은 들어 있지 않습니다. 직접 덤프한 일본판 카드 롬을 이 폴더에
`ghost-trick-jp.nds` 로 두세요.

| | |
| --- | --- |
| 헤더 제목·게임 코드 | `GHOSTTRICK-J`, `BGTJ` (134,217,728 바이트) |
| CRC32 | `105DDD9E` |
| SHA-1 | `323901c81e6e9300e2221e5cc42289cc5be73dce` |

`v1.1/v1.1.xdelta` 는 v1.1 패치(xdelta3, VCDIFF)이고 빌드가 먼저 적용합니다.
적용한 v1.1 롬은 119,459,746 바이트, CRC32 `D366A4D9` 입니다.

## 빌드

준비물: 저장소의 Python 환경(최상위 README 참고), zsh, `xdelta3`(PATH 에 있어야
함, 3.2.2 에서 확인).

```sh
zsh tools/build.sh
```

결과물: `ghost-trick-kr-v1.2.nds`(119,462,534 바이트, CRC32 `EA51D7F3`)와
`release/v1.2/Ghost Trick (K) v1.2.xdelta`. 배포한 패치와 같습니다. 패치
바이트는 `xdelta3` 버전에 따라 달라질 수 있으니 롬 CRC32 로 비교하세요.
다른 환경을 쓰려면 `PYTHON`, `KRPATCH` 를 지정합니다.

단계: `krpatch xdelta apply`(v1.1) → `tools/check.py`(문제가 있으면 빌드
중단) → `tools/build.py` → `krpatch xdelta make`.

`tools/build.py` 는 스크립트 파일(`stNN/*_Expand.xml.lz`, `system/*.bin`)마다
일본판 스크립트에 `tables/v1.2/script.tsv` 의 대사를 차례로 이어 쓰고, 옮겨 간
대사를 가리키는 포인터와 레이블을 고칩니다. 대사 머리(창·번호)는 일본판 값을
씁니다. 롬은 `kr_patch.nds.rom` 으로 다시 묶습니다.

## 대본 고치기

`tables/v1.2/script.tsv` 는 일본판 대사 하나에 한 줄입니다. 열은 `file`(롬 안
경로), `run`(파일 안 대사 묶음 번호), `i`(묶음 안 순번), `ko`(대사)입니다.
`ko` 표기:

- 글자: 한글(KS X 1001 2350자)과 `tables/low.tsv` 의 앞쪽 글자(숫자·영문·가나·기호).
- `{01}` 줄바꿈, `{02}` 다음 창, `{XX}`·`{XX:a,b}` 제어 코드(인수는 16진),
  `[hex]` 글자표에 없는 값. 인수 개수는 `tools/textcodec.py` 의 `ARGS`.
- `{08:xx}`·`{1B:xx}` 는 말하는 인물, `{05:xx}` 는 글자색(`{05:f}` 가 기본색).

일본어와 나란히 보려면 대사를 뽑습니다(결과는 롬에서 나온 일본어를 담고 있으니
저장소에 넣지 않습니다).

```sh
../../.venv/bin/python tools/dump.py ghost-trick-jp.nds ghost-trick-kr-v1.2.nds work/side.tsv
```

고친 뒤에는 `tools/check.py` 가 다음을 봅니다: 글자표에 없는 글자, 제어 코드 열이
v1.1·일본판과 다름, 줄 넘침(초상화가 창 안에 있는 창 13자, 전체 폭 창 16자),
창 하나에 일본어보다 많은 줄, 남은 일본어.

```sh
../../.venv/bin/python tools/check.py ghost-trick-jp.nds work/build-v1.1.nds tables/v1.2/script.tsv
```

## 구성

| 경로 | 내용 |
| --- | --- |
| `tables/v1.2/script.tsv` | v1.2 대본(4,048 대사: 본편 3,503, `system/` 545) |
| `tables/jp.tsv` | 일본판 대사 폰트 코드표(글자 번호 → 글자) |
| `tables/low.tsv` | 한국어판 코드표의 0x000–0x12B(그 뒤는 KS X 1001 순서의 한글) |
| `tools/` | 빌드·검사·에뮬레이터 도구(사용법은 각 파일 첫 줄) |
| `v1.1/` | 빌드의 출발점인 v1.1 패치 |

## 테스트

에뮬레이터는 desmume libretro 코어를 씁니다. libretro/desmume 의 커밋
`95b4d79`(2026-09-20)을 직접 빌드해 `compat/cores/desmume_libretro.dylib` 에
둡니다(`make -C desmume/src/frontend/libretro`). melonDS DS v1.4.0 코어는 롬을
읽은 뒤 멈춰서 쓰지 않습니다.

```sh
# 전원을 켜고 버튼·터치를 넣어 가며 화면을 찍는다(세이브 스테이트로 이어 갈 수 있음)
../../.venv/bin/python tools/play.py ghost-trick-kr-v1.2.nds out --save s1.state --cmd "wait 600; press start; a 20; shot title"
# 「처음부터」가 다른 스테이지·장면에서 시작하는 시험 롬
../../.venv/bin/python tools/stage_rom.py ghost-trick-kr-v1.2.nds work/st06.nds 06 game004
# 대사 하나를 시험 문장으로 바꾼 롬(창 폭 실험)
../../.venv/bin/python tools/probe.py ghost-trick-jp.nds ghost-trick-kr-v1.2.nds work/probe.nds st01/st01_game000_Expand.xml.lz 0 0 "가나다라마바사아자차카타파하"
# 첫 장면에 확인할 대사를 모은 롬
../../.venv/bin/python tools/gallery.py ghost-trick-kr-v1.2.nds tables/v1.2/script.tsv work/gallery.nds st06/st06_game002_Expand.xml.lz:0:15
```

`tools/font_store.py` 는 대사 폰트(`fonts2bpp_new.imb`)를 툴킷 글리프
저장소(JSON)로 뽑습니다.

## 라이선스

코드(Python, 셸): MIT, 최상위 `LICENSE` 참고. 한국어 대본, 코드표, v1.1 패치는
팬 번역 데이터라 MIT 가 아니며 비상업으로 배포합니다.
