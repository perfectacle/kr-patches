# 에이전트 진입 문서

이 저장소는 perfectacle 의 한글 패치 소스다. 게임 폴더(`<기종>/<게임>/`, 예: `snes/otogirisou/`, `nds/ghost-trick/`)마다 그 게임에만 해당하는 어셈블리·대본·코드표·빌드 스크립트·에뮬레이터 테스트와 롬 분석 노트가 있고, 공통 도구는 릴리스 태그로 고정한 [kr-patch-toolkit](https://github.com/perfectacle/kr-patch-toolkit) 에서 가져온다. 모든 빌드는 직접 덤프한 일본판 롬에서 시작해 **배포한 패치와 바이트 단위로 같은 결과**를 내야 하고, 롬이 없는 CI 는 이것을 검사하지 못한다. 그래서 빌드 결과를 바꿀 수 있는 변경은 로컬에서 다시 빌드해 비교하는 것이 가장 중요한 제약이다. 이 문서는 모든 코딩 에이전트(Claude Code, Codex, Cursor 등)가 처음 읽는 곳이다. 규칙의 정본은 `.agents/` 에 한 벌만 있고, 여기에는 요약과 "무엇을 하려면 어디를 읽나" 만 있다.

도구별 경로는 정본을 가리킨다: `CLAUDE.md` 는 이 파일을 import 하고, `.claude/skills` 는 `.agents/skills` 의 심볼릭 링크다. 스킬을 고칠 때는 `.agents/skills/` 실경로를 쓴다 — 심볼릭 링크 너머 경로는 `git add` 가 거부한다.

## 절대 규칙

어떤 도구를 쓰든 지킨다. 각 줄의 링크가 정본이다.

- **롬·세이브·세이브 스테이트를 커밋하지 않는다** — CI 가 막는다. [ROM-01](.agents/skills/game-patch/SKILL.md#rom-01--롬-데이터-금지)
- **빌드 결과가 바뀔 수 있는 변경(툴킷·Pillow·Python 버전, 빌드 도구)은 게임마다 다시 빌드해 README 의 CRC32·배포한 패치(IPS·xdelta)와 비교한다** — [BUILD-01](.agents/skills/game-patch/SKILL.md#build-01--배포한-패치와-같은-빌드)
- **빌드의 출발점인 이전 버전 패치를 바꾸지 않는다** — [BASE-01](.agents/skills/game-patch/SKILL.md#base-01--출발점-패치는-불변)
- **여러 게임이 쓸 도구는 툴킷에, 한 게임 전용은 게임 폴더에** — [GAME-01](.agents/skills/game-patch/SKILL.md#game-01--게임-폴더와-툴킷의-경계)
- **문서는 영어판과 한국어판을 함께 고친다** — CI 가 짝을 검사한다. [DOC-01](.agents/skills/game-patch/SKILL.md#doc-01--영어판과-한국어판)
- **릴리스된 지 7일 안 된 의존성을 들이지 않는다** — 보안 수정과 자체 툴킷만 예외. [DEP-01](.agents/skills/dependencies/SKILL.md#dep-01--7일-쿨다운)
- **작업마다 최신 `origin/main` 에서 워크트리를 파고, 머지가 끝나면 지운다** — [GIT-02](.agents/skills/git-workflow/SKILL.md#git-02--작업마다-워크트리)
- **모든 변경은 브랜치 → PR, `ci-ok` 를 통과시킨다** — [GIT-01](.agents/skills/git-workflow/SKILL.md#git-01--브랜치와-pr), [CI-01](.agents/skills/ci/SKILL.md#ci-01--ci-ok-와-자동-머지)
- **검사가 실패하면 기준을 낮추지 말고 원인을 고친다** — [CI-02](.agents/skills/ci/SKILL.md#ci-02--실패는-원인을-고친다)

전체 목록: [불변식 카탈로그](.agents/invariants/INVARIANTS.md)

## 무엇을 하려면 어디를 읽나

| 하려는 일                                                         | 읽을 정본                                            |
| ----------------------------------------------------------------- | ---------------------------------------------------- |
| 게임 패치(어셈블리·대본·코드표·빌드·테스트 스크립트)를 고치거나 새 게임을 더한다 | [game-patch](.agents/skills/game-patch/SKILL.md)     |
| 툴킷 고정 버전·Python·uv·Actions 버전을 바꾸거나 Renovate PR 을 처리한다 | [dependencies](.agents/skills/dependencies/SKILL.md) |
| 워크플로를 바꾸거나 CI 실패를 고친다                              | [ci](.agents/skills/ci/SKILL.md)                     |
| 워크트리·브랜치·커밋·PR 을 만들거나 정리한다                      | [git-workflow](.agents/skills/git-workflow/SKILL.md) |
| 한국어 문서(README.ko, ANALYSIS.ko)를 쓴다                        | [korean-copy](.agents/skills/korean-copy/SKILL.md)   |

준비는 `README.md` 의 Setup, CI 구성은 `.github/workflows/ci.yml` 에서 바로 확인한다. 패치 페이지와 내려받기 파일은 블로그 저장소(perfectacle.github.io)에 있다.
