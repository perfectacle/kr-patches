드래곤볼 Z 초오공전 돌격편 한글패치 v1.2 도구 묶음

필요한 것: Python 3 (Pillow, numpy), zsh, Mesen 2 (Lua 스크립트 실행용)

1. 빌드
   이 폴더에 일본판 원본 롬(헤더 없음, CRC32 D531289B)을 super-gokuden-jp.smc로 두고
   zsh tools/build.sh
   → super-gokuden-kr-v1.2.smc (CRC32 81DAD733)
   타이틀 글꼴 BM영성체는 macOS 시스템 글꼴 경로에서 읽습니다. (tools/title.py의 TITLE_FONT)

2. 폴더
   ANALYSIS.txt  롬 분석 문서 (헤더, 메모리, 대사·폰트 형식, 후킹 주소, 쓴 빈 공간, 디버그 메뉴)
   tools/   빌드와 분석 도구 (각 파일 첫머리에 사용법)
   tables/  v1.1/  : v1.1 텍스트 (id, 창 정보, 본문)
            ui-fixes.tsv : 포인터 테이블 밖 메뉴 문자열
            *-v1.0.tsv : 일본어 원문과 v1.0 번역 대조 덤프
            jp-verified.txt, kr-v1.0.txt : 일본판 / v1.0 글자 코드표
            kr-v1.2-glyphs.txt : v1.2가 다시 그린 다섯 자리의 이름 (kr-v1.0.txt 위에 덮음)
            password.tsv : 엔딩 암호 글자 163자 (코드, 가나, v1.1 화면, v1.2 화면)
   v1.0/    v1.0 IPS (빌드의 기반)
   lua/     Mesen 2 테스트 러너용 스크립트
   compat/  libretro 코어 비교 (compat/run_all.sh 머리말)

3. 디버그 시나리오 실행 (Mesen 2)
   롬 파일 0x61의 80 04를 EA EA로 바꾸면 디버그 메뉴가 켜집니다.
   TARGET=10 SHOTS=1 SHOT_DIR=out Mesen --testrunner debug.smc lua/scenario.lua
   → out/ids.txt (프레임, 대사 ID), out/q*.png
   python3 tools/pages1.py out 0142   → 대사 0142의 페이지별 완성 화면 프레임
   두 롬의 실행 결과 폴더 묶음 비교: python3 tools/rgcmp1.py runs_jp runs_kr

4. 클리어 표 이벤트 목록 문제 재현
   TARGET=c0 SHOT_DIR=out Mesen --testrunner debug.smc lua/eventlist.lua

5. 엔딩 암호 화면 (Mesen 2)
   엔딩 직전 세이브 스테이트에서 이름을 바꿔 암호 화면을 찍습니다.
   NAME=12C,142,14C,14D,1C8 ST=ending.mss SHOT_DIR=out Mesen --testrunner debug.smc lua/ending.lua
   → out/password.png, out/pw.bin ($7E:0A00), out/name.bin ($7E:0B01)
   글자 검사는 빌드 안에서 tools/pwglyph1.py가 합니다.
   전체 텍스트 덤프 비교: python3 tools/textdump1.py 롬.smc out.tsv
