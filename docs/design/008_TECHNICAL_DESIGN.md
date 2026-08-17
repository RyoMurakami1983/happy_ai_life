# Technical Design 008: GitHub-first knowledge storage の導線整備

## Goal

この repo の durable knowledge を GitHub 上の artifact に集約し、`AGENTS.md`、`docs/README.md`、`docs/knowledge/`、関連 skill / instructions / tests を通じて、人間と AI の両方が同じ導線で辿れる状態にする。

## Success Criteria

- repo root に `AGENTS.md` が追加され、repo purpose / commands / boundaries / source-of-truth が明示される
- `docs/README.md` と `docs/knowledge/README.md` が追加され、docs 全体と knowledge artifact の置き場が辿れる
- `CONTEXT.md` に GitHub-first knowledge 運用で使う canonical term が追加される
- GitHub-first knowledge storage の判断理由が ADR と関連 docs に残る
- `happy-add-issue` から gist を long detail の標準逃がし先として案内しない
- docs / tests が新方針を固定する

## Out of Scope

- Notion / MCP 連携の実装
- gist 自体の guard policy 廃止
- full repo-wide knowledge migration
- PR 作成と review response

## Context / Source of Truth

- `.github/copilot-instructions.md`
- `CONTEXT.md`
- `README.md`
- `docs/AUTHORING.md`
- `docs/DEVELOPMENT.md`
- `docs/adr/instruction-hierarchy-and-authoritative-source.md`
- `docs/adr/skill-single-responsibility-and-orchestration.md`
- `plugins/happy-core/skills/happy-add-issue/SKILL.md`
- [grill result 008](../grill_results/008_GRILL_WITH_DOCS_RESULT.md)
- [design index](README.md)

## Structure Decisions

### 1. GitHub-first knowledge boundary

durable knowledge の正本は GitHub repo 内の docs / ADR / Issue / PR / instructions / `AGENTS.md` とする。gist は個人用 shared reference / snippet の用途に限定し、repo 固有の long detail や issue 補助の既定には使わない。

### 2. New top-level knowledge entry points

- `AGENTS.md`: cross-agent brief
- `docs/README.md`: docs 全体の index
- `docs/knowledge/README.md`: knowledge artifact の入口

初期の `docs/knowledge/` は shallow tree を守り、まずは `context/`, `playbooks/`, `troubleshooting/`, `lessons/`, `references/` の index だけを置く。

### 3. Responsibility separation

- `AGENTS.md`: current behavior, commands, boundaries
- `copilot-instructions.md`: repo-specific facts and dispatch
- ADR: why
- `docs/knowledge/`: durable reusable reference
- skill docs: workflow detail

### 4. Learnings adoption

`learnings` は「会話ログ」ではなく「再発防止へ圧縮した短い一般化ルール」として定義し、関連 docs からその役割が分かるようにする。

### 5. ADR strategy

今回の方針は hard-to-reverse かつ tradeoff を伴うため、新規 ADR を追加して GitHub-first knowledge storage の判断を残す。

## Public Interfaces / Test Surface

- `AGENTS.md`
- `README.md`
- `docs/README.md`
- `docs/knowledge/README.md`
- `docs/knowledge/**/index.md`
- `CONTEXT.md`
- `docs/DEVELOPMENT.md`
- `docs/AUTHORING.md`
- `plugins/happy-core/skills/happy-add-issue/SKILL.md`
- 新規 targeted docs test

## Data Flow

```text
research / repo policy
  -> ADR / docs / CONTEXT / AGENTS
  -> repo-wide instructions and skill wording
  -> targeted docs test
```

## Security Boundary

- gist を secret store と誤解させない
- external live config や private detail を docs の既定導線に混ぜない
- repo knowledge と personal cheat sheet を分離する

## Behavior List

- [ ] AGENTS.md から repo の purpose / commands / boundaries が分かる
- [ ] docs 全体の入口が `docs/README.md` に集約される
- [ ] `docs/knowledge/` の役割と各ノードの責務が明記される
- [ ] GitHub-first knowledge の判断理由が ADR に残る
- [ ] `happy-add-issue` が gist を補助 detail の標準導線として案内しない
- [ ] learnings の意味が docs / context 上で分かる

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|
| 1. Knowledge policy and domain terms | AFK | ADR / CONTEXT / docs policy が固まる | targeted docs test | 新しい term / ADR / refs が存在しない | `uv run python -m pytest -q tests/test_github_knowledge_docs.py` |
| 2. Entry points and knowledge tree | AFK | `AGENTS.md`, `docs/README.md`, `docs/knowledge/` が追加される | targeted docs test | 入口ファイルや required section が足りない | `uv run python -m pytest -q tests/test_github_knowledge_docs.py` |
| 3. Skill/docs sync | AFK | gist guidance fix と README / DEVELOPMENT / AUTHORING の整合が取れる | targeted docs test | 古い gist guidance や missing link が残る | `uv run python -m pytest -q tests/test_github_knowledge_docs.py` |
| 4. Eval and deep review | AFK | focused validation と再 review が通る | same test + lint | docs policy mismatch が残る | `uv run python -m pytest -q tests/test_github_knowledge_docs.py && uv run ruff check tests/test_github_knowledge_docs.py` |

## Risks / Unknowns

- `docs/knowledge/` を作り込みすぎると、まだ使われていない空ディレクトリだけ増える
- gist guidance を一気に全部消すと、個人用 shared reference の有効な用途まで失われる可能性がある

## ADR

- 新規 ADR を作成する: `docs/adr/github-first-knowledge-storage-and-agent-entrypoints.md`

## Implementation Handoff

### Goal

GitHub-first knowledge storage 方針を、repo の入口ファイル、knowledge tree、用語、issue-related skill wording、tests に反映する。

### Success Criteria

- `AGENTS.md`、`docs/README.md`、`docs/knowledge/README.md` が存在する
- 新規 ADR と `CONTEXT.md` が方針を説明する
- `happy-add-issue` が gist を long detail 置き場として推奨しない
- focused docs test が通る

### Out of Scope

- Notion integration
- PR 作成
- whole-repo docs refactor

### Artifacts

artifacts:
  - [docs/grill_results/008_GRILL_WITH_DOCS_RESULT.md](../grill_results/008_GRILL_WITH_DOCS_RESULT.md)
  - [docs/design/008_TECHNICAL_DESIGN.md](008_TECHNICAL_DESIGN.md)
  - [docs/plan/008_PLAN_DONE.md](../plan/008_PLAN_DONE.md)

### Commands

```powershell
uv run python -m pytest -q tests/test_github_knowledge_docs.py
uv run ruff check tests/test_github_knowledge_docs.py
```

### Return Conditions

- FAIL: wording / docs / test mismatch が局所修正で直る
- REPLAN_REQUIRED: `docs/knowledge/` の責務や AGENTS の位置づけが既存 ADR と両立しない
