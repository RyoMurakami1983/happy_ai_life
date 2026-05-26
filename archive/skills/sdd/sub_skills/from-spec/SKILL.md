---
name: from-spec
description: >
  仕様書がある状態から設計以降を進める。
  Use when: 仕様は固まっていて、設計から始めたいとき。
---

# From Spec

仕様書が手元にある状態から、設計 → 計画 → implement handoff を進める sub-skill です。spec-workshop を経由せず、design-and-plan から開始します。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


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

**multirepository 判定と explicit handoff**:
- 「このプロジェクトに関連するリポは複数か」を質問。関連リポを列挙する。
- 判定結果を **明示的に design-and-plan へ handoff** してください：

```
【multirepository handoff】
- Multirepository: Yes/No
- Related Repositories（複数の場合）:
  - Frontend (TypeScript/React)
  - Backend (Python/FastAPI)
  - ...
- Expected design route（複数の場合）: balanced-coupling-design (Context Map 推奨)
```

**deep-research-preflight との関係**:
- preflight で multirepository 判定済みの場合は、「preflight で既に判定済み（multirepository = Yes）」と明示してください
- 調査段階で判定が不明だった場合は、ここで改めて「複数関連リポがあるか」を質問します

不足があれば `spec-workshop` に戻ることを提案します。

---

### ステップ 1.5 — 必要ならモックを挟む

要求の理解や画面・操作感の確認を優先したい場合は、ここでモックを作成します。モックの技術は仮選定として扱い、そのまま MVP の本選定に直結させません。

### ステップ 2 — 設計を検証する（design-and-plan）

仕様書を `design-and-plan` に渡し、判断表に従い standard または balanced-coupling-design ルートで設計を進めます。standard ルートでは、構造判断の後に MVP 技術選定チェックポイントを通して本採用する言語・フレームワークを比較・決定します。balanced-coupling-design ルートでは、ステップ 3 のモジュール設計で技術方式を選定します。

### ステップ 3 — 実装計画と implement handoff

設計書が完成したら、from-design または from-plan を使用して PLAN mode → implement へ引き継ぎます：

**ルート選択**:
- 計画をゼロから立てる場合は `sdd/sub_skills/from-design/` を呼び出す
- 計画が既に存在する場合は `sdd/sub_skills/from-plan/` を呼び出す
- どちらでも最終的には `implement` へ handoff します

## 注意点

- **仕様の充足確認を飛ばさない**: 仕様があっても不十分な場合があります。設計の手戻りを防ぐために最初に確認します。
