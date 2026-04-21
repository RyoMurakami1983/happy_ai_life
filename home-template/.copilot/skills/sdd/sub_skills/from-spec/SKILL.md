---
name: from-spec
description: >
  仕様書がある状態から設計以降を進める。
  Use when: 仕様は固まっていて、設計から始めたいとき。
---

# From Spec

仕様書が手元にある状態から、設計 → 計画 → impl-and-ship handoff を進める sub-skill です。spec-workshop を経由せず、design-workshop から開始します。

## こんなときに使う

このスキルは次のようなときに使います:
- 仕様書が既に存在し、設計に入りたいとき
- 外部から仕様を受け取って開発を進めたいとき
- spec-workshop で仕様を固めた後に中断し、再開するとき

## ワークフロー: 仕様から plan handoff まで通す

### ステップ 0 — 仕様の充足確認と multirepository 判定

仕様書が設計に進める状態かを確認し、同時に multirepository 環境かを判定します。以下を確認してください:

**仕様充足確認**:
- 機能要件と受け入れ条件
- 対象の技術スタック
- 非機能要件の言及

**multirepository 判定**:
- 「このプロジェクトに関連するリポは複数か」を質問。関連リポを列挙する。
- 複数リポが判定された場合、複数リポ構成をそのまま design-workshop へ受け渡してください。

不足があれば `spec-workshop` に戻ることを提案します。

**関連ドキュメント**: `deep-research-preflight` skill でも multirepository 環境判定を行うことが可能です。調査段階で既に multirepository 判定が済んでいる場合は、ここで再確認する必要はありません。

---

### ステップ 1 — 設計を検証する（design-workshop）

仕様書を `design-workshop` に渡し、判断表に従い standard または balanced-coupling-design ルートで設計を進めます。

### ステップ 3 — 計画 → impl-and-ship へ handoff

`sdd/sub_skills/from-scratch/` のステップ 3-4 と同じ流れで進めます（PLAN mode → impl-and-ship handoff）。

## 注意点

- **仕様の充足確認を飛ばさない**: 仕様があっても不十分な場合があります。設計の手戻りを防ぐために最初に確認します。
