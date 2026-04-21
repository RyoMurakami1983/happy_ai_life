---
name: sdd
description: >
  仕様駆動開発の前半工程（spec → design → plan handoff）を1つの入口で進める。
  途中の spec / design / planning フェーズからも再開できる。
  Use when: 仕様駆動で開発を始めたいとき、途中のフェーズから再開したいとき。
---

# SDD — Spec-Driven Development

仕様駆動開発の前半工程（spec → design → plan）を1つの入口から進める router skill です。各フェーズの中身は既存の skill に委譲し、この skill 自身はフローの振り分けと接続だけを担います。plan が完成したら `impl-and-ship` へ引き継ぎます。途中からの再開にも対応し、最も進んだ地点の次から始められます。

## こんなときに使う

このスキルは次のようなときに使います:
- ゼロから仕様駆動で開発を始めたいとき
- 仕様はあるが設計から進めたいとき
- 設計済みで計画フェーズに入りたいとき
- 中断した spec / design / planning を途中から再開したいとき

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| ゼロから仕様駆動で開発したい | `sub_skills/from-scratch/` | spec-workshop → design-workshop → PLAN mode → impl-and-ship へ handoff |
| 仕様があり設計から始めたい | `sub_skills/from-spec/` | design-workshop → PLAN mode → impl-and-ship へ handoff |
| 設計があり計画から始めたい | `sub_skills/from-design/` | PLAN mode → impl-and-ship へ handoff |
| 計画があり実装から始めたい | `impl-and-ship` を直接使う | bootstrap 確認 → contract checkpoint → 実装 slice → eval gate → review → PR |
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
                    ＊ここで sdd の責務は終わり ＊
                    → impl-and-ship（実装・eval・review・furikaeri・PR の後半サイクル）
```

## セキュリティ checkpoint（設計時）

設計フェーズでは design-workshop 内で trust boundary と設計方針を確認します。実装中のセキュリティ checkpoint は `impl-and-ship` が担います。

## 共通リソース

- `home-template/.copilot/skills/spec-workshop/SKILL.md` — 仕様作成
- `home-template/.copilot/skills/design-workshop/SKILL.md` — 技術設計（router: standard / balanced-coupling-design）
- `home-template/.copilot/skills/modularity-review/SKILL.md` — 既存コードの結合構造分析
- `home-template/.copilot/skills/impl-and-ship/SKILL.md` — 実装・eval・review・PR の後半サイクル
- `references/interactive-app-bootstrap-checklist.md` — interactive app pilot の実装前前提
- `references/interactive-app-comparable-harness-contract.md` — interactive app pilot の比較前提

## ルーティングメモ

- ユーザーの現在地点に最も合う sub-skill へ直接案内する。
- 実行ロジックは router ではなく sub-skill と既存 skill に置く。
- 各フェーズの中身を sdd 内に再実装しない。委譲先の skill や PLAN mode が正本。
- 計画の正本は PLAN mode の出力または明示的な plan artifact に置く。
- sdd 自体はモデル選定を持たず、入口と接続だけを担う。
- plan handoff が完成したら、実装の入口は `impl-and-ship` に委譲する。

## multirepository 環境での handoff

複数リポが関連する場合、plan handoff は以下の形式で各リポごとに作成してください：

- **複数リポ構成の確認**: from-scratch ステップ 0.5 または from-spec ステップ 0 で multirepository 判定が行われます。
- **設計フェーズでの分割**: design-workshop で balanced-coupling-design ルート（context map + bounded context 分類）を選択し、リポ境界に沿った設計書を作成します。
- **PLAN mode への受け渡し**: 複数リポの場合、各リポに対応する plan artifact を作成するか、統合 plan 上で「リポ間の依存関係と実装順序」を明記してください。`impl-and-ship` がリポごとの並列実装や順序制御を行います。

## 注意点

- **各段の中身を再実装しない**: sdd はフローを繋ぐだけです。仕様は spec-workshop、設計は design-workshop、計画は PLAN mode または plan artifact が正本です。
- **実装フェーズは sdd に持ち込まない**: plan handoff 完了後は `impl-and-ship` が正本です。
- **全フェーズを必ず通す必要はない**: 途中から始めてよいし、特定フェーズを飛ばす判断もユーザーに委ねます。
