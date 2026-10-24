# 불변식 카탈로그

이 저장소가 지키는 규칙의 목록이다. 이 파일에는 규칙의 요지와 **소유자**(규칙 본문이 있는 스킬의 절)만 있다. 본문·이유·예외는 소유자에서 읽는다. 규칙을 바꿀 때는 소유자 한 곳만 고치고, 이 표의 요지가 달라졌으면 이 줄도 고친다.

## 패치 — 배포한 패치를 그대로 다시 만든다

| ID       | 요지                                                                                         | 소유자                                                                           |
| -------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| ROM-01   | 롬·세이브 RAM·세이브 스테이트를 커밋하지 않는다(CI 검사)                                     | [game-patch §ROM-01](../skills/game-patch/SKILL.md#rom-01--롬-데이터-금지)                 |
| BUILD-01 | 빌드는 배포한 패치와 바이트 단위로 같다. 결과가 바뀔 수 있는 변경은 게임마다 다시 빌드해 비교 | [game-patch §BUILD-01](../skills/game-patch/SKILL.md#build-01--배포한-패치와-같은-빌드)    |
| BASE-01  | 빌드의 출발점인 이전 버전 패치(IPS·xdelta)는 바꾸지 않는다                                               | [game-patch §BASE-01](../skills/game-patch/SKILL.md#base-01--출발점-패치는-불변)          |
| GAME-01  | 한 게임 전용은 `<기종>/<게임>/` 에, 여러 게임이 쓸 도구는 툴킷에                               | [game-patch §GAME-01](../skills/game-patch/SKILL.md#game-01--게임-폴더와-툴킷의-경계)     |
| DOC-01   | 문서는 `X.md`(영어)와 `X.ko.md`(한국어)가 짝이고 내용이 같다(CI 가 짝을 검사)               | [game-patch §DOC-01](../skills/game-patch/SKILL.md#doc-01--영어판과-한국어판)             |
| LIC-01   | 코드는 MIT, 번역 데이터는 MIT 가 아니다. 새 종류의 파일은 README 라이선스 절에서 어느 쪽인지 밝힌다 | [game-patch §LIC-01](../skills/game-patch/SKILL.md#lic-01--코드와-번역-데이터)       |
| COPY-01  | 한국어 문서는 합니다체, 번역투 없이, 용어집(게임 이름 포함)을 따른다                         | [korean-copy](../skills/korean-copy/SKILL.md)                                    |

## 의존성·CI·git

| ID     | 요지                                                                   | 소유자                                                                            |
| ------ | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| DEP-01 | 릴리스된 지 7일 지난 버전만 쓴다(보안 수정과 자체 툴킷만 예외)         | [dependencies §DEP-01](../skills/dependencies/SKILL.md#dep-01--7일-쿨다운)        |
| DEP-02 | 의존성을 바꾸면 `uv.lock` 이 같이 바뀌고 `uv sync --locked` 가 통과한다 | [dependencies §DEP-02](../skills/dependencies/SKILL.md#dep-02--lockfile)          |
| CI-01  | main 은 `ci-ok` 통과가 필수, 통과한 PR 은 자동 머지                    | [ci §CI-01](../skills/ci/SKILL.md#ci-01--ci-ok-와-자동-머지)                      |
| CI-02  | 실패하면 기준을 낮추지 말고 원인을 고친다                              | [ci §CI-02](../skills/ci/SKILL.md#ci-02--실패는-원인을-고친다)                    |
| GIT-01 | 모든 변경은 브랜치 → PR, 머지 전 로컬 검증                             | [git-workflow §GIT-01](../skills/git-workflow/SKILL.md#git-01--브랜치와-pr)       |
| GIT-02 | 작업마다 최신 `origin/main` 에서 워크트리를 파고, 머지가 끝나면 지운다 | [git-workflow §GIT-02](../skills/git-workflow/SKILL.md#git-02--작업마다-워크트리) |
