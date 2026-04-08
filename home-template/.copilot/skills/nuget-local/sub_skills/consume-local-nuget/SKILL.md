---
name: consume-local-nuget
description: >
  local feed を利用側 repository に接続し、参照追加から restore/build まで通す。Use when: 作成した nupkg を対象 repository で確認したいとき。
compatibility: "Visual Studio / Package Manager Console, NuGet.Config, packages.config, PackageReference, dotnet msbuild"
---

# ローカル NuGet を使う

local feed を利用側 repository に接続し、参照追加から restore/build まで通すための sub-skill です。pack 側と分ける理由は、こちらの失敗点が NuGet.Config、HintPath、packages.config、PackageReference の整合に集中するからです。trusted repository を前提にし、未確認の repo は sandbox / isolated environment でのみ扱い、restore/build 前に `*.csproj`、`.sln*`、`Directory.Build.*`、`*.props`、`*.targets`、`NuGet.Config`、`packages.config` を確認します。package の追加・更新は command-first で進め、手編集は command で表現できない例外に限ります。

## こんなときに使う

このスキルは次のようなときに使います:
- local feed を user profile か repo-local かで登録したいとき
- 利用側 repository に package を追加して build まで確認したいとき
- `packages.config` と `PackageReference` の restore 方法を切り分けたいとき
- 対象 repository で Debug 起動まで確認したいとき

## ワークフロー: feed を接続して build を通す

### ステップ 1 — feed と参照方法を決める

まず local feed の場所を決めて `NuGet.Config` に登録します。`repo-local` を既定にし、`user profile` 配下を使う場合は一時的な opt-in として扱います。`packages.config` の project なら Visual Studio / Package Manager Console の `Install-Package` で追加し、`nuget.exe restore` で復元します。CLI-only の legacy repo では、追加は direct edit の例外として扱い、`packages.config` と `HintPath` の同期を必要最小限にします。SDK-style の project なら `dotnet add package` -> `dotnet restore` -> `dotnet build` が中心になるため、ここを分けると後続の手順がぶれません。

### ステップ 2 — 利用側 repository で restore/build を確認する

パッケージを追加したら、利用側 repository で restore を通し、次に build を実行します。失敗しやすいのは、feed 登録漏れ、package version の不一致、`HintPath` の古さ、足りない transitive dependency の 4 つです。

## 注意点

- **repo に machine-specific な NuGet.Config を残さない**: 個人の絶対パスは事故の元なので、必要なら repo-local ではなく user profile 配下か明示的なテンプレートに分け、source mapping か一意な package ID で衝突を避けます。
- **restore と build を別々に確認する**: restore が通っても build が壊れることがあるため、両方見るのが安全です。
- **packages.config と PackageReference を混ぜる前提を明示する**: 混在リポジトリでは、どの project がどちらの流儀かを先に固定した方が迷いません。
- **package 管理の手編集を避ける**: version 更新や参照変更は先に command を試し、手編集は不整合補正に限定します。`packages.config` では `HintPath` や `.props` / `.targets` / `NuGet.Config` の同期、またはコマンド後の不整合補正が必要なときだけ direct edit を許可します。

## 早見表

| 消費側の形 | まず使うコマンド |
| --- | --- |
| `packages.config` | Visual Studio / Package Manager Console の `Install-Package` -> `nuget.exe restore` |
| SDK-style / `PackageReference` | `dotnet restore` -> `dotnet build` |

## 関連ルート

- `../pack-local-nuget/` — 使う package を作る側の流れに戻る

## 関連スキル

- `pack-local-nuget` — package を作る流れに戻る

