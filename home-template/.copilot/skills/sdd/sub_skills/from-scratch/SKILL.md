---
name: from-scratch
description: >
  ゼロから仕様駆動開発の前半工程（spec → design → plan）を進める。
  Use when: 仕様も設計もない状態から開発を始めたいとき。
---

# From Scratch

仕様がまだ存在しない状態から、仕様 → 設計 → 計画 → impl-and-ship handoff を順に進める sub-skill です。各フェーズの成果物が次のフェーズの入力になり、plan が完成したら `impl-and-ship` へ引き継ぎます。

## こんなときに使う

このスキルは次のようなときに使います:
- アイデアはあるが仕様書がまだないとき
- 要件を固めるところから始めたいとき
- 前半工程（spec → design → plan）を最初から通して進めたいとき

## ワークフロー: ゼロから plan handoff まで通す

### ステップ 0.5 — 環境判定（multirepository の確認）

対象プロジェクトが複数の関連リポを含むかを確認します。これにより、後続の設計フェーズでのハンドオフ形式が決まります。

**判定項目**:
- 「このプロジェクトに関連するリポは複数か」を質問。関連リポ（フロントエンド、バックエンド、モバイル、SDK など）を列挙する。

**判定結果の受け渡し**:
複数リポが判定された場合、以下のように **明示的に design-workshop へ handoff** してください：

```
【multirepository handoff】
- Multirepository: Yes
- Related Repositories:
  - Frontend (TypeScript/React)
  - Backend (Python/FastAPI)
  - ...
- Expected design route: balanced-coupling-design (Context Map 推奨)
```

単一リポの場合は、この情報を設計フェーズで記述する必要はありません。

**deep-research-preflight との関係**:
- `deep-research-preflight` skill でも multirepository 判定を行う場合があります
- preflight で判定済みの場合は、「既に preflight で multirepository = Yes と判定済み」と明示してください
- preflight と異なる判定が出た場合は、その旨をメモ（「preflight では single-repo、ここで multirepository 判定」）として design-workshop へ引き継ぎます

### ステップ 1 — 仕様を固める（spec-workshop）

`spec-workshop` を呼び出し、仕様書を作成します。ゼロからの場合は `spec-workshop/sub_skills/from-scratch/` route に振り分けられ、対話で論点を掘り、必要な根拠だけを targeted research で固めます。

成果物: 仕様書（要件、制約、受け入れ条件）

### ステップ 2 — 設計を検証する（design-workshop）

仕様書を `design-workshop` に渡します。design-workshop の判断表に従い、standard（構造判断 → 実装適合レビュー → セキュリティ設計確認）または balanced-coupling-design（サブドメイン分類 → 3次元結合評価）を選びます。DDD 戦略パターンはこのステップで扱います。

成果物: 技術設計書 + planning handoff サマリ

### ステップ 3 — 実装計画を立てる（PLAN mode）

設計書と planning handoff サマリを使用し、実装計画を立てます。以下のいずれかの方法で進めてください：

**方法 A: built-in PLAN mode を使う場合**
- セッション中に Shift+Tab で PLAN mode に切り替える
- 設計からの制約、依存関係、リスクを整理する
- plan.md が自動生成され、以下セクションが揃う：
  - Project Context
  - Phase Breakdown
  - Acceptance Criteria & Test Strategy
  - Risks & Mitigations

**multirepository 環境の場合の追加対応**:
- plan.md の「Project Context」に必ずリポ構成と依存順序を記述
- sdd/SKILL.md の「multirepository 環境での handoff」セクションを参照し、handoff フォーマットを合わせる

成果物: 実装計画（フェーズ分割、依存関係、実行順序）

### ステップ 4 — impl-and-ship へ handoff する

plan artifact が揃ったら `impl-and-ship` に引き継ぎます。`impl-and-ship` が bootstrap 確認、contract checkpoint、実装、eval gate、review、furikaeri、PR サイクルを担います。

interactive app の場合は `sdd/references/interactive-app-bootstrap-checklist.md` と `sdd/references/interactive-app-comparable-harness-contract.md` を handoff に添付します。

## 注意点

- **焦って仕様を飛ばさない**: 仕様が曖昧なまま設計に進むと、手戻りが大きくなります。
- **各フェーズの成果物を確認してから次へ**: 前のフェーズの出力が不十分なら、戻って補完します。
- **計画の正本は PLAN mode に置く**: テスト観点を補っても、計画そのものの正本にはなりません。
