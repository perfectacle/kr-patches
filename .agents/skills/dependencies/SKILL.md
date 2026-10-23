---
name: dependencies
description: 툴킷 고정 버전·Pillow 등 Python 의존성·Python·uv·GitHub Actions 버전을 바꿀 때, 또는 Renovate PR 을 처리할 때. 7일 쿨다운, uv.lock, rebuild-needed PR.
---

# 의존성

이 스킬이 DEP-01, DEP-02 의 정본이다. Python 환경은 `pyproject.toml`(툴킷을 릴리스 태그로 고정) + `uv.lock`(간접 의존성 Pillow 까지 고정)이고, `uv sync` 가 빌드 스크립트가 쓰는 최상위 `.venv/` 를 만든다. 업데이트는 Renovate 가 PR 로 올린다(`renovate.json`). GitHub Actions 업데이트만 CI 통과 후 자동 머지되고, 빌드 결과를 바꿀 수 있는 업데이트는 `rebuild-needed` 라벨을 달고 사람이 머지한다.

## 절차 — `rebuild-needed` PR (툴킷 태그, lock 유지보수, Python 버전)

1. **PR 브랜치로 워크트리를 판다** — `git fetch origin <브랜치> && git worktree add ../kr-patches-<짧은-설명> <브랜치>`(원격 브랜치를 따라가는 로컬 브랜치가 생긴다). 정리는 [git-workflow 절차 6](../git-workflow/SKILL.md#절차) 과 같다.
   완료: 워크트리가 PR 의 HEAD 다.
2. **lock 을 맞춘다** — 툴킷 태그 PR 은 Renovate 가 `pyproject.toml` 의 태그만 바꾸고 `uv.lock` 은 그대로라 CI 의 `uv sync --locked` 가 실패한다. `uv lock` 으로 lock 을 다시 만들어 같은 PR 에 커밋한다. 툴킷 CHANGELOG 의 해당 버전 절에서 출력이 바뀐다는 항목이 있는지 먼저 읽는다.
   완료: `uv sync --locked` 통과.
3. **게임마다 다시 빌드해 비교한다** — [BUILD-01](../game-patch/SKILL.md#build-01--배포한-패치와-같은-빌드). README 의 결과물 CRC32 와 배포한 IPS 와 같아야 한다.
   완료: 모든 게임이 같다. 다른 게임이 있으면 머지하지 않고 원인(툴킷 변경, Pillow 렌더링)을 PR 에 적는다.
4. **PR 에 결과를 적고 머지한다** — 게임별 CRC32 를 적고 `gh pr merge --merge`.
   완료: PR 이 `MERGED`.

## 규칙

### DEP-01 — 7일 쿨다운

릴리스된 지 7일이 지난 버전만 쓴다. uv(`[tool.uv] exclude-newer = "7 days"`)와 Renovate(`minimumReleaseAge: 7 days`) 양쪽에 걸려 있다.

- 이유: 공급망 공격은 대개 배포 직후 며칠 안에 발견·회수된다.
- 예외 1: 자체 툴킷(kr-patch-toolkit) 태그는 쿨다운이 없다(같은 주인이 릴리스한다). git 의존성이라 uv 의 `exclude-newer` 도 적용되지 않는다.
- 예외 2: 보안 수정. Renovate 는 취약점 PR 에 쿨다운을 적용하지 않는다(`vulnerabilityAlerts`). uv 쪽은 `[tool.uv] exclude-newer-package` 에 그 패키지만 넣어야 lock 에 들어간다. 근거(advisory 링크)를 PR 에 적고, 쿨다운이 지나면 그 항목을 지운다. 보안 수정이라도 Pillow 처럼 빌드 결과를 바꿀 수 있으면 위 절차 3 을 거친다.
- GitHub Actions 도 같은 기준이다. 액션은 커밋 SHA 로 고정하고 `# vX.Y.Z` 주석을 단다. actionlint 이미지는 digest 로, zizmor 는 잡 env 의 `ZIZMOR`, uv 는 `setup-uv` 의 `version` 한 곳에 둔다. Renovate 가 모두 올린다.

### DEP-02 — lockfile

`pyproject.toml` 을 바꾸면 `uv.lock` 도 같이 바뀌어야 하고 `uv sync --locked` 가 통과해야 한다.

- 충돌이 나면 main 의 lock 을 가져와(`git checkout origin/main -- uv.lock`) `uv lock` 으로 다시 만든다. 손으로 고치지 않는다.
- 새 의존성은 `uv add <pkg>`. 게임 하나만 쓰는 패키지라도 환경이 하나라 여기에 넣는다.

## 참고

- **툴킷 태그를 Renovate 가 읽는 방법**: pep621 매니저는 git 의존성을 건너뛰어서, `renovate.json` 의 regex customManager 가 `pyproject.toml` 의 `kr-patch-toolkit @ git+…@vX.Y.Z` 줄을 github-tags 로 올린다. 그래서 lock 은 따라 바뀌지 않는다(절차 2).
- **Python 버전**은 `.python-version`(uv 와 CI 가 읽는다)이 정한다. Renovate 가 올리되 자동 머지하지 않는다.
