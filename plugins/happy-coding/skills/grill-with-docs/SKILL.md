---
name: grill-with-docs
description: >
  要求・計画・設計・用語を既存ドキュメントとコードに照らして厳しく問い直し、合意した用語や ADR 候補だけを小さく記録する。
  Use when: 実装前に要求や計画を domain language、CONTEXT.md、ADR、既存コードと突き合わせたいとき。
license: MIT-derived
---

# Grill with Docs

この skill は、Matt Pocock さんの `grill-with-docs` を出発点に、GitHub Copilot CLI、日本語での対話、`docs/PHILOSOPHY.md` の「基礎と型」「ニュートラル」「外科的対応」「ドキュメントを学習資産にする」方針へ合わせて再設計したものです。
要求や計画を褒めるのではなく、既存の言葉・コード・ADR と照合して曖昧さを潰し、合意できたものだけを `CONTEXT.md` や ADR に残します。

## こんなときに使う

- 実装前に計画や設計の言葉が既存の domain language と合っているか確認したいとき
- 仕様・設計・依頼文の用語が曖昧で、実装者ごとに解釈が割れそうなとき
- ゼロから要求を立ち上げる、または既存ドラフトの穴を埋めたいとき
- 内部 source of truth と外部公開情報を分け、事実・推論・未確認事項を整理したいとき
- `CONTEXT.md`、`CONTEXT-MAP.md`、`docs/adr/` と計画の矛盾を洗いたいとき
- design-workshop や実装前に、用語と前提を対話で固めたいとき
- 決定を ADR に残すべきか、過剰文書化かを判断したいとき

## 判断表

| 状況 | 次にやること |
| --- | --- |
| 質問の答えがコードや既存 docs から取れる | 先に調査し、証拠を添えて確認する |
| 要求がまだ粗い | 目的・対象・制約・受け入れ条件・非対象を 1 問ずつ確認する |
| 既存ドラフトがある | ドラフトの穴、矛盾、未確認事項を抽出してから補う |
| 外部知見が必要 | 内部 source of truth と外部公開情報を分け、根拠を混ぜない |
| 用語が `CONTEXT.md` と衝突する | 衝突を明示し、正しい意味を 1 問ずつ確認する |
| 用語が曖昧または過負荷 | 推奨する canonical term を提示して確認する |
| 合意した用語が domain 固有 | `CONTEXT.md` / 対応する context の用語へ小さく追記する |
| 決定が戻しにくく、驚きがあり、実トレードオフがある | ADR の作成を提案する |
| 決定が一時的・自明・戻しやすい | ADR 化せず、会話や plan の範囲に留める |

## ワークフロー: docs とコードで計画を grill する

### ステップ 1 — ゴールと source of truth を固定する

まず何を grill するのか、成功条件、確認手段を一文で固定します。ゼロ開始なら目的・対象・制約・受け入れ条件・非対象を最小限で仮置きし、ドラフトありなら穴と矛盾を先に列挙します。次に、今回の根拠として読むものを分けます。

- repo instructions、README、関連 docs
- `CONTEXT-MAP.md`、`CONTEXT.md`
- `docs/adr/`
- 変更対象のコード、既存 test、既存 skill / agent
- 外部の公式 docs、release notes、公開 best practice（必要な場合）
- この repo では必要に応じて `docs/PHILOSOPHY.md`

Why: 最初に根拠を固定しないと、好みの質問や一般論で計画を揺らしやすくなるためです。

### ステップ 2 — 1 問ずつ厳しく確認する

質問は 1 つずつ行い、各質問には推奨回答を添えます。ただし、コードや docs を読めば答えられる質問をユーザーへ投げません。

確認する観点:
- 目的、スコープ、制約、Acceptance Criteria が観測可能か
- その言葉は既存 docs の意味と一致しているか
- 既存コードはユーザーの説明と同じ振る舞いをしているか
- 同じ言葉で別概念を指していないか
- 具体シナリオや境界値で破綻しないか
- 今決めるべきことと、後で決めてよいことが混ざっていないか
- 複数リポが関係する場合、主リポ、依存リポ、provide / require の関係が明示されているか

### ステップ 2a — 事実・推論・未確認事項を分ける

調査を含む場合は、結論を急がずに次を分けて残します。

- **Fact**: repo 内の code / docs / ADR / test、または公式 docs で確認できたこと
- **Inference**: fact から妥当に導けるが、まだ判断を含むこと
- **Unknown**: 調査しても未確認、またはユーザー確認が必要なこと

外部情報は内部 source of truth より優先しません。外部 best practice と repo の既存方針が衝突した場合は、衝突として記録し、設計判断が必要なら `design-workshop` に渡します。

### ステップ 3 — 合意した用語だけを CONTEXT に残す

用語が解決したら、その場で `CONTEXT.md` へ小さく反映します。複数 context がある場合は `CONTEXT-MAP.md` を読み、該当 context の `CONTEXT.md` を更新します。

`CONTEXT.md` は用語集であり、仕様書、設計メモ、実装判断の置き場ではありません。実装詳細は書かず、domain 固有の言葉、避ける別名、関係、曖昧さの解決だけに絞ります。

### ステップ 4 — ADR は少なく、強く残す

ADR は次の 3 条件をすべて満たすときだけ提案します。

1. 後から戻すコストが意味を持つ
2. 背景なしに読むと驚きがある
3. 実際に比較した代替案とトレードオフがある

Why: `docs/PHILOSOPHY.md` の外科的対応に合わせ、知識資産は増やしますが、将来の認知負荷だけ増える文書は作りません。

### ステップ 5 — 次工程へ handoff する

最後に、合意できた用語、残った質問、作成または更新した docs、ADR 候補、次に渡す skill を短く返します。

出力形式:

```markdown
## Grill with Docs Result
- 対象:
- 読んだ source of truth:
- 解決した用語:
- 更新した docs:
- ADR 判断:
- 残った質問:
- 推奨される次工程:
```

## 共通リソース

- `references/domain-docs.md` — `CONTEXT.md` と ADR の Happy AI Life 向け書式
- `references/origin.md` — 出典、適用範囲、MIT license notice
- `prototype` — 実装前の不確実性を短時間で試す
- `design-workshop` — 用語と前提が固まった後の設計
- `impl-and-ship` — 実装契約が固まった後の実装・eval・review・PR
- `modularity-review` — 既存コードの境界をさらに分析したいとき

## 注意点

- すべての質問をユーザーへ投げない。調べれば分かることは先に調べる。
- `CONTEXT.md` を仕様書や設計メモにしない。
- ADR を量産しない。戻しにくさ、驚き、実トレードオフが揃わない判断は残さない。
- grill の勢いで実装に入らない。用語と判断を固めたら、design-workshop / impl-and-ship へ渡す。
