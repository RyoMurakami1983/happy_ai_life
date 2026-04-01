---
name: deep-research-preflight
description: >
  内部 source of truth と外部の公開知見を集める調査の入口を整え、deep-researcher agent へ渡す。
  Use when: Planner や Architect の前に一次情報確認や現状ベストプラクティス調査を始めたいとき。
license: Personal
compatibility: GitHub Copilot Agent, Claude Code, Codex
---

# Deep Research Preflight

この skill は、調査を始める前の問いの整理、参照元の切り分け、そして深掘り担当への受け渡しを標準化します。  
入口を Skill に寄せる理由は、Planner や Architect から同じ調査手順を再利用しやすくなり、調査の始め方がぶれにくくなるからです。

## こんなときに使う

このスキルは次のようなときに使います:
- Planner や Architect の前に根拠を固めたいとき
- 内部の source of truth と外部の公開知見を照合したいとき
- 事実、推論、未確認事項を分けて整理したいとき

## ワークフロー: Research Handoff

### ステップ 1 — 問いを一文で固定する
何を調べるのか、何を答えれば成功なのかを短く決めます。  
ここで曖昧さを残すと、後続の調査が事実確認と提案で混ざりやすくなります。

### ステップ 2 — source of truth を分ける
内部では README、ADR、instructions、scripts、既存の agent / skill を確認します。  
外部では公式ドキュメント、release notes、公開ベストプラクティスを確認します。  
調査の本文は `deep-researcher` agent に渡し、証拠の収集と照合を進めます。

### ステップ 3 — 事実と推論を分離する
調査結果は、内部で確認できた事実、外部で確認した知見、そこからの推論に分けます。  
未確認事項は無理に埋めず、そのまま残します。

### ステップ 4 — Planner / Architect へ渡す
結論をそのまま実装に流さず、次に必要な判断だけを渡します。  
これにより、計画と構造判断は証拠に基づいて進めやすくなります。

## 判断表

| やりたいこと | 次にやること |
| --- | --- |
| 調査を始めたい | 問いを一文で固定して、内部と外部の source of truth を分ける |
| 調査結果を使いたい | 事実、推論、未確認事項を分けて整理する |
| 計画や構造判断に進みたい | `planner` または `architect` に証拠つきで渡す |

## 注意点

- **Skill だけで深掘りを完結させない**: ここは入口と手順の標準化が役割で、専門的な調査本文は `deep-researcher` agent に任せます。
- **提案を急がない**: 調査の価値は、まず真実を固めることにあります。結論を先に決めるより、証拠を揃える方が後続の判断が安定します。

## 関連スキル

- `deep-researcher` — 内部と外部の証拠を集めて整理する調査エージェント
- `planner` — 調査結果をもとに実行順序を組み立てる
- `architect` — 調査結果をもとに構造判断とトレードオフを整理する
