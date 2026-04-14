---
name: sdd
description: >
  仕様駆動開発（Spec-Driven Development）の全工程を1つの入口で進める。
  spec → design → plan → 実装 → eval → レビュー を既存 skill に委譲しながら通す。
  Use when: 仕様駆動で開発を始めたいとき、途中のフェーズから再開したいとき。
---

# SDD — Spec-Driven Development

仕様駆動開発の全工程を1つの入口から進める router skill です。各フェーズの中身は既存の skill に委譲し、この skill 自身はフローの振り分けと接続だけを担います。途中からの再開にも対応し、最も進んだ地点の次から始められます。

## こんなときに使う

このスキルは次のようなときに使います:
- ゼロから仕様駆動で開発を始めたいとき
- 仕様はあるが設計から進めたいとき
- 設計済みで計画と実装に入りたいとき
- 計画があり実装を開始したいとき
- 中断した開発を途中から再開したいとき

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| ゼロから仕様駆動で開発したい | `sub_skills/from-scratch/` | spec-workshop → design-workshop → PLAN mode → 実装 slice → eval gate → レビュー |
| 仕様があり設計から始めたい | `sub_skills/from-spec/` | design-workshop → PLAN mode → 実装 slice → eval gate → レビュー |
| 設計があり計画から始めたい | `sub_skills/from-design/` | PLAN mode → 実装 slice → eval gate → レビュー |
| 計画があり実装から始めたい | `sub_skills/from-plan/` | 計画確認 → contract checkpoint → 実装 slice → eval gate → レビュー |
| 中断した開発を再開したい | `sub_skills/resume/` | 成果物の状態から中断地点を判定し、該当フェーズから再開 |

## 全体フロー

```
仕様フェーズ        → spec-workshop（対話 + 調査）
  ↓
設計フェーズ        → design-workshop（router: standard / balanced-coupling-design）
  ↓                    standard: 構造判断 + 自己レビュー
  ↓                    balanced-coupling-design: サブドメイン分類 + 3次元結合評価
  ↓                    DDD 戦略パターン（Bounded Context, Context Map）は
  ↓                    design-workshop が構造判断として扱う
  ↓
計画フェーズ        → PLAN mode
  ↓
contract checkpoint → slice 単位の done / 非対象 / test 観点を固定
  ↓
実装フェーズ        → オーケストレーター主導 / 必要時は `tdd-coder`
  ↓                    テストファースト、ビルドエラー修正、リファクタリング
  ↓                    セキュリティ境界変更時は中間チェック
  ↓
実装中 eval gate   → `implementation-eval-gate`
  ↓                    PASS: 次の slice へ
  ↓                    FAIL: 実装修正へ戻す
  ↓                    REPLAN_REQUIRED: PLAN mode / design-workshop へ戻す
  ↓
最終レビューフェーズ → 自己レビュー + built-in 機能
```

## セキュリティ checkpoint

セキュリティレビューは2段階で実施します:

1. **設計時**: design-workshop 内で trust boundary と設計方針を確認
2. **実装中（イベント駆動）**: 以下の変更時に中間チェック
   - 認証/認可を追加・変更する
   - 外部入力の入口を増やす
   - 機密データの保存/転送を追加する
   - 外部 API / Webhook / ファイル I/O / コマンド実行を追加する
   - trust boundary をまたぐデータフローを増やす

## 共通リソース

- `home-template/.copilot/skills/spec-workshop/SKILL.md` — 仕様作成
- `home-template/.copilot/skills/design-workshop/SKILL.md` — 技術設計（router: standard / balanced-coupling-design）
- `home-template/.copilot/skills/modularity-review/SKILL.md` — 既存コードの結合構造分析
- `home-template/.copilot/skills/implementation-eval-gate/SKILL.md` — 実装 slice の批判的 gate

## ルーティングメモ

- ユーザーの現在地点に最も合う sub-skill へ直接案内する。
- 実行ロジックは router ではなく sub-skill と既存 skill に置く。
- 各フェーズの中身を sdd 内に再実装しない。委譲先の skill や PLAN mode が正本。
- 計画の正本は PLAN mode の出力または明示的な plan artifact に置く。
- 実装中の評価本文は `implementation-eval-gate` が正本で、`sdd` は順序と戻り先だけを持つ。
- sdd 自体はモデル選定を持たず、入口と接続だけを担う。

## 注意点

- **各段の中身を再実装しない**: sdd はフローを繋ぐだけです。仕様は spec-workshop、設計は design-workshop、計画は PLAN mode または plan artifact が正本です。
- **汎用 coder は置かない**: 実装はオーケストレーター + built-in 機能で担います。
- **eval は別タスクで行う**: generator の自己正当化を避けるため、実装と評価を同じ流れに閉じ込めません。
- **全フェーズを必ず通す必要はない**: 途中から始めてよいし、特定フェーズを飛ばす判断もユーザーに委ねます。
