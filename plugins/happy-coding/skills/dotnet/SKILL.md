---
name: dotnet
description: >
  こんなときに使う: .NET 関連の依頼で、どの leaf に進めばよいか迷うとき。公開入口を
  `dotnet` に集約し、framework bridge、setup、modern C#、並行処理、WPF、
  slopwatch、NuGet の internal sub-skill へ振り分けたいとき。
disable-model-invocation: true
---

# dotnet

この skill は、.NET family の **唯一の公開入口**です。公開一覧を短く保ちつつ、配下の internal sub-skill へ振り分ける family router として動きます。詳細な実装手順は child skill に置き、親は route / handoff に徹します。

## こんなときに使う

- .NET のことならまず `dotnet` から入りたいとき
- framework bridge、setup、modern C#、並行処理、WPF、NuGet のどれへ進むべきか迷うとき
- public skill 一覧を増やさずに .NET family を辿りたいとき

## 役割の境界

- `sub_skills/framework-bridge/` は、.NET Framework 4.x と .NET 8+ の共有境界を扱います。
- `sub_skills/setup/` は、dotnet CLI を軸にした再現可能な .NET 開発環境を扱います。
- `sub_skills/modern-cs/` は、モダン C# の実装・リファクタリングを扱います。
- `sub_skills/type-perf/` は、.NET の型設計と性能判断を扱います。
- `sub_skills/cs-concurrency/` は、.NET の並行処理抽象の選択を扱います。
- `sub_skills/wpf-mvvm/` は、WPF の MVVM 実装を扱います。
- `sub_skills/wpf-secure-config/` は、WPF の安全な設定管理を扱います。
- `sub_skills/slopwatch/` は、.NET の anti-slop 品質ゲートを扱います。
- `sub_skills/nuget-local/` は、ローカル NuGet の pack / consume を扱います。

## 実行ルール

1. 既存 repo の build contract や SDK の診断から始めたい場合は `sub_skills/setup/` へ進みます。
2. .NET Framework と .NET 8+ の橋渡しが主題なら `sub_skills/framework-bridge/` へ進みます。
3. モダン C#、型設計、並行処理は `sub_skills/modern-cs/`、`sub_skills/type-perf/`、`sub_skills/cs-concurrency/` に分けます。
4. WPF の UI / 設定管理は `sub_skills/wpf-mvvm/`、`sub_skills/wpf-secure-config/` に分けます。安全な設定保存が主題なら `wpf-secure-config`、画面分離や command / validation が主題なら `wpf-mvvm` を優先します。
5. 品質ゲートは `sub_skills/slopwatch/`、ローカル NuGet は `sub_skills/nuget-local/` に進みます。

## 迷ったときの判断

- `.NET のことならまず dotnet` を入口にします。
- 初手が build / restore / solution / SDK なら `setup` に寄せます。
- leaf 名だけで迷う場合は、親文脈が補う前提で child へ直接入らず、この router の判断表から進みます。

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| .NET Framework 4.x と .NET 8+ を netstandard2.0 でつなぎたい | `sub_skills/framework-bridge/` | bridge 境界と参照方向を決める |
| 既存 .NET repo を診断し、再現可能な build contract を整えたい | `sub_skills/setup/` | Step 0 から SDK / solution / props を確認する |
| モダン C# の実装や設計を整理したい | `sub_skills/modern-cs/` | C# 12+ のイディオムと Result 型を確認する |
| 型設計と性能の両立を見たい | `sub_skills/type-perf/` | class / struct / record と allocation を確認する |
| 並行処理の抽象を選びたい | `sub_skills/cs-concurrency/` | async/await、Channels、Actors を比較する |
| WPF の MVVM を整えたい | `sub_skills/wpf-mvvm/` | ViewModel-first の分離へ進む |
| WPF の安全な設定管理を入れたい | `sub_skills/wpf-secure-config/` | DPAPI を使った設定保存へ進む |
| WPF 設定画面で secure storage と MVVM の両方が絡む | `sub_skills/wpf-secure-config/` を先に選ぶ | secure storage を先に固定し、画面分離は child 側の関連 skill から辿る |
| .NET の anti-slop 品質ゲートを見たい | `sub_skills/slopwatch/` | rule と enforcement を確認する |
| ローカル NuGet を pack / consume したい | `sub_skills/nuget-local/` | pack 側か consume 側かを切り分ける |

## 共通リソース

- `sub_skills/` — .NET family の internal sub-skill
- `../repo-onboarding/` — repo 全体の入口がまだ曖昧な場合

## 注意点

- ここに child の詳細手順を複製しないでください。
- public skill 一覧に dotnet leaf を並べ直さず、公開入口は `dotnet` に集約します。
- `disable-model-invocation: true` は route / handoff の意図であり、可視性制御の保証には使いません。
