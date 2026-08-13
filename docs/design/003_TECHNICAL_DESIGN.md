# Technical Design 003: Safe plugin repair fallback

## Goal

`happy_ai_life` の plugin 更新で `copilot plugin update` が Windows の lock / Access denied で失敗したとき、正規導線を崩さずに安全に復旧できる repo-local command と docs を追加する。

## Success Criteria

- `uv run app.py plugin-repair --dry-run --no-interactive` で、対象 plugin、backup 先、実行予定の reinstall が確認できる。
- `uv run app.py plugin-repair --yes --no-interactive` で、対象 plugin の backup -> delete -> reinstall を安全に実行できる。
- 非対話実行で `--yes` なしの場合は、削除前に安全に停止する。
- reinstall が失敗した場合、backup から元の plugin directory を復元し、利用者に restore 状況を伝える。
- README / GETTING_STARTED / TROUBLESHOOTING / PLUGIN_MAINTENANCE が、**通常は update、失敗時は repair** の導線に整う。
- focused test が通る。

## Out of Scope

- `copilot plugin update` のラップや置き換え。
- marketplace plugin payload 自体へ repair script を同梱して配布すること。
- `happy-ai-life-marketplace` 以外の plugin 管理。
- VS Code / Copilot process の自動停止。

## Context / Source of Truth

- `docs/grill_results/003_GRILL_WITH_DOCS_RESULT.md`
- `README.md`
- `docs/GETTING_STARTED.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PLUGIN_MAINTENANCE.md`
- `happy_env.py`
- `tests/test_app_smoke.py`
- `CONTEXT.md`

## Structure Decisions

- 正規導線は `copilot plugin update` のまま維持し、repo-local fallback として `uv run app.py plugin-repair` を追加する。
- repair 対象は `happy-ai-life-marketplace` 配下の `happy-core` / `happy-coding` に限定し、必要なら `--plugin` で subset を選べるようにする。
- destructive な削除前に backup を必須化し、対話端末では確認プロンプト、非対話では `--yes` を必須にする。
- reinstall 失敗時は、削除済み plugin を backup から restore して partial failure を残しにくくする。
- docs は Path 1 の通常利用では update を維持し、repair は troubleshooting / local development の fallback として案内する。

## Public Interfaces / Test Surface

- `uv run app.py plugin-repair --dry-run --no-interactive`
- `uv run app.py plugin-repair --yes --no-interactive`
- `uv run app.py plugin-repair --plugin happy-core --yes --no-interactive`
- `happy_env.py`
- `tests/test_app_smoke.py`
- `README.md`
- `docs/GETTING_STARTED.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PLUGIN_MAINTENANCE.md`

## Data Flow

```text
user sees update failure
  -> read README / TROUBLESHOOTING
  -> run uv run app.py plugin-repair --dry-run
  -> confirm target + backup path
  -> run uv run app.py plugin-repair --yes
  -> backup current plugin dirs
  -> delete target dirs
  -> copilot plugin install <plugin>@happy-ai-life-marketplace
  -> success summary or restore from backup on failure
```

## Security Boundary

- repair command は `$HOME\.copilot\installed-plugins\happy-ai-life-marketplace\` 配下だけを触る。
- 削除対象は known plugin 名だけに制限し、自由入力パスは受けない。
- destructive step の前に backup を作り、非対話では `--yes` を要求する。
- install command の失敗を握りつぶさず、restore の成否もそのまま出す。

## Behavior List

- 正規導線は README 上で `copilot plugin update` を維持する。
- `plugin-repair` は dry-run で backup path と対象 plugin を表示する。
- `plugin-repair` は `--plugin` 未指定時に `happy-core` と `happy-coding` の両方を扱う。
- `plugin-repair` は backup 後に対象 plugin directory を削除し、`copilot plugin install` を実行する。
- install 失敗時は backup から restore を試み、restore 結果を明示する。
- docs は「通常更新」と「失敗時の safe repair」の役割分担を説明する。

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|
| Slice 1: CLI entrypoint and safety guard | AFK | `plugin-repair` parser と `--yes` / `--dry-run` / plugin 選択が追加される | app parser / behavior test | command 未対応、または非対話 safety guard がない | `uv run python -m pytest -q tests/test_app_smoke.py` |
| Slice 2: repair workflow | AFK | backup / delete / reinstall / restore のロジックが追加される | workflow unit test | backup なし削除、restore 欠如、subset 不備 | `uv run python -m pytest -q tests/test_app_smoke.py` |
| Slice 3: docs and handoff | HITL | docs が update primary + repair fallback に揃う | docs assertion + launcher smoke | README と troubleshooting の責務が曖昧 | `uv run python -m pytest -q tests/test_app_smoke.py` |

## Risks / Unknowns

- repo を clone していない marketplace 利用者は `app.py` を直接使えない。対策として、README では update を primary に保ち、repair は troubleshooting と repo 改善者向け docs へ寄せる。
- Windows の lock 形態によっては delete も失敗しうる。対策として、失敗箇所を明示し、削除前 backup を維持する。

## ADR

- 不要。正規導線の変更や plugin 配布構造の変更ではなく、repo-local fallback の追加に留まる。

## Implementation Handoff

### Goal

`copilot plugin update` が Windows で失敗した場合に備え、backup と restore を伴う `uv run app.py plugin-repair` と、その導線 docs を追加する。

### Success Criteria

- `plugin-repair` の dry-run と実行モードがある。
- 非対話時は `--yes` が必須。
- reinstall 失敗時は restore を試みる。
- docs は update primary / repair fallback を一貫して説明する。
- focused test が通る。

### Out of Scope

- `copilot plugin update` の置換。
- plugin payload 配布方式の変更。
- 任意 marketplace / 任意 plugin の汎用管理ツール化。

### Structure Decisions

- 実装場所: `happy_env.py`
- テスト場所: `tests/test_app_smoke.py`
- docs: `README.md`, `docs/GETTING_STARTED.md`, `docs/TROUBLESHOOTING.md`, `docs/PLUGIN_MAINTENANCE.md`

### Behavior List

- `plugin-repair` は両 plugin を既定対象にする。
- `plugin-repair` は backup path を表示する。
- reinstall 失敗時は restore を試みる。
- docs は fallback の使いどころを限定して説明する。

### Vertical Slices

1. `plugin-repair` の CLI surface と safety guard を追加する。
2. backup / delete / reinstall / restore の実行ロジックを追加する。
3. docs と focused tests を更新し、review-ready にする。

### Artifacts

artifacts:
  - docs/grill_results/003_GRILL_WITH_DOCS_RESULT.md
  - docs/design/003_TECHNICAL_DESIGN.md
  - docs/plan/003_PLAN.md

### Commands

```powershell
uv run python -m pytest -q tests/test_app_smoke.py
uv run ruff check happy_env.py tests/test_app_smoke.py
uv run ty check .
```

### Return Conditions

- FAIL: parser / workflow / docs のいずれかが focused check で落ちた場合は同じ plan で修正する。
- REPLAN_REQUIRED: `plugin-repair` が repo-local fallback では足りず、配布方式や public update path 自体を変える必要が出た場合は `design-and-plan` に戻す。
