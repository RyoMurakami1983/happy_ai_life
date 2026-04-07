---
description: C# / .NET 向けの追加ルール
applyTo: "**/*.cs"
---

# C# / .NET instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは C# / .NET の追加ルールだけを定義する。
- 既存の target framework、SDK style、EditorConfig、analyzers、nullable context を尊重する。
- `.csproj`、`.sln` / `.slnx`、package reference、project reference は、対応する `dotnet` CLI があるなら手書きより `dotnet new` / `dotnet sln` / `dotnet add` を優先する。
- 新しい solution は基本的に `.slnx` を使い、既存 `.sln` を変更するときは `dotnet sln migrate` を正規ルートにする。問題がある場合だけ例外扱いにする。
- `global.json`、`Directory.Build.props`、`Directory.Packages.props`、`.config/dotnet-tools.json` がある場合は build contract として尊重し、勝手に回避しない。
- Nullable reference types を前提に実装し、null 安全を優先する。`!` は最後の手段にする。
- warning suppress や `NoWarn` の追加で逃げず、analyzer / nullable 警告は根本修正を優先する。
- `async` / `await` を優先し、非同期メソッド名は `Async` 接尾辞を付ける。
- `var` は右辺から型が明白な場合のみ使用し、明白でなければ明示型を使う。
- `IDisposable` / `IAsyncDisposable` は `using` / `await using` で明確に管理する。
- 例外は処理できる場所でのみ catch し、握りつぶさない。
- LINQ は可読性が高い場合に使う。ホットパスでは過剰な連鎖や不要な割り当てを避ける。
- 既存で DI、Options、Logging、Configuration のパターンがある場合はそれに合わせる。
- テストは既存の基盤（xUnit / NUnit / MSTest など）と既存の書き方を尊重し、振る舞いを検証する。
