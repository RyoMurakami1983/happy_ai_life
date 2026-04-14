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

`spec-workshop` を呼び出し、仕様書を作成します。ゼロからの場合は `spec-workshop/sub_skills/from-scratch/` route に振り分けられ、対話で論点を掘り、必要な根拠だけを targeted research で固めます。

成果物: 仕様書（要件、制約、受け入れ条件）

### ステップ 2 — 設計を検証する（design-workshop）

仕様書を `design-workshop` に渡します。design-workshop の判断表に従い、standard（構造判断 → 実装適合レビュー → セキュリティ設計確認）または balanced-coupling-design（サブドメイン分類 → 3次元結合評価）を選びます。DDD 戦略パターンはこのステップで扱います。

成果物: 技術設計書 + planning handoff サマリ

### ステップ 3 — 実装計画を立てる（PLAN mode）

設計書と handoff サマリを PLAN mode に渡し、実装計画を立てます。ここでは、受け入れ条件と依存関係に加えて、実装前に確認すべきテスト方針の下地を揃えます。

成果物: 実装計画（フェーズ分割、依存関係、実行順序）

### ステップ 4 — テスト戦略と target repo bootstrap を確認する

実装計画を読み、TDD またはテストファーストで進められる粒度になっているかを確認します。テスト可能な受け入れ条件、主要な境界値、エラーパス、外部依存のモック境界が不足していれば、PLAN mode で計画補完を行います。

target repo を触る場合は、`.github/instructions/` が配布済みかもここで確認します。未配布なら `scripts/sync-to-repo.ps1 -TargetRepoPath PATH` 相当で配布するか、未配布のまま進める理由を handoff に残します。

interactive app では `sdd/references/interactive-app-bootstrap-checklist.md` を使い、最低限の test runner、import-safe 条件、runtime launch entrypoint を先に固定します。

成果物: TDD-ready handoff（テスト観点で補強された実装着手条件）

### ステップ 5 — contract checkpoint を固定する

plan artifact を読み、今回の実装を 1 slice に落とします。最低でも対象振る舞い、非対象、主要な test 観点、generator handoff に残す test artifact path / test command / runtime launch command、戻り先の条件を明示します。

成果物: slice contract（small-slice 単位の done 定義）

### ステップ 6 — 実装する

オーケストレーター主導で、TDD の Red-Green-Refactor サイクルを回しながら実装を進めます。必要なら `tdd-coder` を narrow generator として使います。設計の揺れが出たら `design-workshop` に、順序や分割の揺れが出たら PLAN mode に戻ります。trust boundary が変更された時点では built-in review または自己レビューで中間チェックします。

### ステップ 7 — implementation eval gate を通す

各 slice の実装後に `implementation-eval-gate` を実行し、`PASS` / `FAIL` / `REPLAN_REQUIRED` を返します。評価は実装スレッドと分け、次の行動を固定してから先へ進みます。

### ステップ 8 — 最終レビュー

実装完了後、built-in review または自己レビューで品質とセキュリティの両面を確認します。

## 注意点

- **焦って仕様を飛ばさない**: 仕様が曖昧なまま設計に進むと、手戻りが大きくなります。
- **各フェーズの成果物を確認してから次へ**: 前のフェーズの出力が不十分なら、戻って補完します。
- **テスト戦略レビューを共同計画にしない**: テスト観点を補っても、計画の正本は PLAN mode の出力または plan artifact に残します。
- **大きい sprint を既定にしない**: 初期導入では 1 slice ごとの contract-driven loop を優先し、必要になってから広げます。
