# PLAN 008

関連:
- [grill result 008](../grill_results/008_GRILL_WITH_DOCS_RESULT.md)
- [design 008](../design/008_TECHNICAL_DESIGN.md)
- [plan index](README.md)

## GOAL

GitHub-first knowledge storage と agent entrypoint の方針を、repo の durable artifact と skill wording に落とし込み、人間と AI の両方が同じ導線で辿れる状態にする。

## Success Criteria

- `AGENTS.md` が追加される
- `docs/README.md` と `docs/knowledge/README.md` が追加される
- `CONTEXT.md` と新規 ADR が canonical term / rationale を持つ
- `happy-add-issue` の gist guidance が新方針へ置き換わる
- focused docs test が通る

## Out of Scope

- Notion / MCP 実装
- gist guard policy の全廃
- PR 作成

## Progress

- [x] Bootstrap / 前提確認
- [x] Slice 1: Knowledge policy and domain terms
- [x] Slice 2: Entry points and knowledge tree
- [x] Slice 3: Skill/docs sync
- [x] Slice 4: Eval + deep review
- [x] Completion handoff

## Structure Decisions

- durable knowledge の正本は GitHub artifact に置く
- `AGENTS.md` は cross-agent brief として root に置く
- `docs/knowledge/` は shallow tree で始める
- gist は personal shared reference / snippet に用途を限定する

## Behavior List

- [x] `AGENTS.md` から repo の役割、主要 command、touch してよい境界が分かる
- [x] `docs/README.md` から docs 全体が辿れる
- [x] `docs/knowledge/README.md` から knowledge artifact の責務が分かる
- [x] 新規 ADR が GitHub-first knowledge storage を説明する
- [x] `happy-add-issue` が gist を issue detail の標準逃がし先として案内しない

## Vertical Slices

### Slice 1: Knowledge policy and domain terms

- Type: AFK
- Done: ADR / CONTEXT / policy docs の方針が確定する
- First test: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- RED expectation: 新規 term / ADR / required policy text が不足して失敗する
- GREEN command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- Acceptance command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- Out of scope: knowledge tree 全体の作成

### Slice 2: Entry points and knowledge tree

- Type: AFK
- Done: `AGENTS.md`, `docs/README.md`, `docs/knowledge/` 入口が揃う
- First test: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- RED expectation: missing file / missing section で失敗する
- GREEN command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- Acceptance command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- Out of scope: 各 knowledge node の重い本文

### Slice 3: Skill/docs sync

- Type: AFK
- Done: README / DEVELOPMENT / AUTHORING / `happy-add-issue` が新方針に同期する
- First test: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- RED expectation: old gist guidance や missing docs link が残る
- GREEN command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- Acceptance command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- Out of scope: 他 skill の全面改修

### Slice 4: Eval + deep review

- Type: AFK
- Done: focused validation、implementation eval、再 review が完了する
- First test: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- RED expectation: docs / wording / boundary mismatch が残る
- GREEN command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py`
- Acceptance command: `uv run python -m pytest -q tests\test_github_knowledge_docs.py && uv run ruff check tests\test_github_knowledge_docs.py`
- Out of scope: PR

## Order Rationale

- 先に用語と policy を固めると、後続の AGENTS / docs / skill wording がぶれない
- その後に入口ファイルを作り、最後に関連 docs と skill を同期する方が差分を小さく保てる

## Risks / Unknowns

- `docs/knowledge/` の初期ノードを増やしすぎると運用前に stale になる
- gist を完全否定すると、個人用 snippet の正当な用途まで潰しかねない

## Return Conditions

- FAIL: wording / docs / test mismatch があるが、現在の plan のまま修正できる
- REPLAN_REQUIRED: AGENTS / knowledge tree / ADR の責務分離が既存 repo 方針と衝突する

## Completion Handoff

- Completed slices:
  - Slice 1: Knowledge policy and domain terms
  - Slice 2: Entry points and knowledge tree
  - Slice 3: Skill/docs sync
  - Slice 4: Eval + deep review
- Commands:
  - `uv run python -m pytest -q tests\test_app_smoke.py tests\test_plugin_manifest.py tests\test_secret_guard_minimal.py tests\test_github_knowledge_docs.py tests\test_evals_policy.py`
  - `uv run python -m ruff check .`
  - `uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\happy-add-issue\SKILL.md --level L2`
- Main artifacts:
  - `AGENTS.md`
  - `docs/README.md`
  - `docs/knowledge/README.md`
  - `docs/adr/github-first-knowledge-storage-and-agent-entrypoints.md`
  - `tests/test_github_knowledge_docs.py`
- Remaining out of scope:
  - Notion / MCP integration
  - gist guard policy の全廃
  - PR 作成
