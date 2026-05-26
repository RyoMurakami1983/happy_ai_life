# Work Artifacts

`grill-with-docs` から `design-and-plan`、`implement` へ渡る成果物の既定構造です。

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
- `docs/design/NNN_TECHNICAL_DESIGN.md` は設計完了時に保存する
- `docs/plan/NNN_PLAN.md` は implementation handoff 可能な段階でだけ作る
- `implement` の Step 7 完了処理まで終わったら `docs/plan/NNN_PLAN_DONE.md` へリネームする

## Boundary with `implement`

`docs/plan/NNN_PLAN.md` は人間向けの進捗計画です。multirepository fleet の contract verification が読む repo root の `plan.md` YAML front-matter とは別物として扱います。

## Technical Design template

```markdown
# 技術設計書: [プロジェクト/機能名]

## ゴール
[何を達成する設計か]

## 成功条件
- [設計が成立したと判断する条件]

## 確認手段
- [設計をどう確認するか]

## 概要
[構造の要約]

## コンポーネント構成
[責務境界]

## データフロー
[主要フロー]

## MVP 技術選定
[採用技術、比較結果、見直し条件]

## 技術検証結果
[実装適合レビュー]

## セキュリティ設計
[trust boundary、認証、入力検証]

## 設計判断の記録
[ADR がある場合]

## 余白メモ
[今は決めなくてよいこと]

## Implementation Handoff

### 設計判断の要約
- [コンポーネント、責務、データフロー]

### 確定事項
- [実装で前提にしてよい判断]

### 制約
- [技術的制約、セキュリティ要件]

### 未決定事項
- [保留した判断]

### リスク
- [実装時の注意点]
```

## PLAN template

`web-to-tools` の PLAN を土台にしつつ、進捗確認しやすいように「現在位置」と「スライス進捗」を明示します。

```markdown
# PLAN NNN

## GOAL
[GOAL を 1-2 文で固定する]

## ゴール時点で成立している状態

- [完了時の状態]

## 現在位置

- 現在のマイルストーン: [M1 / M2 / M3 ...]
- 現在のスライス: [Slice 1 / Slice 2 ...]
- 次のチェックポイント: [次に確認すること]

## 逆算したマイルストーン

### M3. [完了状態]
- [条件]

### M2. [中間状態]
- [条件]

### M1. [着手状態]
- [条件]

## 実装スライス進捗

| Slice | 目的 | 状態 | 完了条件 |
| --- | --- | --- | --- |
| Slice 1 | [目的] | pending | [done の定義] |
| Slice 2 | [目的] | pending | [done の定義] |

状態は `pending` / `in_progress` / `done` / `blocked` を使う。

## 実装順序の理由

- [なぜこの順序か]

## 受け入れ条件

- [観測可能な条件]

## 対象外

- [今回やらないこと]

## リスク / 未決定事項

- [残課題]
```
