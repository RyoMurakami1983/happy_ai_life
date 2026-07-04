---
name: interview-with-docs

description: 計画やデザインを研ぎ澄ませるための統合スキル。`happy-core@interview-me` で問いを深め、`happy-coding@domain-modeling` で用語と文脈を整理する。

disable-model-invocation: true

---

この skill は、`happy-core@interview-me` と `happy-coding@domain-modeling` を順に組み合わせて使うためのオーケストレーションです。目的は、要件の深掘りと、用語・文脈の整理を一連の会話で進めることです。

## 役割の境界

- `happy-core@interview-me` は「問いを深める」役割です。
- `happy-coding@domain-modeling` は「用語と概念を整理する」役割です。
- `interview-with-docs` は、その両方を一つのセッションで運ぶ役割です。

## 実行ルール

1. まず `/interview-me` で、目的・役割・例外・失敗・実務ルールを引き出します。
2. 次に `/domain-modeling` で、引き出した内容から用語・定義・境界を整理します。
3. その結果を、必要に応じて `CONTEXT.md` や ADR へ反映します。

> 実装上の明示参照としては `happy-core@interview-me` / `happy-coding@domain-modeling` を使い、実行時の会話では `/interview-me` / `/domain-modeling` で扱うのが自然です。

## 迷ったときの判断

- 深掘りが足りないなら、先に `/interview-me` に戻ります。
- 用語が曖昧なら、`/domain-modeling` で整えます。
- どちらも不要で、すでに合意が取れているなら、次工程へ進みます。