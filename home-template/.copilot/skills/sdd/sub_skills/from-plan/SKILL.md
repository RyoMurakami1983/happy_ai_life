---
name: from-plan
description: >
  計画がある状態から実装サイクルを開始する。
  Use when: 計画が揃っていて実装フェーズに入りたいとき。
compatibility: "impl-and-ship"
---

# From Plan — Handoff to Implementation

このルートは `impl-and-ship` skill へ直接 handoff するための sub-skill です。

計画（plan.md / todos / PLAN summary）が手元にある場合は、以下のステップで `impl-and-ship` へ引き継いでください。

## こんなときに使う

このスキルは次のようなときに使います:
- plan.md が既に揃っていて、実装フェーズに入りたいとき
- PLAN mode を実行済みで、計画が確定したとき
- sdd/from-design で計画を作成し、実装の入口を確認したいとき

## ワークフロー: plan artifact から impl-and-ship へ

### ステップ 1 — 計画の completeness チェック

plan.md が以下の必須セクションを満たしているか確認します：
- **Project Context**: リポ構成（multirepository の場合）、key constraints
- **Phase Breakdown**: 各フェーズと終了条件
- **Acceptance Criteria & Test Strategy**: テスト観点
- **Risks & Mitigations**: 既知リスクと対策

いずれかが不足している場合は、PLAN mode に戻るか plan.md を直接編集してから次へ進んでください。

### ステップ 2 — impl-and-ship へ引き継ぐ

`impl-and-ship` を呼び出し、以下の情報を渡してください：
```
plan artifact path: ~/.copilot/session-state/<session-id>/plan.md
multirepository: true/false
related repositories: [list if multirepository]
```

`impl-and-ship` が bootstrap 確認、contract checkpoint、実装（TDD）、eval gate、review、furikaeri、PR サイクル全体を担います。

## 注意点

- **計画の品質が実装を左右する**: plan.md の重要性は spec / design と同等です。不完全な計画で進むと、実装途中で何度も戻ります
- **plan artifact の正本**: PLAN mode で生成した plan.md が最終版です。途中の trial や仮設置はこの skill の scope 外です
- **multirepository 環境での並列実装**: plan.md に依存順序が明記されていれば、impl-and-ship が `/fleet` で並列実装を判定します
