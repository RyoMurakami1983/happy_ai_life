---
name: from-plan
description: >
  実装計画がある状態から実装とレビューを進める。
  Use when: 計画は立っていて、実装を開始したいとき。
---

# From Plan

実装計画が手元にある状態から、実装 slice → eval gate → レビュー を進める sub-skill です。既存の計画を確認したうえで、実装フェーズから開始します。plan artifact は `plan.md`、todo、PLAN summary、外部作成の実装計画を含みます。

## こんなときに使う

このスキルは次のようなときに使います:
- 実装計画が既に存在し、コーディングに入りたいとき
- PLAN mode や既存 plan artifact を作った後に中断し、再開するとき
- 外部で作成された計画に沿って実装するとき

## ワークフロー: 計画から実装を通す

### ステップ 1 — 計画の確認

実装計画が存在し、実装を始められる状態かを確認します。以下が揃っているかをチェックします:
- todo リスト（実装対象と依存関係）
- 技術的な前提条件
- 受け入れ条件
- テスト可能な受け入れ条件、主要な境界値、エラーパス、外部依存のモック境界

不足があれば、まずテスト戦略を見直します。計画の補完が必要なら PLAN mode に戻します。

### ステップ 2 — contract checkpoint を固定する

実装に入る前に、今回の slice で何を done とみなすかを固定します。最低でも次を残します:

- 今回の対象振る舞い
- 非対象
- 主要な test 観点
- `FAIL` なら実装修正、`REPLAN_REQUIRED` なら plan / design に戻る条件

大きな sprint を一度に抱えず、まずは 1 受け入れ条件または 1 ユーザー行動を 1 slice として切ります。

### ステップ 3 — TDD で実装する

オーケストレーター主導で Red-Green-Refactor サイクルを回しながら、レビュー済みの計画に沿って実装を進めます。必要なら `tdd-coder` を narrow generator として使います。

- ビルドエラーや計画逸脱が発生したら PLAN mode / `design-workshop` に戻る
- リファクタリングは振る舞い不変を前提に自分で小さく進める
- trust boundary が変更されたら built-in review または自己レビューで中間チェック

### ステップ 4 — implementation eval gate を通す

実装後は、`implementation-eval-gate` で slice を別タスク評価します。ここでは実装を直し始めず、まず verdict を固定します。

- `PASS`: 次の slice へ進む
- `FAIL`: 同じ plan のまま generator に戻す
- `REPLAN_REQUIRED`: PLAN mode または `design-workshop` に戻す

### ステップ 5 — 最終レビュー

実装完了後、built-in review または自己レビューで品質とセキュリティを確認します。

## 注意点

- **計画を無視して実装しない**: 計画にない作業は scope creep の原因です。必要なら PLAN mode で計画を更新します。
- **TDD サイクルを飛ばさない**: テストを先に書くことで、実装の品質と網羅性を担保します。
- **eval を自己レビューで代替しない**: 次へ進む gate は、できるだけ実装スレッドから分けて評価します。
