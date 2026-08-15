---
name: <context>-<object>
description: >
  <What this router does>
disable-model-invocation: true
---

# <Router Title>

<Explain what this router orchestrates and why a single entry point helps.>

## 役割の境界

- `<route-a>` は <purpose A> を担当する
- `<route-b>` は <purpose B> を担当する
- `<router-name>` 自体は route と handoff を担当し、各 route の詳細手順は持たない

## 実行ルール

1. <Condition for route-a> のときは `<route-a>` へ進む
2. <Condition for route-b> のときは `<route-b>` へ進む
3. route をまたぐ場合でも、親には route 判断だけを残し、詳細な workflow は子へ置く

> 実装上の明示参照としては plugin-qualified 名を使い、実行時の会話では短い呼び出し名で扱うのが自然です。

## 迷ったときの判断

- まず **1 skill = 1 primary purpose** に分解できないかを見る
- それでも 1 入口が必要なら、この router を薄い orchestration として保つ
- 実行ロジックを親へ足したくなったら、child skill へ降ろせないかを先に確認する

## 共通リソース

- `_foundation/` は sub-skill 間で共有する template / convention / quality definition を置く
- `scripts/` は sub-skill から呼ぶ deterministic helper を置く
- `references/` は overflow documentation や必要時の補助資料を置く
