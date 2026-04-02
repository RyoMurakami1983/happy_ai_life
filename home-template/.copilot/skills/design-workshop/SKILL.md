---
name: design-workshop
description: >
  仕様書から技術設計書を組み立てる入口。標準設計と Balanced Coupling レンズ設計を振り分ける。
  Use when: 仕様が固まり設計を始めたいとき、結合構造を意識した設計がしたいとき、
  実装計画の前に構造とセキュリティを確認したいとき。
compatibility: >
  home-template/.copilot/agents/architect.agent.md,
  home-template/.copilot/agents/security-review.agent.md,
  home-template/.copilot/agents/dotnet-shihan.agent.md,
  home-template/.copilot/agents/python-shihan.agent.md,
  home-template/.copilot/agents/typescript-shihan.agent.md
---

# Design Workshop

仕様書を技術設計書に落とし込むための入口です。設計アプローチに応じて適切な sub_skill に案内します。spec-workshop の後段、planner の前段に位置します。

## こんなときに使う

- 仕様が固まり、コンポーネント構造やデータフローを設計したいとき
- 実装計画（planner）に渡す前に、構造判断とセキュリティ設計を確認したいとき
- architect の設計判断を言語固有の型で検証したいとき
- 設計レビューを構造・セキュリティの両面で実施したいとき
- 既存コードの結合構造を意識した設計がしたいとき

## 判断表

| やりたいこと | ルート | 次にやること |
|---|---|---|
| 標準的な設計ワークフローで進めたい | `sub_skills/standard/` | architect → shihan → security-review → planner handoff の5ステップで設計書を作る |
| 結合の3次元（統合強度・距離・変動性）を意識した設計がしたい | `sub_skills/balanced-coupling-design/` | サブドメイン分類とバランスルールを使い、モジュラーアーキテクチャを設計する |

## 共通リソース

- `_foundation/README.md` — 共通リソースの説明
- `_foundation/DDD_GLOSSARY.md` — DDD と Balanced Coupling モデルの用語集
- `docs/local_references/balanced-coupling/README.md` — Balanced Coupling モデルの参照ガイド

## ルーティングメモ

- 迷ったら **standard** から始める。結合分析が必要だと分かった時点で balanced-coupling-design に切り替えてもよい。
- Balanced Coupling レンズは全案件の既定ではなく、モジュール分割や境界設計を深掘りしたい場合に選ぶ。
- どちらのルートでも、最終的に planner への handoff サマリを出力する。

## 注意点

- **router に実行詳細を書き込まない**: 設計プロセスの詳細は sub_skill に委譲する。
- **2つのルートを混ぜない**: 1つの設計フェーズでは1つのルートを選ぶ。途中での切り替えは、明示的な判断として記録する。

## 関連リソース

- `home-template/.copilot/skills/spec-workshop/SKILL.md` — 前段: 仕様書作成
- `home-template/.copilot/agents/architect.agent.md` — 構造判断の主担当
- `home-template/.copilot/agents/planner.agent.md` — 後段: 実装計画
- `home-template/.copilot/agents/security-review.agent.md` — セキュリティ設計確認
- `home-template/.copilot/skills/sdd/SKILL.md` — 仕様駆動開発の全工程を通すとき
- `home-template/.copilot/skills/modularity-review/SKILL.md` — 既存コードの結合構造分析
