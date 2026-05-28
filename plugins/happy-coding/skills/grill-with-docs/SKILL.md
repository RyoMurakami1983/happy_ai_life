---
name: grill-with-docs
description: >
  要求・計画・設計・用語を、既存 docs、CONTEXT、ADR、コードに照らして問い直し、実装や設計をブロックする曖昧さだけを解消する。
  Use when: 実装前に domain language、source of truth、未確認事項、ADR 候補を確認し、design-and-plan または implement へ渡せる状態にしたいとき。
---

# Grill with Docs

要求や計画を褒めずに、既存の言葉・コード・ADR と照合します。
目的は「質問を増やすこと」ではなく、次工程をブロックする曖昧さを減らすことです。

Matt Pocock さんの `grill-with-docs` を出発点に、日本語での対話、`CONTEXT.md`、ADR、Happy AI Life の docs 運用へ合わせています。出典と license notice は `references/origin.md` を参照します。

## Core Loop

```text
target
  -> source of truth
  -> Fact / Inference / Blocking Unknown
  -> one question when needed
  -> CONTEXT / ADR decision
  -> handoff
```

## ステップ 1 — 対象と source of truth を固定する

まず何を grill するのか、成功条件、確認手段を 1-2 文で固定します。
次に、今回読む根拠を分けます。

- repo instructions、README、関連 docs
- `CONTEXT-MAP.md`、`CONTEXT.md`
- `docs/adr/`
- 変更対象のコード、既存 test
- 外部公式 docs や release notes（必要な場合）
- この repo では必要に応じて `docs/PHILOSOPHY.md`

コードや docs を読めば答えられることを、ユーザーに聞きません。

## ステップ 2 — Fact / Inference / Blocking Unknown に分ける

調査結果を混ぜずに分類します。

- **Fact**: repo 内の code / docs / ADR / test、または公式 docs で確認できたこと
- **Inference**: fact から妥当に導けるが、判断を含むこと
- **Blocking Unknown**: 次の設計・実装判断を止めている未確認事項

Blocking Unknown だけを質問対象にします。知っておくと便利な程度の疑問は、handoff の残件に回します。

## ステップ 3 — 1 問だけ確認する

質問が必要な場合は、最も上位の Blocking Unknown を 1 つだけ聞きます。
各質問には推奨回答または判断軸を添えます。

確認する観点:

- 目的、スコープ、制約、受け入れ条件が観測可能か
- その言葉は既存 docs の意味と一致しているか
- 既存コードはユーザーの説明と同じ振る舞いをしているか
- 同じ言葉で別概念を指していないか
- 今決めるべきことと、後で決めてよいことが混ざっていないか

2 問続けて詳細に寄ったら、一度だけ鳥の目へ戻り、ゴール、非対象、成功条件、責務境界、影響範囲を見直します。

## ステップ 4 — CONTEXT と ADR を小さく更新する

用語が解決し、domain 固有の言葉なら `CONTEXT.md` に小さく反映します。
複数 context がある場合は `CONTEXT-MAP.md` を読み、該当 context の `CONTEXT.md` だけを更新します。

`CONTEXT.md` に入れるもの:

- canonical term
- 避ける別名
- 1-2 文の定義
- 必要なら所有関係や cardinality
- 解決済みの曖昧さ

`CONTEXT.md` に入れないもの:

- 仕様詳細
- 設計メモ
- 実装方針
- TODO
- 一般的な技術語

ADR は次の 3 条件をすべて満たすときだけ提案します。

1. 後から戻すコストが意味を持つ
2. 背景なしに読むと驚きがある
3. 実際に比較した代替案とトレードオフがある

## ステップ 5 — handoff する

最後に、次工程へ渡せる形でまとめます。
grill 完了時は同じ内容を `docs/grill_results/NNN_GRILL_WITH_DOCS_RESULT.md` に保存します。`NNN` は同じ案件の `design` / `plan` と共有します。

```markdown
## Grill with Docs Result
- 対象:
- 読んだ source of truth:
- Fact:
- Inference:
- 解決した用語:
- 更新した docs:
- ADR 判断:
- Blocking Unknown:
- 推奨される次工程:
```

## 判断表

| 状況 | 次にやること |
| --- | --- |
| 答えがコードや docs から取れる | 先に調査し、証拠を添える |
| 要求が粗い | 目的・対象・制約・受け入れ条件・非対象から最上位の 1 問を聞く |
| 用語が `CONTEXT.md` と衝突する | 衝突を明示し、canonical term を確認する |
| Blocking Unknown がなくなった | design-and-plan または implement へ渡す |
| 判断が戻しにくく、驚きがあり、実トレードオフがある | ADR を提案する |
| 判断が一時的・自明・戻しやすい | ADR 化しない |

## 注意点

- 調べれば分かることを聞かない。
- Blocking Unknown ではない疑問で進行を止めない。
- `CONTEXT.md` を仕様書や設計メモにしない。
- ADR を量産しない。
- grill の勢いで実装に入らない。用語と判断を固めたら `design-and-plan` / `implement` へ渡す。

## 共通リソース

- `references/domain-docs.md` — `CONTEXT.md` と ADR の書式
- `references/GRILL_RESULT_TEMPLATE.md` — grill result の雛形
- `references/origin.md` — 出典と license notice
