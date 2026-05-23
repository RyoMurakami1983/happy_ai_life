---
name: design-workshop
description: >
  要求や仕様から技術設計書を組み立てる入口。標準設計と Balanced Coupling レンズ設計を振り分ける。
  Use when: grill-with-docs で要求や仕様が固まり設計を始めたいとき、結合構造を意識した設計がしたいとき、
  実装計画の前に構造とセキュリティを確認したいとき。
---

# Design Workshop

要求や仕様を技術設計書に落とし込み、次の実装契約に渡せる handoff を作るための入口です。設計アプローチに応じて適切な sub_skill に案内します。grill-with-docs の後段に位置します。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

- 仕様が固まり、コンポーネント構造やデータフローを設計したいとき
- MVP で採用する言語・フレームワークを、比較軸つきで選びたいとき
- 実装計画に渡す前に、構造判断を確認したいとき
- 設計判断を実装しやすい形に整えたいとき
- 設計レビューを構造の観点で実施したいとき
- 既存コードの結合構造を意識した設計がしたいとき

## 判断表

| やりたいこと | ルート | 次にやること |
|---|---|---|
| 標準的な設計ワークフローで進めたい（単一リポまたはモノリシック） | `sub_skills/standard/` | 構造判断、MVP 技術選定、設計レビューを行い、implementation handoff を作る |
| 複数リポが関連する、または結合の3次元（統合強度・距離・変動性）を意識した設計がしたい | `sub_skills/balanced-coupling-design/` | マルチリポ環境での context map 作成、サブドメイン分類とバランスルールを使い、モジュラーアーキテクチャを設計する |

**multirepository 判定ガイド**: 以下のいずれかに当てはまる場合は、「複数リポが関連する」と判定し、balanced-coupling-design ルートを検討してください:
- フロントエンド、バックエンド、モバイルなど複数のアプリが存在する
- SDK や shared library など、他リポから参照される
- 独立したマイクロサービスが複数ある
- 複数の開発チームが異なるリポを担当する

## 共通リソース

- `_foundation/README.md` — 共通リソースの説明
- `_foundation/DDD_GLOSSARY.md` — DDD と Balanced Coupling モデルの用語集
- `_foundation/IMPLEMENTATION_HEURISTICS.md` — サブドメイン分類から実装パターンを導く判断ツリー
- `_foundation/TECH_SELECTION_HARNESS.md` — モックの仮選定と MVP の本選定を分ける技術選定ハーネス
- `docs/local_references/balanced-coupling/README.md` — Balanced Coupling モデルの参照ガイド（repo 内ローカル参照。`~/.copilot` 同期環境では開けない）

## ルーティングメモ

- 迷ったら **standard** から始める。結合分析が必要だと分かった時点で balanced-coupling-design に切り替えてもよい。
- Balanced Coupling レンズは全案件の既定ではなく、モジュール分割や境界設計を深掘りしたい場合に選ぶ。
- どちらのルートでも、最終的に `impl-and-ship` へ渡せる implementation handoff summary を出力する。

## 注意点

- **router に実行詳細を書き込まない**: 設計プロセスの詳細は sub_skill に委譲する。
- **2つのルートを混ぜない**: 1つの設計フェーズでは1つのルートを選ぶ。途中での切り替えは、明示的な判断として記録する。

## 関連リソース

- `plugins/happy-coding/skills/grill-with-docs/SKILL.md` — 要求・用語・前提・ADR と照合してから設計に入るとき
- `plugins/happy-coding/skills/prototype/SKILL.md` — 設計前に技術・UI・境界の不確実性を小さく試すとき
- `plugins/happy-coding/skills/modularity-review/SKILL.md` — 既存コードの結合構造分析
