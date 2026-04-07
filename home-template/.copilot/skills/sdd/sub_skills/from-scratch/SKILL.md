---
name: from-scratch
description: >
  ゼロから仕様駆動開発の全工程を進める。
  Use when: 仕様も設計もない状態から開発を始めたいとき。
---

# From Scratch

仕様がまだ存在しない状態から、仕様 → 設計 → 計画 → 実装 → レビュー の全工程を順に進める sub-skill です。最も長いパスですが、各フェーズの成果物が次のフェーズの入力になるため、手戻りが少なくなります。

## こんなときに使う

このスキルは次のようなときに使います:
- アイデアはあるが仕様書がまだないとき
- 要件を固めるところから始めたいとき
- 全工程を最初から通して進めたいとき

## ワークフロー: ゼロから全工程を通す

### ステップ 1 — 仕様を固める（spec-workshop）

`spec-workshop` を呼び出し、仕様書を作成します。ゼロからの場合は `spec-workshop/sub_skills/from-scratch/` route に振り分けられ、`spec-interviewer` で論点を掘り、`deep-researcher` で根拠を固めます。

成果物: 仕様書（要件、制約、受け入れ条件）

### ステップ 2 — 設計を検証する（design-workshop）

仕様書を `design-workshop` に渡します。design-workshop の判断表に従い、standard（構造判断 → 言語検証 → セキュリティ設計確認）または balanced-coupling-design（サブドメイン分類 → 3次元結合評価）を選びます。DDD 戦略パターンはこのステップで扱います。

成果物: 技術設計書 + planner handoff サマリ

### ステップ 3 — 実装計画を立てる（planner）

設計書と handoff サマリを `planner` に渡し、実装計画を立てます。ここでは、受け入れ条件と依存関係に加えて、`tdd-guide` に渡せるテスト方針の下地を揃えます。

成果物: 実装計画（フェーズ分割、依存関係、実行順序）

### ステップ 4 — テスト戦略を確認する（tdd-guide）

`tdd-guide` に実装計画を渡し、TDD 観点で計画をレビューします。テスト可能な受け入れ条件、主要な境界値、エラーパス、外部依存のモック境界が不足していれば、`planner` に計画補完を依頼します。

成果物: TDD-ready handoff（テスト観点で補強された実装着手条件）

### ステップ 5 — 実装する（tdd-guide + build-resolver + refactor）

`tdd-guide` で TDD の Red-Green-Refactor サイクルを回しながら実装を進めます。ビルドエラーは `build-resolver`、リファクタリングは `refactor` に委譲します。trust boundary が変更された時点で `security-review` を中間チェックします。

### ステップ 6 — 最終レビュー（code-quality-review + security-review）

実装完了後、`code-quality-review` と `security-review` で品質とセキュリティの両面を確認します。

## 注意点

- **焦って仕様を飛ばさない**: 仕様が曖昧なまま設計に進むと、手戻りが大きくなります。
- **各フェーズの成果物を確認してから次へ**: 前のフェーズの出力が不十分なら、戻って補完します。
- **テスト戦略レビューを共同計画にしない**: `tdd-guide` はテスト観点を返しますが、計画の正本は `planner` に残します。
