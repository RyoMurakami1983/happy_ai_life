---
name: from-spec
description: >
  仕様書がある状態から設計以降を進める。
  Use when: 仕様は固まっていて、設計から始めたいとき。
---

# From Spec

仕様書が手元にある状態から、設計 → 計画 → 実装 → レビュー を進める sub-skill です。spec-workshop を経由せず、design-workshop から開始します。

## こんなときに使う

このスキルは次のようなときに使います:
- 仕様書が既に存在し、設計に入りたいとき
- 外部から仕様を受け取って開発を進めたいとき
- spec-workshop で仕様を固めた後に中断し、再開するとき

## ワークフロー: 仕様から設計以降を通す

### ステップ 1 — 仕様の充足確認

仕様書が存在し、設計に進める状態かを確認します。以下が揃っているかをチェックします:
- 機能要件と受け入れ条件
- 対象の技術スタック
- 非機能要件の言及

不足があれば `spec-workshop` に戻ることを提案します。

### ステップ 2 — 設計を検証する（design-workshop）

仕様書を `design-workshop` に渡し、判断表に従い standard または balanced-coupling-design ルートで設計を進めます。

### ステップ 3 — 計画 → bootstrap / テスト戦略レビュー → contract checkpoint → 実装 → implementation eval gate → 最終レビュー

`sdd/sub_skills/from-scratch/` のステップ 3-8 と同じ流れで進めます。

## 注意点

- **仕様の充足確認を飛ばさない**: 仕様があっても不十分な場合があります。設計の手戻りを防ぐために最初に確認します。
