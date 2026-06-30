# Technical Design 001: Loop Engineering skill

## Goal

`happy-core` に Loop Engineering の入口を追加し、AI 開発・authoring・PR 対応を「観察、計画、実行、検証、評価、ふりかえり、修正、停止判断」のループとして扱えるようにする。

## Success Criteria

- `plugins/happy-core/skills/loop-engineering/SKILL.md` が追加され、Copilot CLI plugin の skill として検出できる。
- Loop Engineering の基本ループ、停止条件、PrivateEval 5軸が 1 つの skill から辿れる。
- PrivateEval の旧「会社視点」は **組織視点** として定義されている。
- 既存の `skill-eval`、`empirical-prompt-tuning`、`copilot-authoring` と責務が重複せず、使い分けが明記されている。
- `happy-core` の利用者導線と plugin version が、利用者体験の変化に合わせて更新されている。

## Out of Scope

- 新規 `plugins/private-eval-loop/` plugin の追加。
- PR / commit / ADR / loop report テンプレート一式の同時追加。
- 評価を自動実行する CLI / script の実装。
- 既存 `skill-eval` / `empirical-prompt-tuning` の置き換え。

## Context / Source of Truth

- `docs/grill_results/001_GRILL_WITH_DOCS_RESULT.md`
- `README.md`
- `docs/DEVELOPMENT.md`
- `docs/AUTHORING.md`
- `docs/PHILOSOPHY.md`
- `docs/adr/distribution-strategy.md`
- `docs/adr/happy-ai-life-plugin-split-and-skill-slug-simplification.md`
- `plugins/happy-core/README.md`
- `plugins/happy-core/plugin.json`
- `.github/plugin/marketplace.json`
- `plugins/happy-core/skills/skill-eval/SKILL.md`
- `plugins/happy-core/skills/empirical-prompt-tuning/SKILL.md`
- `plugins/happy-core/skills/copilot-authoring/SKILL.md`

## Structure Decisions

- 新規 skill は `plugins/happy-core/skills/loop-engineering/SKILL.md` に置く。
- 評価軸の詳細は同 skill の `references/private-eval.md` に分ける。skill 本体は入口、手順、停止条件、関連 skill への接続に集中する。
- テンプレート群は初回 PR では追加しない。レビュー後または main merge 後に、`loop-engineering` の `references/` または既存 authoring / GitHub skill との接続として別 slice で扱う。
- 新規 ADR は作らない。第三 plugin を作らず `happy-core` に入れる判断は既存 ADR に従う。
- 利用者体験が変わるため `plugins/happy-core/plugin.json` と `.github/plugin/marketplace.json` の `happy-core` version を patch bump する。

## Public Interfaces / Test Surface

- `plugins/happy-core/skills/loop-engineering/SKILL.md`
- `plugins/happy-core/skills/loop-engineering/references/private-eval.md`
- `plugins/happy-core/plugin.json`
- `.github/plugin/marketplace.json`
- `plugins/happy-core/README.md`
- `tests/test_plugin_manifest.py`

## Data Flow

```text
user request / review signal / failed check
  -> loop-engineering
  -> Observe / Plan / Act / Verify
  -> Evaluate with PrivateEval
  -> Reflect
  -> Patch or Stop
  -> route to existing skills when specialized work is needed
```

## Security Boundary

- skill は手順文書のみで、外部 I/O、secret、認証情報、コマンド実行の自動化は追加しない。
- 破壊的操作、secret、権限変更、force push は既存の Copilot CLI / repo guard 方針に従い、Loop Engineering の中でも自動実行しない。
- 評価より先に test / lint / typecheck / build など機械判定を優先する。

## Behavior List

- ユーザーが Loop Engineering を求めたとき、`loop-engineering` skill が入口になる。
- skill は Observe から Stop or Loop までの順序を示す。
- Evaluate では PrivateEval 5軸を使い、`組織視点` を含める。
- 停止条件は、機械判定、Critical 要件、PrivateEval、改善収束を分けて示す。
- 既存 skill へ委譲すべき場面を示し、評価・authoring・実証検査を重複実装しない。

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|
| Slice 1: skill skeleton | AFK | `loop-engineering` skill と PrivateEval reference が追加される | plugin manifest smoke | skill 追加前は存在しない | `uv run python -m pytest -q tests/test_plugin_manifest.py` |
| Slice 2: distribution wiring | AFK | README と version metadata が更新される | manifest / marketplace 目視 + smoke | version 不整合の可能性 | `uv run python -m pytest -q tests/test_plugin_manifest.py` |
| Slice 3: pre-PR review | HITL | diff が意図、リスク、後続テンプレート追加へつながる状態になる | preflight review | 文書だけでは trigger / scope が曖昧な可能性 | `uv run ruff check .` |

## Risks / Unknowns

- テンプレートを初回に入れないため、貼付文書の全体像は後続 PR に残る。対策として skill 内に「後続テンプレート化」の導線を明記する。
- `skill-eval` と PrivateEval の語感が近い。対策として `skill-eval` は prompt / skill 評価、PrivateEval は Loop Engineering の作業品質ゲートと定義する。

## ADR

- 不要。既存の配布 ADR に従う判断であり、新しい戻しにくい構造判断ではない。

## Implementation Handoff

### Goal

`happy-core` に `loop-engineering` skill を追加し、PrivateEval を品質ゲートとして使う最小導線を配布可能にする。

### Success Criteria

- `loop-engineering` skill が追加され、description が trigger と責務を明確に示す。
- PrivateEval 5軸は `構造化精度 / 形式知化力 / 完了条件設計力 / 組織視点 / 再利用性` で統一される。
- `plugins/happy-core/README.md` から新 skill の意図が分かる。
- `plugins/happy-core/plugin.json` と `.github/plugin/marketplace.json` の version が同期する。
- focused check が通る。

### Out of Scope

- 第三 plugin、テンプレート一式、自動評価 script、ADR 追加。

### Structure Decisions

- 追加先: `plugins/happy-core/skills/loop-engineering/`
- 参考資料: `references/private-eval.md`
- 既存 skill への接続: `skill-eval`、`empirical-prompt-tuning`、`copilot-authoring`、必要時に `implement` / `gh-pr-respond`

### Behavior List

- Loop の各段階で何を確認するかが読める。
- 停止条件と戻り条件が読める。
- 低リスク小タスクでは軽量化してよい条件が読める。
- 評価で落ちた軸だけを改善対象にする。

### Vertical Slices

1. `loop-engineering` skill と PrivateEval reference を追加する。
2. `happy-core` README と plugin metadata を更新する。
3. focused check と pre-PR review を行い、PR 化する。

### Commands

```powershell
uv run python -m pytest -q tests/test_plugin_manifest.py
uv run ruff check .
```

### Return Conditions

- FAIL: skill structure や manifest smoke が失敗した場合は同じ plan のまま修正する。
- REPLAN_REQUIRED: `loop-engineering` が `skill-eval` の責務と分離できない、または第三 plugin が必要になる根拠が出た場合は `design-and-plan` に戻す。
