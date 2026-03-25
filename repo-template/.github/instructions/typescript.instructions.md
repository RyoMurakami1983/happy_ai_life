---
description: TypeScript 向けの追加ルール
applyTo: "**/*.ts,**/*.tsx,**/*.mts,**/*.cts"
---

# TypeScript instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは TypeScript の追加ルールだけを定義する。
- 既存の `tsconfig`、ESLint、Prettier、テスト基盤がある場合はそれを優先する。
- 型安全を優先し、`any` は原則使わない。境界では `unknown` を使い、型を絞り込む。
- export する関数、型、公開 API には明示的な型シグネチャを付ける。
- ルーズなオブジェクトより、`type` / `interface` / 判別可能 union で状態を表現する。
- 非同期処理は `async` / `await` を優先し、例外と失敗系を明示的に扱う。
- `@ts-ignore` や `@ts-expect-error` は最終手段とし、必要なら理由を残す。
- ネットワーク、環境変数、外部 JSON、ファイル入力などの境界では実行時検証を意識する。
- `const` と `readonly` を活用し、意図しない再代入や破壊的変更を減らす。
- テストは既存の framework に合わせ、実装詳細より振る舞いを検証する。