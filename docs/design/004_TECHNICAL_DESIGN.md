# Technical Design 004: Git write workflow confirmation defaults

## Goal

`git-commit` と `gh-pr-create` で、branch 名と commit message の候補提示と承認取得を既定動作として明文化し、関連 docs と配布 metadata を一貫させる。

## Success Criteria

- `plugins/happy-core/skills/git-commit/SKILL.md` が、毎回 branch 名候補と commit message 候補を提示し、承認後に commit する既定を明示する。
- `plugins/happy-core/skills/gh-pr-create/SKILL.md` が、未コミット時に上記確認ルールを引き継ぎ、branch 名候補の確認後に push / PR 作成へ進む既定を明示する。
- 補助例や関連 docs が同じ運用方針を説明する。
- `happy-core` plugin version と marketplace manifest の対応する version が更新される。
- focused test と skill validator が通る。

## Out of Scope

- `git-commit` / `gh-pr-create` の自動実行ロジック追加。
- `git push`、`git merge`、`git rebase` など他の Git 書き込み全般への拡大。
- built-in skill や外部 CLI 本体の挙動変更。

## Context / Source of Truth

- Issue #249
- `plugins/happy-core/skills/git-commit/SKILL.md`
- `plugins/happy-core/skills/git-commit/references/examples.md`
- `plugins/happy-core/skills/gh-pr-create/SKILL.md`
- `docs/DEVELOPMENT.md`
- `docs/SKILL_MAP.md`
- `plugins/happy-core/skills/copilot-authoring/references/plugin-versioning.md`

## Structure Decisions

- 既定動作の正本は `git-commit` と `gh-pr-create` の `SKILL.md` に置く。
- 具体例は `git-commit/references/examples.md` に寄せ、本文は短く保つ。
- 関連 docs は利用者導線に関係する `docs/DEVELOPMENT.md` と `docs/SKILL_MAP.md` に限定する。
- plugin 配布中 skill の UX 変更として、`plugins/happy-core/plugin.json` と `.github/plugin/marketplace.json` の `happy-core` version を patch 更新する。

## Public Interfaces / Test Surface

- `plugins/happy-core/skills/git-commit/SKILL.md`
- `plugins/happy-core/skills/git-commit/references/examples.md`
- `plugins/happy-core/skills/gh-pr-create/SKILL.md`
- `docs/DEVELOPMENT.md`
- `docs/SKILL_MAP.md`
- `tests/test_git_workflow_skill_docs.py`
- `plugins/happy-core/skills/copilot-authoring/_skill/_eval/scripts/validate_skill.py`

## Data Flow

```text
user asks to commit or create PR
  -> skill confirms branch purpose and branch name candidate
  -> skill confirms commit scope and commit message candidate
  -> approval is obtained
  -> commit runs
  -> gh-pr-create reuses the same confirmation rule when changes are still uncommitted
  -> push and PR creation proceed from the confirmed branch
```

## Security Boundary

- 対象は skill と docs の文面、および plugin version metadata に限定する。
- main / master 直コミット抑止を弱めず、むしろ「branch 名候補の確認」を既定化して事故防止を強化する。
- commit message は毎回候補提示してから承認を取る方針とし、曖昧なまま書き込み操作へ進まない。

## Behavior List

- `git-commit` は毎回 branch 名候補または branch 作成導線を先に提示する。
- `git-commit` は毎回 commit message 候補を提示し、承認後に commit する。
- `gh-pr-create` は branch 名候補の確認を飛ばさない。
- `gh-pr-create` は未コミット時に `git-commit` の確認ルールを引き継ぐ。
- 関連 docs は「既定で確認する」運用を同じ言葉で説明する。

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|
| Slice 1: policy assertions | AFK | skill / docs の必須文言を focused test で固定する | skill docs assertion test | branch / commit 確認既定の文言が欠けて落ちる | `uv run python -m pytest -q tests/test_git_workflow_skill_docs.py` |
| Slice 2: skill and docs update | AFK | `git-commit` / `gh-pr-create` / examples / related docs が同じ既定を説明する | Slice 1 の test | skill 間で方針がずれる | `uv run python -m pytest -q tests/test_git_workflow_skill_docs.py` |
| Slice 3: authoring and release alignment | AFK | validator と manifest version が整う | skill validator and manifest tests | validator fail または version 不整合 | `uv run python -m pytest -q tests/test_plugin_manifest.py tests/test_skill_map.py tests/test_git_workflow_skill_docs.py` |

## Risks / Unknowns

- prose の言い換えが強すぎると focused test が brittle になりうる。対策として、完全一致ではなく既定動作を示す中核語に絞って検証する。
- version 更新を忘れると plugin 配布物と marketplace metadata がずれる。既存 manifest test で補強する。

## ADR

- 不要。単一 repo 内の skill / docs / version 運用の更新に留まる。

## Implementation Handoff

### Goal

`git-commit` と `gh-pr-create` の既定動作として、branch 名候補と commit message 候補の確認を明文化し、関連 docs と plugin version を同期する。

### Success Criteria

- `git-commit` が毎回の branch / commit 候補確認を明示する。
- `gh-pr-create` が未コミット時も同じ確認ルールを引き継ぐ。
- examples / development docs / skill map が同じ方針に揃う。
- `happy-core` version と marketplace entry が更新される。
- focused tests と skill validator が通る。

### Out of Scope

- 他の Git 書き込み skill への展開。
- automation や hook の追加。

### Structure Decisions

- 正本: `plugins/happy-core/skills/git-commit/SKILL.md`, `plugins/happy-core/skills/gh-pr-create/SKILL.md`
- 補助例: `plugins/happy-core/skills/git-commit/references/examples.md`
- 関連 docs: `docs/DEVELOPMENT.md`, `docs/SKILL_MAP.md`
- version metadata: `plugins/happy-core/plugin.json`, `.github/plugin/marketplace.json`

### Behavior List

- 毎回 branch 名候補を確認する。
- 毎回 commit message 候補を確認する。
- 未コミットの PR 作成前でも同じ確認ルールを使う。
- plugin version を patch 更新する。

### Vertical Slices

1. focused test で required wording を先に固定する。
2. skill / docs / examples を更新して test を通す。
3. validator と manifest version を整え、review-ready にする。

### Artifacts

artifacts:
  - docs/design/004_TECHNICAL_DESIGN.md
  - docs/plan/004_PLAN_DONE.md

### Commands

```powershell
uv run python -m pytest -q tests/test_git_workflow_skill_docs.py tests/test_plugin_manifest.py tests/test_skill_map.py
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\git-commit\SKILL.md --level L2
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\gh-pr-create\SKILL.md --level L2
uv run ruff check tests\test_git_workflow_skill_docs.py
```

### Return Conditions

- FAIL: focused test、validator、manifest 整合のいずれかが落ちた場合は同じ plan で修正する。
- REPLAN_REQUIRED: `git-commit` / `gh-pr-create` の範囲では解決できず、他 skill か global instructions に既定を昇格する必要が出た場合は `design-and-plan` に戻す。
