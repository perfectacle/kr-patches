제절초 한글패치 v1.1 / v1.2 빌드 도구

어떤 문제를 어떤 도구로 풀었는지는 아래 페이지의 「롬 분석 노트」에 있습니다.
 https://perfectacle.github.io/games/kr-patches/sfc/otogirisou/#making
롬 주소와 형식 전체는 압축 파일 맨 위의 ANALYSIS.txt에 있습니다.

이 압축 파일에는 롬, asar, Mesen, libretro 코어가 들어 있지 않습니다.

필요한 것
 - Python 3 + Pillow
 - asar 1.91 (tools/asar 에 실행 파일을 두세요)
 - 일본판 롬: Otogirisou (Japan).sfc (헤더 없음, CRC32 8E4BEFD0)
 - v1.0 IPS: Otogirisou(K).ips (첨부)

빌드
 tools/build.sh         → build/otogirisou-kr-v1.1.sfc
 tools/release.sh       → release/v1.1/*.ips, 해시값 출력
 tools/build-v1.2.sh    → build/otogirisou-kr-v1.2.sfc (v1.1 롬 위에 편의 기능)
 tools/release-v1.2.sh  → release/v1.2/*.ips, 해시값 출력

대사 수정
 tables/script.txt 를 고친 뒤 빌드합니다. 같은 줄 번호의 일본어는 tables/script-jp.txt 에 있습니다.
 이 파일은 압축 파일에 넣지 않았습니다. tools/build.sh 가 처음 실행될 때 일본판 롬에서 뽑아 만듭니다.
 빌드할 때마다 build/waits.tsv (입력 대기 위치)와 build/overflow.tsv (9줄 초과)를 확인하세요.
 9줄을 넘는 페이지는 tools/splitpages.py 로 나눌 수 있습니다.

새 글자
 v1.0 폰트에 없는 글자를 쓰면 빌드가 경고를 냅니다. tables/newglyphs.json 에 그려 넣으세요.
 tools/glyph_workbench.py 로 v1.0 글리프를 보거나 이어 붙일 수 있습니다.

에뮬레이터 검증 (Mesen 2 테스트 러너)
 LIBDIR=lua LAP=1 STABLE=18 PERIOD=40 SHOT_DIR=out Mesen --testrunner rom.sfc lua/pages.lua

v1.2 편의 기능
 장 구분: tables/qol-chapters.tsv (장 번호, 제목, 시작 줄, 레인, 레인 범위, 변수 17 복원)
 엔딩: tables/qol-endings.tsv ({1D}가 있는 줄, 제목)
 데이터: tools/qol.py (bank $1B), tools/flow.py (bank $1C). 코드: asm/qol.asm, asm/flow.asm
 테스트: lua/qol/menujump.sh rom.sfc 템플릿.srm 출력폴더 (MESEN=Mesen 2 실행 파일 경로)
