---
name: dotnet-setup-dev-environment
description: >
  Use when: dotnet CLI を軸に、再現可能な .NET 開発環境を安全に整えたいとき。
license: Personal
---

# dotnet-setup-dev-environment

`dotnet` CLI を入口にそろえ、SDK・プロジェクト構造・品質ゲートを再現可能な形で整える skill です。
「まず手でファイルを書く」のではなく、「まず CLI と build contract を置く」に寄せます。

## こんなときに使う

- 新しい .NET プロジェクトを `.slnx` 前提で立ち上げたいとき
- 既存の .NET リポジトリを受け取り、build contract を診断したいとき
- `.csproj` や solution を手書きせずに進めたいとき
- `.NET Framework 4.x` と `.NET 5+` の共存有無を見極めたいとき
- `global.json`、`Directory.Build.props`、`.editorconfig` を使って品質の型をそろえたいとき
- `dotnet build` / `dotnet test` / `dotnet format --verify-no-changes` を完了条件にしたいとき

## ワークフロー: .NET 開発環境を整える

### Step 0 — 既存リポジトリを診断する

既存の .NET repo から始める場合は、先に現状を確認します。
repo 全体がまだ読めていないなら、まず `repo-onboarding` で地図を作ってからここに戻ります。

```powershell
dotnet --version
Test-Path global.json
Get-ChildItem -Recurse -Include *.sln, *.slnx, *.csproj
Get-ChildItem -Recurse -Filter *.csproj | Select-String 'TargetFramework|TargetFrameworks|<Project Sdk='
Test-Path Directory.Build.props
Test-Path Directory.Packages.props
Test-Path .editorconfig
Test-Path .config\dotnet-tools.json
dotnet restore
dotnet build --no-restore
```

**判断の目安**

- `global.json` がある → 上書きせず、まず SDK を尊重する
- `.sln` がある → 変更は `dotnet sln migrate` を正規ルートにする
- `.slnx` がある → そのまま標準として扱う
- `net472` や `netstandard2.0` が見える → `dotnet-framework-netstandard-bridge` を開く
- `<Project Sdk=` が無い project がある → SDK-style へ寄せる計画を先に考える

### Step 1 — SDK を固定する

```powershell
dotnet --list-sdks
dotnet new globaljson --sdk-version 9.0.312 --roll-forward latestFeature
dotnet --version
```

`global.json` があると、ローカルと CI で同じ SDK 系列を使いやすくなります。
`roll-forward` は完全固定ではなく、同系列の更新を安全に拾いたいときの逃げ道です。
既存 repo では、新しく作る前に既存の `global.json` を確認し、足りないときだけ追加します。

### Step 2 — solution と project は CLI で作る / 更新する

```powershell
# New repo: .slnx を標準にする
dotnet new sln --name MySolution --format slnx
dotnet new classlib -n MyLibrary -o src\MyLibrary
dotnet new xunit -n MyLibrary.Tests -o tests\MyLibrary.Tests
dotnet sln MySolution.slnx add src\MyLibrary\MyLibrary.csproj
dotnet sln MySolution.slnx add tests\MyLibrary.Tests\MyLibrary.Tests.csproj
dotnet add tests\MyLibrary.Tests\MyLibrary.Tests.csproj reference src\MyLibrary\MyLibrary.csproj

# Existing .sln: 変更前に migrate する
dotnet sln MySolution.sln migrate
```

新しい solution は基本的に `.slnx` を標準にします。
既存の `.sln` を変更するときは、まず `dotnet sln migrate` を通してから進めます。

`.csproj`、`.sln` / `.slnx`、project reference は、対応する `dotnet` コマンドがあるなら CLI を優先します。
SDK の既定値、テンプレート更新、将来の互換性を CLI 側に任せるためです。

> **補足**
> `.sln` と `.slnx` を同じ場所に残すと CLI の自動検出が壊れやすくなります。  
> migrate 後は検証し、問題がなければ旧 `.sln` を残さない運用を基本にします。  
> ただし、ツール互換性や業務上の制約がある場合は既存 `.sln` を維持して構いません。

### Step 3 — solution 全体の build contract を置く

`Directory.Build.props` を repo root に置き、品質ゲートを project ごとに重複させないようにします。
単一の .NET 5+ / .NET 8+ 系 repo なら、まずは次のような最小構成で十分です。

```xml
<Project>
  <PropertyGroup>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <AnalysisLevel>9.0-recommended</AnalysisLevel>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
</Project>
```

`Nullable` と `TreatWarningsAsErrors` が、雑な生成を通さない最小の柵です。
`AnalysisLevel` は `latest` のままにせず固定すると、SDK 更新で警告集合が急に変わりにくくなります。

`netstandard2.0` や `net472` を含む mixed TFM では、同じ設定を無条件で貼らないでください。
その場合は build contract も条件付きに寄せます。

```xml
<Project>
  <PropertyGroup>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>

  <PropertyGroup Condition="'$(TargetFramework)' == 'netstandard2.0'">
    <LangVersion>12.0</LangVersion>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <PropertyGroup Condition="$([MSBuild]::IsTargetFrameworkCompatible('$(TargetFramework)', 'net5.0'))">
    <Nullable>enable</Nullable>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <AnalysisLevel>9.0-recommended</AnalysisLevel>
  </PropertyGroup>
</Project>
```

`netstandard2.0` の共有層をどこに切るか、`net472` をどう隔離するかは `dotnet-framework-netstandard-bridge` の責務です。
Step 0 で mixed TFM を検出したら、ここで深追いせず bridge skill に渡します。

### Step 4 — package と local tool の管理を寄せる

