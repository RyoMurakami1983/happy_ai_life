# Technical Design 005: skill 構造の簡素化と評価導線の分離

## Goal

`copilot-authoring` と `skill-eval` を、それぞれ authoring と evaluation の薄い入口として整理し、公開 skill surface を増やさずに責務境界を強化する。

## Success Criteria

- authoring route は `new-skill` / `instructions` / `improve` / `validate` に整理される。
- `new-agent` は公開 route から外れ、agent 作成は標準導線ではないことが明示される。
- `privateEval` は評価ケースの設計・保管・昇格判断として定義され、実行は `skill-eval` の benchmark / empirical へ分かれる。
- `empirical-prompt-tuning` は独立 skill として残る。
- docs / ADR / skill map / tests が新しい境界を説明する。

## Out of Scope

- slash command の非表示機構は新設しない。
- `private-eval` は top-level skill として追加しない。
- `new-agent` の代替 agent 作成 workflow は実装しない。
- full benchmark は実行しない。

## Context / Source of Truth

- `CONTEXT.md`
- `docs/PRIVATE_EVAL.md`
- `docs/AUTHORING.md`
- `docs/SKILL_MAP.md`
- `docs/adr/skill-single-responsibility-and-orchestration.md`
- `plugins/happy-core/skills/copilot-authoring/SKILL.md`
- `plugins/happy-core/skills/skill-eval/SKILL.md`
- `plugins/happy-core/skills/empirical-prompt-tuning/SKILL.md`
- `plugins/happy-coding/skills/loop-engineering/SKILL.md`

## Structure Decisions

### 1. Authoring surface

`copilot-authoring` は薄い親として残す。親は route / handoff だけを持ち、作成・改善・検証の詳細は専門 route に置く。

公開 route は次の 4 つに絞る。

| Route | 責務 |
| --- | --- |
| `new-skill` | 新しい skill の作成と昇格準備 |
| `instructions` | repo-wide / path-specific instructions の作成・整理 |
| `improve` | 既存 skill / instructions / authoring asset の改善 |
| `validate` | 静的・構造確認 |

`new-agent` は標準導線から外す。既存 agent asset や validator は必要に応じて残せるが、新規 agent 作成は例外扱いとし、まず issue / design 判断へ戻す。

### 2. Evaluation surface

`skill-eval` は evaluation の公開入口として残す。`privateEval` は top-level skill ではなく、`skill-eval` の reference / 内部ルートとして扱う。

| Surface | 責務 |
| --- | --- |
| `privateEval` | secret なし評価ケースの設計・保管・昇格判断 |
| `skill-eval` | evaluation 親。benchmark / empirical / privateEval reference へ案内する |
| `benchmark` | baseline / legacy / current の比較実行 |
| `empirical-prompt-tuning` | 指示明瞭性を別実行者で反復改善する独立 skill |
| `loop-engineering` | Verify -> Evaluate -> Reflect -> Patch の改善ループ。評価資産の所有者ではなく利用者 |

### 3. Documentation / validation

構造判断は ADR と AUTHORING docs に残し、regression は targeted docs test で固定する。plugin 配布中の利用者体験が変わるため、`happy-core` version は patch 更新する。

## Public Interfaces / Test Surface

- `plugins/happy-core/skills/copilot-authoring/SKILL.md`
- `plugins/happy-core/skills/skill-eval/SKILL.md`
- `plugins/happy-core/skills/copilot-authoring/sub_skills/new-skill/SKILL.md`
- `docs/SKILL_MAP.md`
- `docs/AUTHORING.md`
- `docs/PRIVATE_EVAL.md`
- `CONTEXT.md`
- `tests/test_copilot_authoring_docs.py`
- 新規または更新する evaluation docs test

## Behavior List

- [ ] authoring 親は `new-agent` を route として提示しない。
- [ ] authoring 親は 4 route だけを提示する。
- [ ] `new-skill` は agent 作成を標準作成 path にしない。
- [ ] `skill-eval` は `privateEval` を設計・保管・昇格判断として説明する。
- [ ] `skill-eval` は benchmark と empirical の違いを説明する。
- [ ] `empirical-prompt-tuning` は独立維持される。
- [ ] `loop-engineering` は evaluation 資産の owner ではなく consumer として説明される。

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|
| 1. PRD / design / plan | HITL | 成果物 005 が揃う | file existence / status | docs が未作成 | `git status` |
| 2. Authoring surface | AFK | `new-agent` route が消え、4 route が固定される | `test_copilot_authoring_docs.py` | 旧 test が `new-agent` を期待する | `uv run python -m pytest -q tests/test_copilot_authoring_docs.py` |
| 3. Evaluation surface | AFK | `privateEval` / `skill-eval` / empirical / loop の境界が docs と tests で固定される | new eval docs test | `privateEval` が実行入口として扱われる | `uv run python -m pytest -q tests/test_skill_eval_docs.py` |
| 4. Integration validation | AFK | skill validators / manifest / skill map / ruff が通る | targeted validation | router / manifest mismatch | targeted validation commands |

## Risks / Unknowns

- Copilot CLI plugin で slash command を完全に非表示にする仕組みは未確認。今回は構造上、`privateEval` を top-level skill にしないことで対応する。
- `new-agent` sub-skill の削除が installed plugin の既存利用者に影響する可能性はある。ただし user 方針として作らないため、公開 route から外す。
- `loop-engineering` 側の既存 `references/private-eval.md` は用語衝突を起こしやすい。必要最小限で「作業品質ゲート」と「評価ケース資産」を区別する。

## ADR

- `docs/adr/skill-single-responsibility-and-orchestration.md` を更新し、`new-agent` 除外と evaluation 分離を追記する。

## Implementation Handoff

### Goal

Happy AI Life の authoring / evaluation skill 構造を、薄い親 + 単一責務 route + privateEval reference の形へ整理する。

### Success Criteria

- `new-agent` route が `copilot-authoring` から外れる。
- `privateEval` は top-level skill ではなく `skill-eval` の内部 reference として扱われる。
- docs と tests が新構造を固定する。

### Out of Scope

- slash command 非表示機能。
- benchmark 実行。
- 新規 agent 作成。

### Artifacts

artifacts:
- docs/grill_results/005_GRILL_WITH_DOCS_RESULT.md
- docs/design/005_TECHNICAL_DESIGN.md
- docs/plan/005_PLAN.md

### Commands

```powershell
uv run python -m pytest -q tests/test_copilot_authoring_docs.py tests/test_skill_eval_docs.py tests/test_skill_map.py tests/test_plugin_manifest.py
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\copilot-authoring\SKILL.md --level L2
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\skill-eval\SKILL.md --level L2
uv run ruff check tests\test_copilot_authoring_docs.py tests\test_skill_eval_docs.py
```

### Return Conditions

- FAIL: targeted tests または validator の失敗が局所修正で直せる。
- REPLAN_REQUIRED: `privateEval` を top-level skill にしないと実現できない、または `new-agent` を消すと既存 plugin policy に反する。
