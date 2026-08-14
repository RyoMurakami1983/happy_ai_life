# PLAN 005

## GOAL

Happy AI Life の skill 構造を、authoring と evaluation の 2 つの薄い入口に整理し、公開 surface を増やさずに責務境界を強化する。

## Success Criteria

- `copilot-authoring` が `new-skill` / `instructions-authoring` / `improve-existing` / `validate-authoring` の 4 route に整理される。
- `new-agent` が公開 route から外れる。
- `privateEval` が評価ケースの設計・保管・昇格判断として定義され、`skill-eval` の reference / 内部ルートとして扱われる。
- `skill-eval`、`empirical-prompt-tuning`、`loop-engineering` の責務が衝突しない。
- targeted tests / validators / manifest checks が通る。

## Out of Scope

- Copilot CLI の slash command 表示制御。
- 新しい top-level `private-eval` skill。
- 新しい custom agent 作成。
- 実 benchmark campaign。

## Progress

- [x] Bootstrap / 前提確認
- [ ] Slice 1: PRD / design / plan
- [ ] Slice 2: Authoring surface
- [ ] Slice 3: Evaluation surface
- [ ] Slice 4: Integration validation
- [ ] Completion handoff

## Structure Decisions

- `copilot-authoring`: authoring の薄い入口。
- `skill-eval`: evaluation の薄い入口。
- `privateEval`: top-level skill ではなく、評価ケース資産の設計・保管・昇格判断。
- `empirical-prompt-tuning`: 独立 skill。
- `loop-engineering`: 全体改善 loop。評価資産の owner ではなく consumer。
- `new-agent`: 標準 authoring route から外す。

## Behavior List

- [ ] `copilot-authoring` に `new-agent` route がない。
- [ ] `new-skill` に agent 作成を標準導線にしない説明がある。
- [ ] `skill-eval` に `privateEval` の位置づけがある。
- [ ] `docs/PRIVATE_EVAL.md` と `CONTEXT.md` の定義が一致する。
- [ ] `loop-engineering` 側で PrivateEval の用語衝突が緩和される。
- [ ] tests が route / terminology の回帰を検出する。

## Vertical Slices

### Slice 1: PRD / design / plan

- Type: HITL
- Done: 005 の PRD、technical design、plan が保存される
- First test: `git --no-pager status --short`
- RED expectation: 005 成果物が未作成
- GREEN command: `git --no-pager status --short`
- Acceptance command: `git --no-pager diff -- docs\grill_results\005_GRILL_WITH_DOCS_RESULT.md docs\design\005_TECHNICAL_DESIGN.md docs\plan\005_PLAN.md`
- Out of scope: skill 本体の変更

### Slice 2: Authoring surface

- Type: AFK
- Done: authoring route から `new-agent` が外れ、docs/tests が 4 route を期待する
- First test: `uv run python -m pytest -q tests\test_copilot_authoring_docs.py`
- RED expectation: test が旧 `new-agent` route を期待して失敗する
- GREEN command: `uv run python -m pytest -q tests\test_copilot_authoring_docs.py`
- Acceptance command: `uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\copilot-authoring\SKILL.md --level L2`
- Out of scope: evaluation 構造の変更

### Slice 3: Evaluation surface

- Type: AFK
- Done: `privateEval` / `skill-eval` / empirical / loop の境界が docs/tests で固定される
- First test: `uv run python -m pytest -q tests\test_skill_eval_docs.py`
- RED expectation: `privateEval` の reference と test が未作成で失敗する
- GREEN command: `uv run python -m pytest -q tests\test_skill_eval_docs.py`
- Acceptance command: `uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\skill-eval\SKILL.md --level L2`
- Out of scope: benchmark 実行

### Slice 4: Integration validation

- Type: AFK
- Done: manifest、skill map、docs tests、ruff が通る
- First test: targeted pytest
- RED expectation: plugin version / skill map / tests の不整合
- GREEN command: `uv run python -m pytest -q tests\test_copilot_authoring_docs.py tests\test_skill_eval_docs.py tests\test_skill_map.py tests\test_plugin_manifest.py`
- Acceptance command: `uv run ruff check tests\test_copilot_authoring_docs.py tests\test_skill_eval_docs.py`
- Out of scope: full quality gate

## Order Rationale

- まず PRD / design / plan を固定し、以降の差分を vertical slice として commit しやすくする。
- Authoring surface を先に整理し、`new-agent` route の除去で public surface を減らす。
- Evaluation surface は用語と reference の同期が必要なため、authoring から分けて実装する。
- 最後に manifest / skill map / validator を通して配布面を確認する。

## Risks / Unknowns

- Copilot CLI で slash command 非表示を明示制御できるかは未確認。今回は top-level skill を増やさないことで対応する。
- `new-agent` 削除による既存利用者影響はあるが、ユーザー方針として標準導線から外す。

## Return Conditions

- FAIL: targeted test / validator の失敗が局所修正で直せる。
- REPLAN_REQUIRED: `privateEval` を top-level skill にしないと必要な UX が成立しない、または `new-agent` 除外が plugin policy と矛盾する。
