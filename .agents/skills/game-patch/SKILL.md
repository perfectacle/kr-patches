---
name: game-patch
description: 게임 패치(어셈블리, 대본·이름 데이터, 코드표, 폰트, 빌드·테스트 스크립트, 롬 분석 노트)를 고치거나 새 게임을 더할 때. 롬 금지, 배포한 패치와 같은 빌드, 출발점 패치, 툴킷과의 경계, 영/한 문서.
---

# 게임 패치

이 스킬이 ROM-01, BUILD-01, BASE-01, GAME-01, DOC-01, LIC-01 의 정본이다.

## 구조

게임은 기종 폴더 아래 `<기종>/<게임 slug>/` 에 둔다(슈퍼 패미콤 `sfc/`, 닌텐도 DS `nds/`). 게임 폴더에 흔히 있는 것:

| 경로                          | 내용                                                       |
| ----------------------------- | ---------------------------------------------------------- |
| `README.md` / `README.ko.md`  | 원본 롬(헤더 제목·CRC32·SHA-1), 빌드 명령과 결과물 CRC32, 테스트 |
| `docs/ANALYSIS(.ko).md`       | 롬 분석 노트(롬 배치, 메모리, 형식, 훅, 빈 공간)           |
| `tools/`                      | 빌드 스크립트(`build.sh` 등)와 게임 전용 Python 도구       |
| `tables/`, `data/`            | 대본·이름 표, 문자 코드표                                  |
| `asm/`, `src/`                | 어셈블리(asar)                                             |
| `lua/`, `compat/`, `test/`    | Mesen 2 스크립트, 여러 에뮬레이터 코어 호환 테스트         |
| `v1.0/*.ips`, `v1.1/*.xdelta` 등 | 빌드의 출발점인 이전 버전 패치([BASE-01](#base-01--출발점-패치는-불변)) |

빌드 스크립트는 저장소 최상위 `.venv/bin/python`·`.venv/bin/krpatch` 를 쓴다(`PYTHON`·`KRPATCH` 로 바꿀 수 있다). 원본 롬은 각 README 가 정한 이름으로 게임 폴더에 둔다. 일부 빌드는 macOS 시스템 글꼴, asar 1.91, `xdelta3` 가 필요하다.

## 절차 — 패치를 고칠 때

1. **원본 롬을 확인한다** — README 의 CRC32·SHA-1 과 맞는 롬이 게임 폴더에 있는지 본다. 없으면 빌드 비교를 할 수 없으니 사용자에게 알리고, 롬 없이 되는 검사만 돌린 채 그 사실을 PR 에 적는다.
   완료: 롬이 있다, 또는 없다는 것을 사용자에게 알렸다.
2. **고치기 전에 지금 빌드가 README 의 결과물 CRC32 와 같은지 본다** — README 의 빌드 명령을 그대로 돌린다.
   완료: CRC32 가 README 값과 같다. 다르면 고치기 전에 원인(환경, 툴킷 버전)부터 찾는다.
3. **고친다** — 한 게임 전용인지 여러 게임이 쓸 것인지 먼저 가른다([GAME-01](#game-01--게임-폴더와-툴킷의-경계)).
   완료: 변경이 게임 폴더 안에만 있다(또는 툴킷 PR 을 따로 냈다).
4. **다시 빌드하고 에뮬레이터에서 확인한다** — 바뀐 화면은 README 의 테스트 절차(Mesen 2 Lua 스크립트, `compat/`, NDS 는 desmume libretro 코어와 `tools/play.py`)로 본다. 의도한 변경이면 새 버전 번호를 정하고 README(영/한)의 결과물 CRC32 와 패치 버전을 고친다.
   완료: 의도하지 않은 화면 변화가 없다.
5. **롬 없이 되는 검사를 돌린다** — CI 와 같다:
   ```sh
   uv sync --locked
   git ls-files -z '*.lua' | xargs -0 -n1 luac -p
   git ls-files -z '*.sh' | xargs -0 -n1 zsh -n
   .venv/bin/python -m compileall -q sfc nds
   ```
   완료: 전부 통과.
6. **PR 로 올린다** — [git-workflow](../git-workflow/SKILL.md). 본문에 빌드 비교 결과(CRC32, 또는 롬이 없어 못 했다는 것)를 적는다. 새 버전을 배포하면 패치 파일과 패치 페이지는 블로그 저장소에서 따로 고친다.
   완료: `ci-ok` 초록.

## 규칙

### ROM-01 — 롬 데이터 금지

롬(`*.sfc`·`*.smc`·`*.nds`), 세이브 RAM(`*.srm`·`*.sav`·`*.dsv`), 세이브 스테이트(`*.mss`·`*.state`)와 롬에서 그대로 뽑은 덤프를 커밋하지 않는다. 사용자의 롬에서 빌드 때 만드는 파일(예: `sfc/otogirisou/tables/script-jp.txt`)은 `.gitignore` 에 넣는다. CI 의 `No ROM data in the repository` 단계가 확장자로 검사한다.

- 이유: 저작물이고, 저장소가 공개다.

### BUILD-01 — 배포한 패치와 같은 빌드

같은 원본 롬과 같은 소스에서 빌드하면 배포한 패치와 바이트 단위로 같은 롬·패치(IPS·xdelta)가 나와야 한다. 각 README 의 결과물 CRC32 가 그 기준이다. 빌드 결과를 바꿀 수 있는 변경은 게임마다 다시 빌드해 CRC32 와 패치를 비교한 뒤에만 머지한다. xdelta 는 `xdelta3` 버전에 따라 바이트가 달라질 수 있어 롬 CRC32 가 기준이다.

- 결과를 바꿀 수 있는 변경: 툴킷 고정 버전, `uv.lock` 의 Pillow(폰트·타이틀 렌더링), `.python-version`, 빌드 스크립트·도구, macOS 시스템 글꼴, asar 버전. xdelta 패치는 `xdelta3` 버전도.
- 이유: CI 에는 롬이 없어 이것을 검사할 수 없다. 그래서 Renovate 도 이런 업데이트는 자동 머지하지 않고 `rebuild-needed` 라벨을 단다([dependencies](../dependencies/SKILL.md)).
- 의도한 변경(새 패치 버전)이면 README 의 CRC32 를 새 값으로 바꾸는 것이 곧 기준을 옮기는 것이다.

### BASE-01 — 출발점 패치는 불변

빌드의 출발점인 이전 버전 패치(`sfc/super-mario-rpg/v1.0/*.ips`, `sfc/otogirisou/Otogirisou(K).ips`, `sfc/dragon-ball-z-super-gokuden-totsugeki/v1.0/v1.0.ips`, `sfc/dragon-ball-z-super-gokuden-kakusei/v1.1/v1.1.ips`, `nds/ghost-trick/v1.1/v1.1.xdelta`)는 바꾸지 않는다. `.gitignore` 가 `*.ips`·`*.xdelta` 를 막고 이 파일들만 예외로 둔다.

- 이유: 이미 배포된 패치라 바꾸면 그 위의 모든 빌드가 달라진다. 고칠 것은 그 위의 단계(스크립트)에서 고친다.

### GAME-01 — 게임 폴더와 툴킷의 경계

한 게임에만 해당하는 것(대본 형식, 포인터 테이블, RAM 주소, 코드표)은 그 게임 폴더에 둔다. 둘 이상의 게임이 같은 것을 다시 짜고 있으면 kr-patch-toolkit 으로 옮기고, 이 저장소는 새 툴킷 릴리스를 고정해서 쓴다.

- 이유: 게임 폴더끼리 서로 import 하면 한 게임의 변경이 다른 게임의 빌드를 움직인다. 툴킷은 태그로 고정되니 그런 일이 없다.
- 게임 스크립트가 쓰는 `kr_patch` 의 이름이 고정 버전에 있는지는 CI 의 `Check kr_patch imports` 가 본다.

### DOC-01 — 영어판과 한국어판

문서는 영어판 `X.md` 와 한국어판 `X.ko.md` 가 짝이고, 맨 위에 언어 전환 링크가 있다. 한쪽을 고치면 다른 쪽도 같은 내용으로 고친다. 에이전트 문서(`AGENTS.md`, `CLAUDE.md`, `.agents/`)만 한국어 한 벌이다.

- 이유: 한쪽만 고치면 다른 쪽이 조용히 틀린 문서가 된다. 짝이 있는지는 CI 가 보지만 내용이 같은지는 사람이 본다.

### LIC-01 — 코드와 번역 데이터

코드(어셈블리, Python, 셸, Lua, 빌드·테스트 스크립트)는 MIT, 번역 데이터(한글 대본, 이름 표, 코드표, 글리프, 그래픽, 출발점 패치)는 MIT 가 아니다. 서드파티 글꼴은 그 라이선스 파일을 사본 옆에 둔다(Galmuri 는 `LICENSE.txt`). 새 종류의 파일을 더하면 최상위 README(영/한)의 라이선스 절에서 어느 쪽인지 밝힌다.

- 이유: 팬 번역 데이터는 비상업 배포 조건이 따로 있어서, 코드와 섞여 MIT 로 읽히면 안 된다.
