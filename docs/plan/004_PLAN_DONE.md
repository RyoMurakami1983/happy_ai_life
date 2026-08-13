# PLAN 004

## GOAL

`git-commit` と `gh-pr-create` で、branch 名候補と commit message 候補の確認を毎回の既定動作として明文化し、関連 docs と plugin version をそろえる。

## Success Criteria

- `git-commit` が毎回 branch 名候補と commit message 候補を提示し、承認後に commit することを明示する。
- `gh-pr-create` が branch 名候補の確認を行い、未コミット時は同じ commit 確認ルールを引き継ぐことを明示する。
- examples / docs / version metadata がこの方針に揃う。
- focused test、manifest test、skill validator が通る。

## Out of Scope

- Git の他の書き込み経路への横展開。
- 実コマンドの自動化や hook 実装。
- built-in skill や Copilot CLI 本体の変更。

## Progress

- [x] Bootstrap / 前提確認
- [x] Slice 1: policy assertions
- [x] Slice 2: skill and docs update
- [x] Slice 3: authoring and release alignment
- [x] Completion handoff

## Structure Decisions

- 既定動作の正本は `git-commit` / `gh-pr-create` の `SKILL.md` に置く。
- 補助例は `git-commit/references/examples.md` に寄せる。
- 関連 docs は `docs/DEVELOPMENT.md` と `docs/SKILL_MAP.md` に限定する。
- plugin UX 変更として `happy-core` version と marketplace entry version を patch 更新する。

## Behavior List

- [ ] `git-commit` が毎回 branch 名候補を確認する。
- [ ] `git-commit` が毎回 commit message 候補を確認する。
- [ ] `gh-pr-create` が未コミット時も同じ確認ルールを引き継ぐ。
- [ ] docs が「既定で確認する」運用を明記する。
- [ ] `happy-core` の version metadata が同期する。

## Vertical Slices

### Slice 1: policy assertions

- Type: AFK
- Done: skill / docs の required wording を focused test で固定できる。
- First test: `tests/test_git_workflow_skill_docs.py` で branch / commit 確認既定を検証する。
- RED expectation: required wording が存在せず test が落ちる。
- GREEN command: `uv run python -m pytest -q tests/test_git_workflow_skill_docs.py`
- Acceptance command: `uv run python -m pytest -q tests/test_git_workflow_skill_docs.py`
- Out of scope: skill 本文の最終 wording 調整以外の release metadata。

### Slice 2: skill and docs update

- Type: AFK
- Done: `git-commit` / `gh-pr-create` / examples / docs が同じ confirmation policy を説明する。
- First test: Slice 1 の focused test。
- RED expectation: skill 間または docs 間で policy がずれて落ちる。
- GREEN command: `uv run python -m pytest -q tests/test_git_workflow_skill_docs.py`
- Acceptance command: `uv run python -m pytest -q tests/test_git_workflow_skill_docs.py tests/test_skill_map.py`
- Out of scope: plugin version 更新。

### Slice 3: authoring and release alignment

- Type: AFK
- Done: skill validator と manifest version 整合が通る。
- First test: `tests/test_plugin_manifest.py`
- RED expectation: `happy-core` version が marketplace entry とずれる、または skill validator が落ちる。
- GREEN command: `uv run python -m pytest -q tests/test_plugin_manifest.py tests/test_skill_map.py tests/test_git_workflow_skill_docs.py`
- Acceptance command: `uv run python -m pytest -q tests/test_plugin_manifest.py tests/test_skill_map.py tests/test_git_workflow_skill_docs.py && uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\git-commit\SKILL.md --level L2 && uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\gh-pr-create\SKILL.md --level L2 && uv run ruff check tests\test_git_workflow_skill_docs.py`
- Out of scope: commit / push / PR 作成 / merge。

## Order Rationale

- 先に test で expected wording を固定すると、skill と docs の更新がぶれにくい。
- skill 本文を正本としてそろえた後に docs を合わせると、説明の重複が管理しやすい。
- version 更新と validator は最後にまとめて確認した方が出荷整合を見落としにくい。

## Risks / Unknowns

- 文言検証を厳しくしすぎると将来の改善で brittle になる。
- version 更新の範囲を `happy-core` だけに留める判断が妥当か確認が必要。

## Return Conditions

- FAIL: focused test / validator / manifest test が落ちた場合は同じ plan で修正する。
- REPLAN_REQUIRED: skill 単体の更新では既定動作を守りきれず、別の instructions や hook 設計が必要になった場合は `design-and-plan` に戻す。
