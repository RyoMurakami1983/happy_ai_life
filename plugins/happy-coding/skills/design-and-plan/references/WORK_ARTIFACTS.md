# Work Artifacts

`interview-with-docs` から `design-and-plan`、`implement` へ渡る成果物の既定構造です。

## Canonical doc structure

```text
docs/
  grill_results/
    001_GRILL_WITH_DOCS_RESULT.md
  design/
    001_TECHNICAL_DESIGN.md
  plan/
    001_PLAN.md
  adr/
    0001-short-slug.md
```

## Numbering rules

- `grill_results` / `design` / `plan` は同じ案件番号 `NNN` を共有する
- ADR は `docs/adr/0001-short-slug.md` の独立連番を使う

## Write timing

- `CONTEXT.md` は用語解決ごとに inline 更新する
- `docs/grill_results/NNN_GRILL_WITH_DOCS_RESULT.md` は grill 完了時に保存する
- `docs/design/NNN_TECHNICAL_DESIGN.md` は設計判断を後で読み返す価値がある場合、またはユーザーが設計書の保存を明示した場合に保存する
- `docs/plan/NNN_PLAN.md` は implementation handoff を checklist として追いたい場合、またはユーザーが計画書の保存を明示した場合に作る
- `implement` の completion handoff まで終わったら、必要に応じて `docs/plan/NNN_PLAN_DONE.md` へリネームする

## Boundary with `implement`

`docs/plan/NNN_PLAN.md` は人間向けの進捗計画です。
`implement` は各 slice の直前に slice contract を再固定し、TDD loop と slice gate を実行します。
handoff には必ず `artifacts:` フィールドを含めます。値は `artifacts: conversation-only`、または `artifacts:` の下に保存した path を列挙する形に統一します。`implement` は bootstrap でこのフィールドを見て、列挙された path の存在確認を行います。

multirepository fleet の contract verification が読む repo root の `plan.md` YAML front-matter とは別物として扱います。

## Technical Design template

```markdown
# Technical Design NNN: [Project / Feature]

## Goal

## Success Criteria

## Out of Scope

## Context / Source of Truth

## Structure Decisions

## Public Interfaces / Test Surface

## Data Flow

## Security Boundary

## Behavior List

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|

## Risks / Unknowns

## ADR

## Implementation Handoff

### Goal

### Success Criteria

### Out of Scope

### Structure Decisions

### Behavior List

### Vertical Slices

### Artifacts

```markdown
### Artifacts

artifacts: conversation-only
```

または:

```markdown
### Artifacts

artifacts:
  - docs/design/NNN_TECHNICAL_DESIGN.md
  - docs/plan/NNN_PLAN.md
```

### Commands

### Return Conditions
```

## PLAN template

PLAN の正本テンプレートは `assets/NNN_PLAN_TEMPLATE.md` に置きます。
PLAN は進捗を追う補助であり、重い工程表ではありません。

含めるもの:

- `GOAL`
- `Success Criteria`
- `Out of Scope`
- `Structure Decisions`
- `Behavior List`
- `Vertical Slices`
- 各 slice の `HITL / AFK`
- 各 slice の `First test`
- `RED expectation`
- `GREEN command`
- `Acceptance command`
- `Return Conditions`

含めないもの:

- 毎回の MVP 技術選定
- 詳細すぎるモジュールテスト仕様
- 実装後の PR / review / furikaeri 手順
- phase ごとの自動停止指示
