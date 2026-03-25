---
description: Rust 向けの追加ルール
applyTo: "**/*.rs"
---

# Rust instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは Rust の追加ルールだけを定義する。
- 既存の edition、workspace 構成、`rustfmt`、`clippy`、CI ルールを尊重する。
- 不要な `clone` や `copy` を避け、所有権と借用で自然に表現できる形を優先する。
- ライブラリコードでは `panic!` より `Result` を優先し、失敗可能性を型で表現する。
- 文字列や数値の生値を乱用せず、`struct`、`enum`、newtype でドメインを表現する。
- 既存で `anyhow`、`thiserror`、`eyre` 等の方針があればそれに合わせる。
- エラー伝播時は必要に応じて文脈を補う。
- `unsafe` はやむを得ない場合に限定し、不変条件と安全性前提をコメントで明示する。
- iterator combinator は可読性が高い場合に使い、見通しが悪くなるなら明示的なループを選ぶ。
- `pub` を最小限にし、モジュール境界と責務を明確に保つ。