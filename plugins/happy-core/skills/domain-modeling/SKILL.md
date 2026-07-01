---
name: domain-modeling
description: >
  repo 固有の言葉を CONTEXT.md に濃縮し、skill / docs / ADR の用語揺れを減らす。
  Use when: grill-with-docs や authoring 中に domain language、canonical term、避ける別名を整理したいとき。
---

# Domain Modeling

Domain Modeling は、会話や docs に散らばった repo 固有語彙を `CONTEXT.md` に小さく集約する skill です。
目的は仕様や設計を増やすことではなく、AI と人間が同じ言葉で続きの作業を進められる状態にすることです。

## こんなときに使う

- 同じ意味に複数の呼び方がある
- `grill-with-docs` で用語の曖昧さが解けた
- skill / docs / ADR の言葉がずれている
- `PHILOSOPHY.md` の言葉を日常参照用に圧縮したい

## Core Loop

```text
term candidate
  -> source of truth
  -> canonical term
  -> avoid aliases
  -> 1-2 sentence definition
  -> CONTEXT.md patch
```

## 入れるもの

- domain 固有語
- canonical term
- 避ける別名
- 1-2文の定義
- 所有関係や範囲が重要な場合の最小説明

## 入れないもの

- 仕様詳細
- 設計メモ
- 実装方針
- TODO
- 一般的な技術語

## handoff

`CONTEXT.md` を更新したら、次工程へ次を渡します。

- 追加・変更した用語
- 参照した source of truth
- 解決した曖昧さ
- まだ残る Blocking Unknown

## 関連

- `grill-with-docs` — 用語の曖昧さを source of truth と照合する入口
- `copilot-authoring` — skill / agent / instructions へ用語を反映する入口
- `CONTEXT.md` — domain language の正本
