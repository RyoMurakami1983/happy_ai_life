# Technical Design 009: repo-onboarding と guard の BootstrapMinimal 化

## Goal

repo-onboarding の初回導線で、破壊的操作を防ぎつつ通常の観測と bootstrap を止めすぎないように、`BootstrapMinimal` policy profile と severity-aware `repo-secure-check` を導入する。

## Success Criteria

- `sync-to-repo.ps1` / `.sh` が `BootstrapMinimal` profile を受け付ける
- bootstrap profile 用 policy が home sync / repo sync で配布される
- `repo-secure-check.ps1` / `.sh` が `severity` を返す
- `repo-onboarding` が BootstrapMinimal -> HappyDefault の流れを説明する
- focused tests が profile 選択と severity JSON を固定する

## Out of Scope

- `allowObserve` schema の導入
- maintenance mode の仕様変更
- multi-agent onboarding graph の全面設計
- eval ケース本体の追加

## Context / Source of Truth

- `plugins/happy-coding/skills/repo-onboarding/SKILL.md`
- `policy/guard-policy.json`
- `policy/guard-policy.schema.json`
- `.github/hooks/scripts/guard_pre_tool.ps1`
- `scripts/guard_policy.py`
- `scripts/sync_to_home_cli.py`
- `scripts/sync-to-home.ps1`
- `scripts/sync-to-repo.ps1`
- `scripts/sync-to-repo.sh`
- `scripts/repo-secure-check.ps1`
- `scripts/repo-secure-check.sh`
- [grill result 009](../grill_results/009_GRILL_WITH_DOCS_RESULT.md)

## Structure Decisions

### 1. BootstrapMinimal profile

`BootstrapMinimal` は downstream repo の初回導入用 profile とする。  
この profile では、破壊的 deny command rules と safety-hook / guard-policy 自体の保護は維持しつつ、より広い repo-local protected path の `ask` を持たない軽量 policy を `sync-to-repo` 実行時に生成して配布する。

### 2. Profile promotion

初回 bootstrap は `BootstrapMinimal` を使い、その後の steady-state は `HappyDefault` を既定とする。  
`repo-onboarding` はこの二段階モデルを説明し、bootstrap 完了後に HappyDefault へ昇格する導線を示す。

### 3. Severity-aware repo-secure-check

`repo-secure-check` は各 check に `severity` を持つ。

初期案:

| Check | Severity |
| --- | --- |
| repoInstructions | blocking |
| copilotHooks | blocking |
| guardPolicyFiles | blocking |
| gitHooksDirectory | blocking |
| gitHookLineEndings | blocking |
| coreHooksPath | blocking |
| toolDependencies | blocking |
| githubWorkflows | advisory |

### 4. Onboarding completion rule

`repo-onboarding` の Bootstrap mode では、**blocking checks がすべて OK** なら bootstrap 完了扱いとし、advisory は follow-up として残す。

### 5. ADR strategy

この変更は guard layering と onboarding completion rule の hard-to-reverse な判断を含むため、新規 ADR を追加する。

## Public Interfaces / Test Surface

- `plugins/happy-coding/skills/repo-onboarding/SKILL.md`
- `home-template/.copilot/managed-manifest.json`
- `scripts/sync_to_home_cli.py`
- `scripts/sync-to-home.ps1`
- `scripts/sync-to-repo.ps1`
- `scripts/sync-to-repo.sh`
- `scripts/repo-secure-check.ps1`
- `scripts/repo-secure-check.sh`
- `tests/test_repo_secure_check_smoke.py`
- `tests/test_wsl2_bootstrap_smoke.py`
- `tests/test_app_smoke.py`

## Data Flow

```text
home-template policy files
  -> sync-to-home
  -> ~/.copilot/policy/
  -> sync-to-repo -PolicyProfile BootstrapMinimal|HappyDefault
  -> target repo policy/guard-policy.json
  -> repo-secure-check severity report
  -> repo-onboarding summary / next action
```

## Security Boundary

- `maintenance-mode-state` deny は維持する
- destructive deny command rules は BootstrapMinimal でも維持する
- 変更は onboarding friction を減らすためであり、 destructive path の緩和には使わない

## Behavior List

- [ ] BootstrapMinimal で sync すると target repo の `policy/guard-policy.json` は軽量版へ rewrite される
- [ ] HappyDefault で sync すると target repo の `policy/guard-policy.json` は通常版になる
- [ ] `repo-secure-check --AsJson` に `severity` が入る
- [ ] `repo-onboarding` が Read-only / Bootstrap / profile promotion の説明を持つ
- [ ] docs が BootstrapMinimal を正規の初回導入 profile として案内する

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
| --- | --- | --- | --- | --- | --- |
| 1. Policy profile distribution | AFK | BootstrapMinimal policy rewrite が sync-to-repo で扱える | repo secure check / wsl bootstrap smoke | profile 名 or policy rewrite が存在しない | `uv run python -m pytest -q tests/test_repo_secure_check_smoke.py tests/test_wsl2_bootstrap_smoke.py` |
| 2. Severity-aware secure check | AFK | repo-secure-check JSON / text に severity が出る | repo secure check smoke | severity key がない | `uv run python -m pytest -q tests/test_repo_secure_check_smoke.py tests/test_wsl2_bootstrap_smoke.py` |
| 3. Onboarding skill and docs sync | AFK | repo-onboarding と docs が BootstrapMinimal -> HappyDefault を説明する | app smoke + targeted docs read assertions | old all-checks-OK wording が残る | `uv run python -m pytest -q tests/test_app_smoke.py` |
| 4. Eval and review | AFK | focused checks / deep review が通る | full focused commands | profile or severity inconsistency | `uv run python -m pytest -q tests/test_app_smoke.py tests/test_repo_secure_check_smoke.py tests/test_wsl2_bootstrap_smoke.py && uv run ruff check . && uv run ty check .` |

## Risks / Unknowns

- BootstrapMinimal の protected path を軽くしすぎると steady-state へ昇格せずに使い続けられるリスク
- severity の選定が downstream 利用者の期待とズレる可能性

## ADR

- 新規 ADR を追加する: `docs/adr/bootstrap-minimal-onboarding-and-check-severity.md`

## Implementation Handoff

### Goal

repo-onboarding の初回導線を穏やかにするため、BootstrapMinimal profile と severity-aware repo-secure-check を導入する。

### Success Criteria

- BootstrapMinimal profile が sync-to-repo で選べる
- repo-secure-check が severity を返す
- repo-onboarding と docs が新しい導線を説明する
- focused tests が通る

### Out of Scope

- `allowObserve` schema 導入
- maintenance mode 拡張
- eval データ追加

### Artifacts

artifacts:
  - [docs/grill_results/009_GRILL_WITH_DOCS_RESULT.md](../grill_results/009_GRILL_WITH_DOCS_RESULT.md)
  - [docs/design/009_TECHNICAL_DESIGN.md](009_TECHNICAL_DESIGN.md)
  - [docs/plan/009_PLAN_DONE.md](../plan/009_PLAN_DONE.md)

### Commands

```powershell
uv run python -m pytest -q tests/test_app_smoke.py tests/test_repo_secure_check_smoke.py tests/test_wsl2_bootstrap_smoke.py
uv run ruff check .
uv run ty check .
```

### Return Conditions

- FAIL: profile or severity mismatch が局所修正で直る
- REPLAN_REQUIRED: BootstrapMinimal が current guard architecture と両立しない
