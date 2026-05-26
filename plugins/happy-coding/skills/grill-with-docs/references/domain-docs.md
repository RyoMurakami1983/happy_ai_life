# Domain Docs Format

`grill-with-docs` が更新する docs の型です。目的は、暗黙知を誰でも使える形式知にしつつ、過剰な文書を増やさないことです。

## CONTEXT.md

`CONTEXT.md` は domain language の用語集です。仕様、設計メモ、実装判断、TODO は入れません。

### 単一 context

```text
/
├── CONTEXT.md
├── docs/
│   ├── grill_results/
│   ├── design/
│   ├── plan/
│   └── adr/
└── src/
```

### 複数 context

```text
/
├── CONTEXT-MAP.md
├── docs/
│   ├── grill_results/
│   ├── design/
│   ├── plan/
│   └── adr/
└── src/
    ├── ordering/
    │   └── CONTEXT.md
    └── billing/
        └── CONTEXT.md
```

### CONTEXT.md の書式

```markdown
# <Context Name>

この context が何を扱い、なぜ独立しているかを 1-2 文で書く。

## Language

**注文 (Order)**:
顧客が購入意思を確定した取引単位。1 つの注文は 1 人の顧客に属し、複数の請求を生む場合がある。
_Avoid_: purchase, transaction

**請求 (Invoice)**:
商品やサービスの提供後に支払いを求める文書。
_Avoid_: bill, payment request

## Flagged ambiguities

- 「account」は顧客とログイン利用者の両方に使われていた。解決: 顧客は **顧客 (Customer)**、ログイン利用者は **利用者 (User)** と呼ぶ。

## Example dialogue

> **Dev:** 顧客が注文した時点で請求を作りますか？
> **Domain expert:** いいえ。請求は出荷が確定した後に作ります。
```

### CONTEXT.md のルール

- 複数の言葉がある場合は canonical term を 1 つ選び、避ける別名を明示する。
- 定義は 1-2 文に抑え、「何であるか」を書く。「どう実装するか」は書かない。
- domain 固有の概念だけを書く。timeout、error type、utility pattern など一般的な技術語は入れない。
- 関係が明らかな場合は cardinality や所有関係を短く書く。
- 曖昧さが残った言葉は `Flagged ambiguities` に解決内容つきで残す。
- 日本語を基本にし、コード識別子や業界で定着した英語は括弧で併記する。

## 進行文書の扱い

- `CONTEXT.md` は用語の正本なので、解決した瞬間に inline で更新する。
- `docs/grill_results/NNN_GRILL_WITH_DOCS_RESULT.md` は grill フェーズ完了時に 1 回だけ保存する。
- `docs/design/NNN_TECHNICAL_DESIGN.md` と `docs/plan/NNN_PLAN.md` は同じ案件番号 `NNN` を共有する。
- ADR は `docs/adr/0001-short-slug.md` の独立連番を使い、判断が確定した時点で作る。

## ADR

ADR は `docs/adr/` に `0001-short-slug.md`、`0002-short-slug.md` のように連番で置きます。directory がなければ、最初の ADR が必要になったときだけ作ります。

### 最小書式

```markdown
# <短い決定名>

<1-3 文で、背景、決定、理由を書く。>
```

### ADR を作る条件

次の 3 条件をすべて満たすときだけ作ります。

1. 戻すコストが意味を持つ
2. 背景なしに読むと驚きがある
3. 実際に代替案とトレードオフがあった

### ADR に向く例

- アーキテクチャ形状: monorepo、event sourcing、service split
- context 間の統合方式: domain event、同期 HTTP、shared database の禁止
- lock-in を伴う技術選定: database、message bus、auth provider、deployment target
- 境界と所有権: 顧客情報は Customer context が所有し、他 context は ID 参照だけにする
- あえて obvious path から外す判断: ORM ではなく manual SQL を選ぶ
- コードから見えない制約: compliance、partner API contract、latency SLO

### ADR にしないもの

- すぐ戻せる設定や一時判断
- obvious な選択
- 実トレードオフがない単なる作業ログ
- `CONTEXT.md` に入れるべき用語定義
