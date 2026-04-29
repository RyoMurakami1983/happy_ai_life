---
name: from-design
description: >
  設計書がある状態から計画以降を進める。
  Use when: 設計は終わっていて、計画フェーズに入りたいとき。
---

# From Design

技術設計書が手元にある状態から、計画 → impl-and-ship handoff を進める sub-skill です。design-workshop を経由せず、PLAN mode から開始します。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

このスキルは次のようなときに使います:
- 設計書が既に存在し、実装計画に入りたいとき
- design-workshop で設計を完了した後に中断し、再開するとき
- 外部で設計された仕様を計画フェーズから進めるとき

## ワークフロー: 設計から plan handoff まで通す

### ステップ 1 — 設計書の存在確認

設計書が存在し、planning に渡せる状態かを確認します。以下が揃っているかをチェックします:
- コンポーネント構成と責務境界
- データフロー
- セキュリティ設計の確認結果

不足があれば `design-workshop` に戻ることを提案します。

### ステップ 2 — 実装計画を立てる（PLAN mode）

設計書を PLAN mode に渡し、実装計画を立てます。以下のいずれかの方法で進めてください：

**方法 A: built-in PLAN mode を使う場合**
- **PLAN mode の起動**: セッション中に Shift+Tab キーを入力して PLAN mode に切り替える
  - 条件：現在のセッションが「対話モード」（通常の会話状態）である必要があります
  - 入力後：Copilot CLI が PLAN mode に移行し、plan.md が生成されます（下記参照）
- 設計からの制約、依存関係、リスクを対話的に整理する
- plan.md が自動生成され、以下セクションが揃う：
  - **Project Context** — リポ構成（multirepository の場合）、trust boundaries、key constraints
  - **Phase Breakdown** — 各実装フェーズと終了条件
  - **Acceptance Criteria & Test Strategy** — テスト観点
  - **Risks & Mitigations** — 既知リスクと対策

**plan.md の生成と保存**:
- PLAN mode 実行中：`~/.copilot/session-state/<session-id>/plan.md` に一時保存
- セッション終了後：ユーザーが accept すれば、project root の `plan.md` として persist
- plan.md が既に project root に存在する場合は、自動で上書きするか確認を促します

**方法 B: 既存 plan.md が完全な場合**
- plan.md が以下の条件を満たしていれば、このステップをスキップして ステップ 3 へ進める：
  - **最小要件**: Project Context、Phase Breakdown、Acceptance Criteria、Risks の 4 セクションが存在し、各セクションに 1 行以上の内容がある
  - **multirepository 推奨**: リポ構成と依存順序（例：Backend → Frontend の順序）が Project Context に明記されている
- 計画の更新が必要なら、plan.md を project root で直接編集してから ステップ 3 へ進む
- PLAN mode 再実行は不要

**multirepository 環境の場合**
- plan.md の「Project Context」に必ず以下を記述：
  - リポ構成（例：Frontend (React) + Backend (FastAPI)）
  - 実装依存順序（例：Backend API contract 完成 → Frontend 開発可能）
- plan.md の「Phase Breakdown」に各リポの実装順序と依存条件を記述
- 詳細フォーマットは `sdd/SKILL.md` の「multirepository 環境での handoff」セクションを参照
- **推奨**: 小規模（2 リポ）なら統合 plan、中規模以上（3+ リポ）なら分割 plan artifact（plan-backend.md など）を検討

### ステップ 3 — impl-and-ship へ handoff する

plan artifact が揃ったら `impl-and-ship` に引き継ぎます。`impl-and-ship` が bootstrap 確認、contract checkpoint、実装、eval gate、review、furikaeri、PR サイクルを担います。

interactive app の場合は `sdd/references/interactive-app-bootstrap-checklist.md` を handoff に添付します。

## 注意点

- **設計の妥当性を再確認しない**: 設計レビューは design-workshop で済んでいる前提です。設計に疑問があれば design-workshop に戻ります。
- **計画の更新は PLAN mode に戻す**: テスト観点を補っても、計画そのものの正本にはなりません。
