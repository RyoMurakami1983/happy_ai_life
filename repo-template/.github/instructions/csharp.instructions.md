---
description: C# / .NET 向けの追加ルール
applyTo: "**/*.cs,**/*.csproj,**/*.sln,**/*.slnx,**/Directory.Build.props,**/Directory.Build.targets,**/Directory.Packages.props,**/NuGet.Config,**/packages.config,**/*.props,**/*.targets"
---

# C# / .NET instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは C# / .NET の追加ルールだけを定義する。
- 既存の target framework、SDK style、EditorConfig、analyzers、nullable context を尊重する。
- `.csproj`、`.sln` / `.slnx`、package reference、project reference は、対応する `dotnet` CLI があるなら手書きより `dotnet new` / `dotnet sln` / `dotnet add` を優先する。
- package の追加・更新・削除は command-first とし、`dotnet` / NuGet の標準コマンドで表現できる変更は原則として直接 `.csproj` / `packages.config` / `NuGet.Config` を編集しない。
- ただし legacy project、`HintPath` / `.props` / `.targets` / `NuGet.Config` の同期、依存管理方式の移行、またはコマンド後の不整合補正では direct edit を例外として許可する。
- direct edit を行った場合は、PR に「なぜコマンドでは足りなかったか」と「実行した検証コマンド」を残す。
- 新しい solution は基本的に `.slnx` を使い、既存 `.sln` を変更するときは `dotnet sln migrate` を正規ルートにする。問題がある場合だけ例外扱いにする。
- `global.json`、`Directory.Build.props`、`Directory.Packages.props`、`.config/dotnet-tools.json`、`NuGet.Config` がある場合は build contract として尊重し、勝手に回避しない。
- 未確認の repository では sandbox / isolated environment でのみ `restore` / `build` / `test` / `pack` を行い、実行前に `*.csproj`、`.sln*`、`Directory.Build.*`、`*.props`、`*.targets`、`NuGet.Config`、`packages.config`、`global.json`、`.config/dotnet-tools.json` を確認する。
- Nullable reference types を前提に実装し、null 安全を優先する。`!` は最後の手段にする。
- warning suppress や `NoWarn` の追加で逃げず、analyzer / nullable 警告は根本修正を優先する。
- `async` / `await` を優先し、非同期メソッド名は `Async` 接尾辞を付ける。
- `var` は右辺から型が明白な場合のみ使用し、明白でなければ明示型を使う。
- `IDisposable` / `IAsyncDisposable` は `using` / `await using` で明確に管理する。
- 例外は処理できる場所でのみ catch し、握りつぶさない。
- LINQ は可読性が高い場合に使う。ホットパスでは過剰な連鎖や不要な割り当てを避ける。
- 既存で DI、Options、Logging、Configuration のパターンがある場合はそれに合わせる。
- テストは既存の基盤（xUnit / NUnit / MSTest など）と既存の書き方を尊重し、振る舞いを検証する。