Central Package Management を使う場合は、`Directory.Packages.props` を置きます。

```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <PackageVersion Include="Microsoft.NET.Test.Sdk" Version="17.12.0" />
    <PackageVersion Include="xunit" Version="2.9.3" />
    <PackageVersion Include="xunit.runner.visualstudio" Version="2.8.2" />
  </ItemGroup>
</Project>
```

local tool は manifest で固定します。

```powershell
dotnet new tool-manifest
dotnet tool install dotnet-format
```

追加の analyzer や CLI を入れる場合も、まずは `dotnet tool` か `PackageReference` の正規ルートを使います。
既存 repo で `Directory.Packages.props` があるなら、新しく作らずにそこへ寄せます。

### Step 5 — `.editorconfig` を build contract にする

```powershell
dotnet new editorconfig
```

`.editorconfig` は target repo 側の build contract であり、`dotnet format --verify-no-changes` の正本です。
共有テンプレートから万能な 1 枚を配るより、target repo で生成したものを最小差分で育てます。

- greenfield: `dotnet new editorconfig` を土台にし、repo root の `.editorconfig` を正本にする
- existing repo: 既存 `.editorconfig` を消さず、`dotnet format --verify-no-changes --verbosity diagnostic` で診断してから差分を足す
- `Directory.Build.props`: `TreatWarningsAsErrors`、`AnalysisLevel`、`Nullable`
- `.editorconfig`: formatting と rule severity の明示

```ini
root = true

[*.cs]
dotnet_analyzer_diagnostic.category-Style.severity = warning
dotnet_analyzer_diagnostic.category-Design.severity = warning
dotnet_analyzer_diagnostic.category-Reliability.severity = warning
dotnet_analyzer_diagnostic.category-Performance.severity = warning
dotnet_diagnostic.CS8602.severity = error
dotnet_diagnostic.CS8604.severity = error
dotnet_diagnostic.CS8618.severity = error
```

最初から naming や doc comment の細則まで全部を強制しないほうが安全です。
まずは `dotnet format --verify-no-changes` と null 安全に直結する最小セットを gate にし、追加 analyzer の細則は repo ごとに増やします。
つまり、この skill は `.editorconfig` の考え方を示し、実ファイルの正本は target repo 側に持たせます。

### Step 6 — 日次コマンドを固定する

```powershell
dotnet restore
dotnet build --no-restore
dotnet format --verify-no-changes
dotnet test --no-build
```

この順序にそろえると、依存解決、コンパイル、整形差分、テスト失敗の切り分けがしやすくなります。
警告を見逃したくない repo では、`Directory.Build.props` 側で `TreatWarningsAsErrors` を有効にします。

### Step 7 — 既存 repo には段階導入する

既存コードベースでは、いきなり全部を厳格化しないほうが安全です。

1. Step 0 で現状を診断する
2. 既存 `.sln` があるなら、まず `dotnet sln migrate` を検討する
3. `global.json` を追加または確認する
4. `dotnet restore` / `dotnet build --no-restore` で現状の成功ラインを確認する
5. `Directory.Build.props` を追加し、`Nullable` から寄せる
6. mixed TFM なら条件付き props にし、詳細は bridge skill で詰める
7. `TreatWarningsAsErrors`
8. 既存 `.editorconfig` があれば上書きせず、gate 用の差分を足して `dotnet format --verify-no-changes`
9. `Directory.Packages.props` と local tool manifest

の順で寄せると、どこで破綻したかを追いやすくなります。

## 注意点

- `.csproj`、`.sln` / `.slnx`、`PackageReference` を最初から手書きしない
- 新しい solution は基本的に `.slnx` を使う
- 既存 `.sln` の変更は `dotnet sln migrate` を標準にし、`.sln` と `.slnx` を並べて残さない
- `net472` や `netstandard2.0` が見えたら、modern .NET 単独前提で build contract を貼らない
- `NoWarn` や warning suppress は最後の手段にする
- `Directory.Build.props` と `Directory.Packages.props` は repo root に置く
- `global.json` がある repo では、手元の新しい SDK に勝手に寄せない

## 関連

- `dotnet`
- `repo-onboarding`
- `dotnet-framework-netstandard-bridge`
- `dotnet-modern-csharp-coding-standards`
- `dotnet-slopwatch`
- `git-commit`

## FAQ

**Q: なぜ `.csproj` を手書きしないの？**  
A: SDK テンプレート、target framework、implicit usings、test project の既定値を CLI が正しく持っているからです。人が最初から書くより、`dotnet new` を起点にしたほうが再現性を保ちやすくなります。

**Q: なぜ `.slnx` を標準にするの？**  
A: `.slnx` は XML ベースで差分を読みやすく、CLI でも扱えます。この skill では新規作成の標準として推します。既存 `.sln` を触るときは、まず `dotnet sln migrate` を通すのを正道とします。

**Q: `.sln` を使い続けてはいけないの？**  
A: ツール互換性や業務上の事情で問題があるなら例外扱いにして構いません。ただし、標準は `.slnx` とし、理由がある場合だけ `.sln` を残します。

**Q: `AnalysisLevel` は `latest` ではだめ？**  
A: `latest` は SDK 更新で実体が変わります。再現性を優先するなら、`9.0-recommended` のように固定して、上げるときだけ意図的に更新するほうが安全です。

**Q: `.NET Framework 4.x` と `.NET 5+` を一緒に扱うときは？**  
A: 共有が必要なら `netstandard2.0` を基準にし、setup skill では mixed TFM を検出して `dotnet-framework-netstandard-bridge` に渡します。境界設計そのものは bridge skill の責務です。
