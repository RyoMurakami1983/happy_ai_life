# PLAN 009

関連:
- [grill result 009](../grill_results/009_GRILL_WITH_DOCS_RESULT.md)
- [design 009](../design/009_TECHNICAL_DESIGN.md)
- [plan index](README.md)

## GOAL

repo-onboarding の初回導線で、Read-only 観測と bootstrap を止めすぎないように `BootstrapMinimal` profile と severity-aware `repo-secure-check` を導入する。

## Success Criteria

- `BootstrapMinimal` profile が sync-to-repo で使える
- repo-secure-check の `checks` に severity が入る
- repo-onboarding と関連 docs が BootstrapMinimal -> HappyDefault 昇格を説明する
- focused tests が通る

## Out of Scope

- `allowObserve` schema 導入
- maintenance mode 変更
- `evals/repo-onboarding/` の追加

## Progress

- [x] Bootstrap / 前提確認
- [x] Slice 1: Policy profile distribution
- [x] Slice 2: Severity-aware secure check
- [x] Slice 3: Onboarding skill and docs sync
- [x] Slice 4: Eval + deep review
- [x] Completion handoff

## Structure Decisions

- Bootstrap 用 policy は `sync-to-repo` 実行時に `policy/guard-policy.json` を軽量版へ rewrite して表現する（ただし safety-hook / guard-policy 自体の保護は残す）
- `sync-to-home` は bootstrap policy も home に同期する
- `sync-to-repo` は PolicyProfile に応じて target repo の `policy/guard-policy.json` を切り替える
- `repo-secure-check` は blocking / advisory を返し、strict 判定は既存互換を保ちながら JSON でも severity を持つ

## Behavior List

- [x] BootstrapMinimal で同期された repo の policy は軽量版へ rewrite される
- [x] HappyDefault で同期された repo の policy は通常版になる
- [x] `repo-secure-check --AsJson` が severity を返す
- [x] `repo-onboarding` が bootstrap 完了条件を blocking ベースで説明する

## Vertical Slices

### Slice 1: Policy profile distribution

- Type: AFK
- Done: home sync / repo sync が bootstrap policy を扱える
- First test: `uv run python -m pytest -q tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py`
- RED expectation: BootstrapMinimal profile か bootstrap policy rewrite が見つからない
- GREEN command: `uv run python -m pytest -q tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py`
- Acceptance command: `uv run python -m pytest -q tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py`
- Out of scope: full guard redesign

### Slice 2: Severity-aware secure check

- Type: AFK
- Done: repo-secure-check JSON / text に severity が出る
- First test: `uv run python -m pytest -q tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py`
- RED expectation: checks に severity key がない
- GREEN command: `uv run python -m pytest -q tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py`
- Acceptance command: `uv run python -m pytest -q tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py`
- Out of scope: severity に応じた自動 remediation

### Slice 3: Onboarding skill and docs sync

- Type: AFK
- Done: repo-onboarding と docs が BootstrapMinimal -> HappyDefault を説明する
- First test: `uv run python -m pytest -q tests\test_app_smoke.py`
- RED expectation: old all-checks OK wording が残る
- GREEN command: `uv run python -m pytest -q tests\test_app_smoke.py`
- Acceptance command: `uv run python -m pytest -q tests\test_app_smoke.py`
- Out of scope: new downstream skill family

### Slice 4: Eval + deep review

- Type: AFK
- Done: focused validation、implementation eval、再 review が完了する
- First test: focused commands
- RED expectation: profile or severity inconsistencies
- GREEN command: `uv run python -m pytest -q tests\test_app_smoke.py tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py`
- Acceptance command: `uv run python -m pytest -q tests\test_app_smoke.py tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py && uv run ruff check . && uv run ty check .`
- Out of scope: PR

## Order Rationale

- 先に profile distribution を固めると、repo-secure-check と docs の説明先が一意になる
- その後に severity を載せ、最後に onboarding skill / docs を同期する

## Risks / Unknowns

- BootstrapMinimal を常用 profile と誤解される可能性
- severity を strict exit code にどう反映するかは現時点では保守互換を優先する

## Return Conditions

- FAIL: wording / profile / severity mismatch があるが plan のまま直せる
- REPLAN_REQUIRED: BootstrapMinimal の導入で home / repo layering 自体を再設計する必要が出る

## Completion Handoff

- Completed slices:
  - Slice 1: Policy profile distribution
  - Slice 2: Severity-aware secure check
  - Slice 3: Onboarding skill and docs sync
  - Slice 4: Eval + deep review
- Commands:
  - `uv run python -m pytest -q tests\test_secret_guard_minimal.py tests\test_repo_secure_check_smoke.py tests\test_wsl2_bootstrap_smoke.py tests\test_repo_onboarding_docs.py tests\test_app_smoke.py`
  - `uv run ruff check .`
  - `uv run ty check .`
  - `uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-coding\skills\repo-onboarding\SKILL.md --level L2`
- Main artifacts:
  - `docs/adr/bootstrap-minimal-onboarding-and-check-severity.md`
  - `docs/design/009_TECHNICAL_DESIGN.md`
  - `docs/plan/009_PLAN_DONE.md`
  - `plugins/happy-coding/skills/repo-onboarding/SKILL.md`
  - `scripts/sync-to-repo.ps1`
  - `scripts/sync-to-repo.sh`
  - `scripts/repo-secure-check.ps1`
  - `scripts/repo-secure-check.sh`
- Remaining out of scope:
  - `allowObserve` schema 導入
  - maintenance mode 変更
  - `evals/repo-onboarding/` の追加
