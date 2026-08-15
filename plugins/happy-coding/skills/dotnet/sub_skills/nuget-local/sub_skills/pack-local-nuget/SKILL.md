---
name: pack-local-nuget
description: >
  remote repository を clone し、net4x と net5+ の違いを踏まえて release build から nupkg を作る。自作ライブラリを local feed 用に pack したいとき。
---

# ローカル NuGet を pack する

remote repository を clone して Release build から nupkg を作るための sub-skill です。なぜ分けるかというと、pack 側の失敗は build 条件、version、pack target、依存 DLL の置き方に集中するからです。trusted repository を前提にし、未確認の repo は sandbox / isolated environment でのみ clone し、restore/build/pack 前に `*.csproj`、`.sln*`、`Directory.Build.*`、`*.props`、`*.targets`、`NuGet.Config`、`packages.config`、`global.json`、`.config/dotnet-tools.json` を確認します。package の更新は command-first で進め、project file の直接編集は例外に限ります。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

このスキルは次のようなときに使います:
- remote repository から clone して配布用 package を作りたいとき
- `net4x` 系の legacy project と `net5+` 系の SDK-style project を分けて pack したいとき
- Release build の成果物を local feed に置きたいとき
- pack 前に version と assembly metadata を揃えたいとき

## ワークフロー: pack して local feed に置く

### ステップ 1 — project の種類を判定する

まず `packages.config` か SDK-style かを見ます。`net4x` の legacy project は `nuget.exe pack` や `.nuspec` を使う前提になりやすく、`net5+` 以降は `dotnet pack -c Release` が素直だからです。

### ステップ 2 — Release build して package を作る

legacy project では clone 後に restore し、Release build を通してから pack します。SDK-style project では `dotnet pack -c Release -o <local-feed>` を使います。失敗しやすいのは、test project まで pack 対象に入れてしまうこと、version が consumer 側とずれること、依存 DLL が local feed に存在しないことです。

## 注意点

- **machine 固有の出力先を hardcode しない**: repo-local feed を基本にし、共有が必要なときだけ user profile 配下へ切り替え、使い終わったら無効化または削除します。
- **pack できない project を無理に pack しない**: test project や library 以外の project は除外する方が安全です。
- **version と DLL の実体を合わせる**: consumer 側の `HintPath` と nupkg 内の version がずれると、restore 後に build が落ちやすいです。
- **手編集より先にコマンドを試す**: `dotnet pack` / `nuget.exe pack` / `dotnet add package` で表現できるなら、project file は直接いじらない。

## 早見表

| 判定 | 選ぶ手順 |
| --- | --- |
| `packages.config` / legacy csproj | restore 後に Release build、必要なら `nuget.exe pack` を使う |
| SDK-style / net5+ | `dotnet pack -c Release -o <local-feed>` を使う |

## 次の正規ルート

- pack が終わったら `../consume-local-nuget/` へ進み、利用側 repository で restore/build を確認する。

## 関連ルート

- `../consume-local-nuget/` — 作成した package を利用側 repository へ流す

## 関連スキル

- `consume-local-nuget` — pack 後に続ける流れ
