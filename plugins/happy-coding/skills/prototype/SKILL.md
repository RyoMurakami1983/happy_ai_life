---
name: prototype
description: >
  捨てられる前提の小さな prototype で、実装前の不確実性を短時間で潰す。
  Use when: 技術選定、UI/UX、業務ロジック、外部 API 接続などを本実装前に試したいとき。
license: MIT-derived
---

# Prototype

この skill は、Matt Pocock さんの `prototype` を出発点に、GitHub Copilot CLI、日本語での対話、Happy AI Life の「外科的対応」「基礎と型」「ニュートラル」へ合わせて再設計したものです。
本実装を早めるために、**捨てる前提の試作**で未知を潰します。prototype は成果物ではなく、判断材料です。

## こんなときに使う

- 技術選定やライブラリ選定の前に、実際に動く最小例でリスクを確認したいとき
- UI / UX の導線、状態遷移、入力パターンを短時間で触って確かめたいとき
- 業務ロジックの境界値や例外ケースを、本実装前に小さく検証したいとき
- 外部 API、ファイル I/O、認証、CLI 連携など system boundary の挙動を確認したいとき
- `design-workshop` の判断材料や `impl-and-ship` の実装契約に、実測の根拠を足したいとき

## 判断表

| 状況 | 次にやること |
| --- | --- |
| 用語や要求が曖昧 | 先に `grill-with-docs` で前提を揃える |
| 構造判断や技術選定の不確実性が高い | prototype で小さく検証し、結果を `design-workshop` に渡す |
| 実装契約が十分に固まっている | prototype ではなく `impl-and-ship` に進む |
| prototype が本実装に流用されそう | 境界を明示し、必要なら最初から TDD の production slice に切り替える |

## ワークフロー: 捨てる前提で確かめる

### ステップ 1 — 1 つの問いに絞る

prototype の問いを 1 文で固定します。複数の問いを同時に試すと、成功・失敗の理由が曖昧になります。

```markdown
Prototype Question:
- Can X API return enough data within Y constraint?
- Can this UI state transition be understood without extra explanation?
```

### ステップ 2 — 捨てる境界を固定する

次を先に決めます。

- prototype の保存場所（例: session artifact、temporary branch、`prototype/` など）
- 本実装へコピーしてよいもの / コピーしないもの
- 使ってよい mock と、実際に叩く system boundary
- 最大作業時間

原則として、prototype code は production code へそのまま混ぜません。採用するのは知見、テスト観点、設計判断です。

### ステップ 3 — Logic / UI / Boundary を選ぶ

目的に応じて、prototype の型を 1 つ選びます。

| 型 | 確かめること | 注意 |
| --- | --- | --- |
| Logic prototype | 業務ルール、境界値、アルゴリズム | production 品質の抽象化を始めない |
| UI prototype | 画面導線、状態遷移、文言、操作感 | 見た目の完成度より理解可能性を優先 |
| Boundary prototype | 外部 API、ファイル、認証、CLI、性能 | system boundary の観測結果を残す |

### ステップ 4 — 最小の tracer bullet を動かす

Happy AI Life では、prototype でも vertical slice を優先します。1 つのユーザー行動または 1 つの受け入れ条件を、入口から出口まで細く通します。

- UI だけ、DB だけ、test だけを横に広げない
- 動く最小例で、判断に必要なログ・スクリーンショット・失敗条件を残す
- うまくいかなかった結果も、設計判断の根拠として扱う

### ステップ 5 — 採用 / 不採用 / 再試作を決める

最後に、prototype の結果を実装契約へ渡せる形にまとめます。

```markdown
## Prototype Result
- 問い:
- 試した型: Logic / UI / Boundary
- 観測結果:
- 採用する知見:
- 捨てるコード:
- 残った不確実性:
- 推奨される次工程:
```

## 関連リソース

- `references/origin.md` — 出典、適用範囲、MIT license notice
- `grill-with-docs` — prototype 前に用語・前提を揃える
- `design-workshop` — prototype の観測結果を設計判断へ反映する
- `impl-and-ship` — 実装契約が固まった後、TDD で production slice を進める

## 注意点

- prototype を成果物扱いしない。成果物にするなら `impl-and-ship` で production code として作り直す。
- 時間を区切る。prototype が長引くなら問いが大きすぎます。
- 「動いたから採用」ではなく、制約・失敗条件・捨てた選択肢も記録する。
