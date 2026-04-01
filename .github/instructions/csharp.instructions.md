---
description: C# / .NET 向けの追加ルール
applyTo: "**/*.cs"
---

# C# / .NET instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは C# / .NET の追加ルールだけを定義する。
- 既存の target framework、SDK style、EditorConfig、analyzers、nullable context を尊重する。
- Nullable reference types を前提に実装し、null 安全を優先する。`!` は最後の手段にする。
- `async` / `await` を優先し、非同期メソッド名は `Async` 接尾辞を付ける。
- `var` は右辺から型が明白な場合のみ使用し、明白でなければ明示型を使う。
- `IDisposable` / `IAsyncDisposable` は `using` / `await using` で明確に管理する。
- 例外は処理できる場所でのみ catch し、握りつぶさない。
- LINQ は可読性が高い場合に使う。ホットパスでは過剰な連鎖や不要な割り当てを避ける。
- 既存で DI、Options、Logging、Configuration のパターンがある場合はそれに合わせる。
- テストは既存の基盤（xUnit / NUnit / MSTest など）と既存の書き方を尊重し、振る舞いを検証する。