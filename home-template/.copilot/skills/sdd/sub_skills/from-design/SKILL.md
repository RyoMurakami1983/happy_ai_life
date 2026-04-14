---
name: from-design
description: >
  設計書がある状態から計画以降を進める。
  Use when: 設計は終わっていて、計画と実装に入りたいとき。
---

# From Design

技術設計書が手元にある状態から、計画 → 実装 → レビュー を進める sub-skill です。design-workshop を経由せず、PLAN mode から開始します。

## こんなときに使う

このスキルは次のようなときに使います:
- 設計書が既に存在し、実装計画に入りたいとき
- design-workshop で設計を完了した後に中断し、再開するとき
- 外部で設計された仕様を実装するとき

## ワークフロー: 設計から計画以降を通す

### ステップ 1 — 設計書の存在確認

設計書が存在し、planning に渡せる状態かを確認します。以下が揃っているかをチェックします:
- コンポーネント構成と責務境界
- データフロー
- セキュリティ設計の確認結果

不足があれば `design-workshop` に戻ることを提案します。

### ステップ 2 — 実装計画を立てる（PLAN mode）

設計書を PLAN mode に渡し、実装計画を立てます。ここで受け入れ条件とテスト方針の下地も揃えます。

### ステップ 3 — テスト戦略と target repo bootstrap を確認する

計画を読み、TDD またはテストファーストで進められる粒度になっているかを確認します。テスト可能な受け入れ条件、主要な境界値、エラーパス、外部依存のモック境界が不足していれば、PLAN mode で計画補完を行います。

target repo を触る場合は、`.github/instructions/` が配布済みかもここで確認します。interactive app では `sdd/references/interactive-app-bootstrap-checklist.md` の前提も確認します。

### ステップ 4 — contract checkpoint → 実装 → implementation eval gate → 最終レビュー

`sdd/sub_skills/from-scratch/` のステップ 5-8 と同じ流れで進めます。

## 注意点

- **設計の妥当性を再確認しない**: 設計レビューは design-workshop で済んでいる前提です。設計に疑問があれば design-workshop に戻ります。
- **計画の更新は PLAN mode に戻す**: テスト観点を補っても、計画そのものの正本にはなりません。
