---
name: nuget-local
description: >
  ローカルで自作 NuGet の pack と consume を切り分けて案内する。Use when: remote repository から clone し、release build で nupkg 化して local feed に置き、利用側 repository で参照追加と build 確認まで進めたいとき。
---

# ローカル NuGet ワークフロー

remote repository から自作 NuGet を作り、local feed に置き、利用側 repository で参照追加と build 確認まで通す流れを 1 つの入口にまとめる router です。pack 側と consume 側を分ける理由は、失敗点と前提が違うためです。trusted repository を前提にし、未確認の repo は clone 後も sandbox / isolated environment でのみ扱い、restore/build/pack 前に `*.csproj`、`.sln*`、`Directory.Build.*`、`*.props`、`*.targets`、`NuGet.Config`、`packages.config`、`global.json`、`.config/dotnet-tools.json` を確認します。package 管理は command-first で進め、手編集は command で表現できない例外に限ります。

## こんなときに使う

このスキルは次のようなときに使います:
- remote repository を clone して nupkg を作る手順を整理したいとき
- `dotnet pack` と `nuget.exe pack` の使い分けを決めたいとき
- local feed を repo-local 既定で置き分け、必要時だけ user profile を opt-in したいとき
- 利用側 repository へ feed を追加して build まで確認したいとき
- パッケージ作成と利用確認を別々に切り分けて debug したいとき

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| remote repository から release build して nupkg を作る | `sub_skills/pack-local-nuget/` | clone、restore、version 調整、pack、local feed 配置まで進める。 |
| local feed を利用側 repository に接続して build まで確認する | `sub_skills/consume-local-nuget/` | NuGet.Config、参照追加、restore、Debug/Release build の順で確認する。 |

## ルーティングメモ

- ユーザーの現在地点に最も合う sub-skill へ直接案内する。
- 実行ロジックは router ではなく sub-skill や script に置く。
- 用語は相手の literacy に合わせ、必要なら専門語を説明する。

## 関連ルート

- `sub_skills/pack-local-nuget/` — remote repository から package を作る側
- `sub_skills/consume-local-nuget/` — local feed を利用側 repository で使う側

## 関連スキル

- `pack-local-nuget` — package を作る流れ
- `consume-local-nuget` — package を使う流れ

## 注意点

- **pack と consume を同じ手順に混ぜない**: 失敗時の原因が見えにくくなるため、まずはどちらの側かを切り分けます。
- **machine 固有の feed を前提にしない**: repo-local feed を基本にし、必要な場合だけ user profile 配下を opt-in にし、使い終わったら無効化または削除します。
- **評価は構造と効果で分ける**: まず `skill/validate` で形を確認し、必要なときだけ `skill/evaluate` で振る舞いを比べます。
- **project file の手編集を先にしない**: version 変更や package 追加は先に `dotnet` / NuGet のコマンドで試し、手編集は例外として使います。
