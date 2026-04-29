# .NET 再現可能開発環境の知識配布境界

**日付**: 2026-04-07
**ステータス**: 承認

---

## 背景

この母艦リポジトリは、`.github/` と `home-template/.copilot/` を同期し、複数の repo で同じ開発体験を再現することを目的にしている。  
一方で .NET の再現性は、C# の書き方だけでは成立しない。

主に次の build contract が必要になる。

- `global.json`
- `Directory.Build.props`
- `Directory.Packages.props`
- `.editorconfig`
- `.config/dotnet-tools.json`
- `dotnet build` / `dotnet test` / `dotnet format --verify-no-changes`

現状は `dotnet-shihan` や既存 dotnet skill により品質判断はできるが、`.NET 環境を CLI-first に立ち上げる型` は薄かった。

## 判断

### 1. 第1マイルストーンは知識配布に限定する

今回の最初のマイルストーンでは、強制系の automation より先に、共通の知識と guardrail を配布する。

含めるもの:

- `plugins/happy-ai-life/skills/dotnet-setup-dev-environment/SKILL.md`
- `plugins/happy-ai-life/skills/dotnet/SKILL.md` の router 更新
- `.github/instructions/csharp.instructions.md`
- `repo-template/.github/instructions/csharp.instructions.md`
- この ADR

後続へ回すもの:

- `repo-template/.github/workflows/dotnet-quality.yml`
- `.editorconfig` baseline のテンプレート配布
- hooks や sync script による補助的 enforcement

### 2. build contract は target repo root の責務とする

母艦 root は .NET アプリ本体ではないため、`global.json` や `Directory.Build.props` を母艦自身に置いて正本化しない。  
それらは **target .NET repo の source of truth** として管理する。

### 3. 共通知識は home-template の skill に置く

repo をまたいで再利用したい .NET setup の手順は、現在は plugin package の `plugins/happy-ai-life/skills/` に置く。
ここでは「何をどの順序で整えるか」と「なぜそうするか」を説明し、CLI-first の型を配布する。

### 4. 短い guardrail は path-specific instructions に置く

`.cs` を扱うたびに常時効かせたい短いルールは、`csharp.instructions.md` に置く。

例:

- `dotnet` CLI がある操作は手書きより CLI を優先する
- `global.json` や `Directory.Build.props` を build contract として尊重する
- warning suppress より root cause の修正を優先する

### 5. transport 層は賢くしすぎない

`scripts/sync-to-home.ps1` と `scripts/sync-to-repo.ps1` は配布の transport 層に留める。  
この段階では、`.NET repo なら自動で project file を生成する` ような判断ロジックを持たせない。

## 根拠

- `plugins/happy-ai-life/skills/dotnet/SKILL.md` は、基盤系 skill の追加余地を既に示している
- `python-setup-dev-environment` skill は、環境構築手順を skill として配布する既存パターンになっている
- `csharp.instructions.md` は style と safety を扱っているが、CLI-first の行動規範は未記載だった
- `global.json`、nullable reference types、.NET analyzers、`dotnet format --verify-no-changes` は、いずれも再現性を pass/fail gate に変える一次要素である
- repo-wide と path-specific instructions は併用できるが、競合時は非決定論的なので、ルールの真実は薄く明確に寄せる必要がある

## トレードオフ

- **利点**: 第1マイルストーンの影響範囲を小さく保ちながら、今後の .NET automation の土台を先に作れる
- **利点**: 母艦 root に .NET 固有ファイルを持ち込まず、責務境界を保てる
- **リスク**: knowledge-only なので、CLI-first を完全強制はできない
- **緩和策**: 次のマイルストーンで workflow / hooks / `.editorconfig` baseline を追加し、知識を gate に近づける

## 影響

この判断により、今後の .NET 系追加は次の順で検討する。

1. skill / instructions で型を定義する
2. workflow や `.editorconfig` で gate 化する
3. 必要なら hooks / sync automation で補助する

つまり、**知識 → gate → 補助的 automation** の順で固める。
