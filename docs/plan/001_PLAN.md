# PLAN 001

## GOAL

`happy-core` に Loop Engineering の入口 skill を追加し、PrivateEval を品質ゲートとして使う最小導線を配布可能にする。

## Success Criteria

- `plugins/happy-core/skills/loop-engineering/SKILL.md` が追加される。
- PrivateEval 5軸が `構造化精度 / 形式知化力 / 完了条件設計力 / 組織視点 / 再利用性` で統一される。
- 既存 `skill-eval`、`empirical-prompt-tuning`、`copilot-authoring` との使い分けが明記される。
- `happy-core` README と plugin metadata が更新される。
- focused check が通る。

## Out of Scope

- `plugins/private-eval-loop/` の追加。
- テンプレート一式の追加。
- 評価自動化 script の追加。
- 新規 ADR の追加。

## Progress

- [x] Bootstrap / 前提確認
- [x] Slice 1: `loop-engineering` skill skeleton
- [x] Slice 2: distribution wiring
- [x] Slice 3: pre-PR readiness
- [x] Completion handoff

## Structure Decisions

- 新規 skill は `plugins/happy-core/skills/loop-engineering/` に置く。
- PrivateEval の詳細は `references/private-eval.md` に分ける。
- `skill-eval` は skill / prompt 評価、PrivateEval は Loop Engineering の作業品質ゲートとして分離する。
- 利用者体験が変わるため `happy-core` の patch version を上げる。

## Behavior List

- [x] Loop Engineering の順序を Observe から Stop or Loop まで示す。
- [x] PrivateEval 5軸で Evaluate する。
- [x] 評価で落ちた軸だけを改善対象にする。
- [x] test / lint / typecheck / build など機械判定を AI 評価より優先する。
- [x] 既存 skill へ委譲する場面を明記する。

## Vertical Slices

### Slice 1: `loop-engineering` skill skeleton

- Type: AFK
- Done: `SKILL.md` と `references/private-eval.md` が追加され、責務と停止条件が読める。
- First test: plugin manifest smoke
- RED expectation: skill 追加前は `loop-engineering` が存在しない。
- GREEN command: `uv run python -m pytest -q tests/test_plugin_manifest.py`
- Acceptance command: `uv run python -m pytest -q tests/test_plugin_manifest.py`
- Out of scope: README / marketplace version 更新。

### Slice 2: distribution wiring

- Type: AFK
- Done: `plugins/happy-core/README.md`、`plugins/happy-core/plugin.json`、`.github/plugin/marketplace.json` が更新される。
- First test: plugin manifest smoke
- RED expectation: version や skill 導線の更新漏れがありうる。
- GREEN command: `uv run python -m pytest -q tests/test_plugin_manifest.py`
- Acceptance command: `uv run python -m pytest -q tests/test_plugin_manifest.py`
- Out of scope: third plugin / template package 追加。

### Slice 3: pre-PR readiness

- Type: HITL
- Done: focused check と事前レビューが完了し、PR ワークフローへ渡せる。
- First test: diff review
- RED expectation: 文書だけでは trigger や後続テンプレート導線が曖昧な可能性。
- GREEN command: `uv run ruff check .`
- Acceptance command: `uv run python -m pytest -q tests/test_plugin_manifest.py; uv run ruff check .`
- Out of scope: commit / push / PR 作成 / merge。merge 後のテンプレート追加は別 PR または次 slice として確認して進める。

## Order Rationale

- skill 本体を先に置くと、README や version 更新が具体物に追従できる。
- 配布導線は利用者体験に関わるため、skill 本体の内容が固まってから更新する。
- テンプレート追加はレビューで skill の責務が確認されてから進める方が、初回 PR の差分とレビュー負荷を抑えられる。

## Risks / Unknowns

- なし。後続テンプレート追加はレビュー後に改めて確認する。

## Return Conditions

- FAIL: focused check が落ちた場合は同じ plan のまま修正する。
- REPLAN_REQUIRED: `loop-engineering` と既存評価 skill の責務分離が崩れた場合は `design-and-plan` に戻す。
