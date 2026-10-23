슈퍼 마리오 RPG (SFC) 한글패치 v1.2 빌드 도구

설명: https://perfectacle.github.io/games/kr-patches/sfc/super-mario-rpg/#making
(「롬 분석 노트」의 각 항목 끝에 그 내용을 다루는 파일을 적어 두었습니다.)

롬 헤더, 메모리, 대사·폰트 형식, 후킹 주소, 쓴 빈 공간, 디버그 기능은 ANALYSIS.txt에 정리했습니다.

이 압축 파일에는 롬, asar, Mesen이 들어 있지 않습니다.

준비물
 - 일본판 원본 롬 (헤더 없음, 4,194,304바이트)
   CRC32 5527071E / MD5 59483FEB9EB20207E3241E005FBDDE7E
 - Python 3 + Pillow
 - asar 1.91 (https://github.com/RPGHacker/asar)
 - zsh (tools/make.sh 실행용)

빌드 순서
 1. 일본판 원본에 v1.0/Super Mario RPG (K) (V1.0).ips를 적용합니다.
    결과(CRC32 F4305A06)를 rom/smrpg_kr_v1.sfc 이름으로 둡니다.
    v1.2는 이 v1.0 롬 위에 덧씌우는 방식으로 빌드합니다.
 2. asar 실행 파일을 tools/asar로 둡니다.
 3. 압축을 푼 폴더에서 파이썬 가상환경을 만듭니다. (make.sh가 .venv/bin/python을 씁니다)
      python3 -m venv .venv
      .venv/bin/pip install pillow
 4. zsh tools/make.sh
    결과: build/test.sfc (CRC32 05DBCBE6)
 5. IPS 만들기 (일본판 원본 기준)
      .venv/bin/python -I tools/py/make_ips.py rom/smrpg_jp.sfc build/test.sfc v1.2.ips v1.2_headered.ips
    (일본판 원본을 rom/smrpg_jp.sfc로 둔 경우)

make.sh가 하는 일
 - tools/build.py: 이름 테이블, 동적 글리프, 대사 폰트 재활용 글자, 레벨업/필살기 화면 문자열 생성 (build/)
 - tools/py/dlg_rewrite.py: 대사와 각종 텍스트를 다시 채운 build/dialogue.asm 생성
 - rom/smrpg_kr_v1.sfc를 build/test.sfc로 복사한 뒤 asar --fix-checksum=on src/main.asm 적용
 - tools/py/check_menu_names.py: 모든 이름을 메뉴가 그리는 글자로 대조 (틀리면 빌드 실패)

참고
 - tools/py/patchnote_compose.py는 macOS 시스템 폰트 경로를 씁니다. 다른 환경에서는 FONT 값을 바꿔 주세요.
 - 테스트 스크립트(tools/run_seq.sh 등)는 tools/Mesen.app (Mesen 2)과
   test/states/*.mss 세이브스테이트를 전제로 합니다. 세이브스테이트는 포함하지 않았습니다.
 - compat/run_all.sh는 compat/cores/에 libretro 코어를, compat/roms/에 jp.sfc, v11.sfc, v111.sfc와
   save_cookie.srm을 두고 실행합니다. (ANALYSIS.txt 8장 "에뮬레이터")
 - tools/fonts/galmuri/ 의 Galmuri 폰트는 SIL Open Font License 1.1입니다. (LICENSE.txt)
