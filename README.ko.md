# kr-patches

[English](README.md) | 한국어

perfectacle 의 한글 패치 소스입니다. 게임 폴더마다 그 게임에만 해당하는 것
(어셈블리, 대본·이름 데이터, 코드표, 빌드 스크립트, 에뮬레이터 테스트
스크립트)과 롬 분석 노트가 있습니다. 공통 도구는
[kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit)
(`krpatch` 명령, `kr_patch` 패키지)에서 가져옵니다.

롬 데이터는 들어 있지 않습니다. 모든 빌드는 직접 덤프한 일본판 카트리지
롬에서 시작하며, 필요한 롬은 각 게임 README 에 헤더 제목, CRC32, SHA-1 로
적어 두었습니다.

| 게임 | 패치 | 원본 롬(헤더 제목, CRC32) |
| --- | --- | --- |
| [슈퍼 마리오 RPG](snes/super-mario-rpg/README.ko.md) | v1.2 | `SUPER MARIO RPG`, `5527071E` |
| [제절초](snes/otogirisou/README.ko.md) | v1.2 | `OTOGIRISOU`, `8E4BEFD0` |
| [드래곤볼 Z 초오공전: 돌격편](snes/dragon-ball-z-super-gokuden-totsugeki/README.ko.md) | v1.2 | `SFX DBZ TOTSUGEKIHEN`, `D531289B` |
| [드래곤볼 Z 초오공전: 각성편](snes/dragon-ball-z-super-gokuden-kakusei/README.ko.md) | v1.3 | `ｽｰﾊﾟｰｺﾞｸｳﾃﾞﾝ ｶｸｾｲﾍﾝ`, `3172CD4F` |

게임은 기종별 폴더(`snes/`)로 나눕니다. 다른 기종은 폴더를 따로 둡니다.
패치 페이지와 내려받기: <https://perfectacle.github.io/games/kr-patches/>.

## 준비

Python 3.15(`.python-version`)와 `requirements.txt` 에 고정한 툴킷이 필요합니다.

```sh
uv venv -p 3.15.0 .venv
uv pip install -p .venv -r requirements.txt
```

게임 빌드 스크립트는 저장소 최상위의 `.venv/bin/python` 과 `.venv/bin/krpatch`
를 씁니다. 다른 환경을 쓰려면 `PYTHON` 과 `KRPATCH` 를 지정하세요. 일부 빌드는
[asar](https://github.com/RPGHacker/asar) 1.91, zsh, macOS 시스템 글꼴도
필요합니다. 자세한 것은 각 게임 README 를 보세요.

툴킷은 릴리스 태그로 고정해, 모든 빌드가 배포한 패치와 바이트 단위로 같게
유지합니다. 고정 버전을 옮길 때는 커밋하기 전에 게임마다 다시 빌드해 IPS 를
배포한 것과 비교하세요.

## 검사

`.github/workflows/ci.yml` 은 롬 없이 되는 것만 돌립니다: Lua·셸 문법, Python
컴파일, 게임 스크립트가 쓰는 `kr_patch` import, 돌격편 대사 배치 검사. 빌드와
IPS 비교는 원본 롬이 있어야 하므로 로컬에서 돌립니다.

## 라이선스

코드(어셈블리, Python, 셸, Lua 소스와 빌드·테스트 스크립트)는 MIT 라이선스를
따릅니다. [LICENSE](LICENSE) 를 보세요.

번역 데이터는 코드와 별개이며 MIT 라이선스 대상이 아닙니다: 한글 대본, 대사와
이름 표, 문자 코드표, 글리프, 그래픽, 빌드의 출발점인 이전 버전 패치. 저작권이
있는 게임의 팬 번역 데이터로, 직접 가진 카트리지와 함께 쓰도록 비상업으로
배포합니다. 판매하거나 롬 이미지와 함께 배포하지 마세요.

`snes/*/tools/fonts/` 의 Galmuri 글꼴은 SIL Open Font License 1.1 을 따릅니다
(각 사본 옆의 `LICENSE.txt`).
