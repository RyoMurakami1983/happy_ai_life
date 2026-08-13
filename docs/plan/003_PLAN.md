# PLAN 003

## GOAL

`copilot plugin update` が lock / Access denied で失敗したときの safe repair 導線を、`uv run app.py plugin-repair` と関連 docs で追加する。

## Success Criteria

- `plugin-repair` command が追加される。
- backup / delete / reinstall / restore の流れが dry-run 付きで実行できる。
- 非対話時は `--yes` なしで destructive step に進まない。
- README / GETTING_STARTED / TROUBLESHOOTING / PLUGIN_MAINTENANCE が update primary / repair fallback を説明する。
- focused check が通る。

## Out of Scope

- `copilot plugin update` の wrapper 化。
- plugin 配布構造の変更。
- 任意 marketplace / 任意 plugin 対応。
- VS Code / Copilot process 自動停止。

## Progress

- [x] Bootstrap / 前提確認
- [x] Slice 1: `plugin-repair` CLI surface
- [x] Slice 2: safe repair workflow
- [x] Slice 3: docs and review readiness
- [x] Completion handoff

## Structure Decisions

- 実装は `happy_env.py` に集約し、repo-local fallback command とする。
- repair 対象は `happy-ai-life-marketplace` の `happy-core` / `happy-coding` に限定する。
- destructive step の前に backup を必須化し、`--yes` と対話確認で安全性を担保する。
- docs は通常利用者へ正規導線を維持し、repair は fallback として案内する。

## Behavior List

- [ ] `uv run app.py plugin-repair --dry-run --no-interactive` が予定作業を表示する。
- [ ] `uv run app.py plugin-repair --yes --no-interactive` が backup -> delete -> reinstall を実行する。
- [ ] reinstall 失敗時に backup から restore を試みる。
- [ ] `--plugin happy-core` のように subset repair ができる。
- [ ] docs が「いつ update、いつ repair」を明確にする。

## Vertical Slices

### Slice 1: `plugin-repair` CLI surface

- Type: AFK
- Done: parser、help、`--plugin`、`--dry-run`、`--yes`、`--interactive/--no-interactive` の挙動が決まる。
- First test: `plugin-repair` parser / non-interactive safety guard
- RED expectation: command 未対応、または `--yes` なしでも destructive path に進んでしまう。
- GREEN command: `uv run python -m pytest -q tests/test_app_smoke.py`
- Acceptance command: `uv run python -m pytest -q tests/test_app_smoke.py`
- Out of scope: 実際の reinstall ロジックの細部。

### Slice 2: safe repair workflow

- Type: AFK
- Done: backup、delete、install、restore の実行順とエラー時の戻しが実装される。
- First test: install failure で restore が走ること
- RED expectation: restore が行われない、または backup path が出ない。
- GREEN command: `uv run python -m pytest -q tests/test_app_smoke.py`
- Acceptance command: `uv run python -m pytest -q tests/test_app_smoke.py`
- Out of scope: docs 更新。

### Slice 3: docs and review readiness

- Type: HITL
- Done: docs が update primary / repair fallback に整い、focused check と preflight review に渡せる。
- First test: docs / launcher consistency
- RED expectation: README と TROUBLESHOOTING の導線が食い違う。
- GREEN command: `uv run ruff check happy_env.py tests/test_app_smoke.py`
- Acceptance command: `uv run python -m pytest -q tests/test_app_smoke.py && uv run ruff check happy_env.py tests/test_app_smoke.py && uv run ty check .`
- Out of scope: commit / push / PR 作成 / merge。

## Order Rationale

- 先に safety guard を固めると、復旧処理本体の設計ミスで destructive path が広がりにくい。
- workflow 本体を先にテストで固めてから docs を合わせると、説明が実装からずれにくい。
- review-ready は最後にまとめて確認した方が docs と code の整合を見やすい。

## Risks / Unknowns

- repo を clone していない利用者には `app.py` がないため、repair を public primary path にできない。
- Windows の lock 状態によっては delete も失敗しうる。

## Return Conditions

- FAIL: focused test / lint / type check が落ちた場合は同じ plan のまま修正する。
- REPLAN_REQUIRED: repair command を repo-local fallback に留められず、plugin 配布方式や public update path の変更が必要になった場合は `design-and-plan` に戻す。
