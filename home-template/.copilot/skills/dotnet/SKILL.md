---
name: dotnet
description: >
  .NET 関連の依頼を、適切な C#、WPF、テスト、基盤、文書系 skill へ振り分ける入口。
  Use when: どの .NET skill を使うべきか迷うとき、または今後追加される dotnet skill の起点が必要なとき。
---

# dotnet ルーター

.NET 関連の依頼を 1 つの入口にまとめる薄いルーターです。  
詳細な判断や手順は既存の leaf skill に置き、ここでは「どこへ行くか」だけを決めます。

## こんなときに使う

このスキルは次のようなときに使います:
- C#、WPF、テスト、基盤のどれに振るべきか迷う
- 既存の dotnet skill 名を毎回覚えたくない
- 今後増える dotnet skill の受け口を先に作りたい

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| .NET Framework 4.x と .NET 8+ を netstandard2.0 でつなぎたい | `dotnet-framework-netstandard-bridge` | bridge skill を直接開く |
| 既存の .NET repo を受け取り、solution や build contract を診断したい | `repo-onboarding` / `dotnet-setup-dev-environment` | まず repo を把握し、次に setup skill の Step 0 へ進む |
| モダン C#、型設計、並行処理を整理したい | `dotnet-modern-csharp-coding-standards` / `dotnet-type-design-performance` / `dotnet-csharp-concurrency-patterns` | 該当 skill を直接開く |
| WPF の MVVM や設定、UI まわりを扱いたい | `dotnet-wpf-mvvm-patterns` / `dotnet-wpf-secure-config` | 該当 skill を直接開く |
| 品質ガードレールや slop を見たい | `dotnet-slopwatch` | 既存ルールを確認する |
| プロジェクト構造、設定、パッケージ管理を再現可能に整えたい | `dotnet-setup-dev-environment` | 新規は `.slnx`、既存は Step 0 と `dotnet sln migrate` から始める |
| データ、シリアライズ、EF Core、DB 性能を扱いたい | データ系の skill を curated import してから使う | まずは family router の経路を追加する |
| テストや検証系を扱いたい | テスト系の skill を curated import してから使う | まずは family router の経路を追加する |
| PDF、OCR、業務ワークフローを扱いたい | 文書・業務系の skill を curated import してから使う | 将来の domain router に分ける |

## ルーティングメモ

- ここは薄く保ち、実装手順は leaf skill に置く。
- 既存 skill は壊さず、増える領域だけ後から router 化する。
- 新しい dotnet skill を足すときは、まずこの入口に経路を追加する。
