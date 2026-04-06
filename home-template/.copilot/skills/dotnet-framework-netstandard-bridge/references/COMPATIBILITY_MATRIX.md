# Compatibility Matrix

このスキルで扱うのは、「`netstandard2.0` を共有契約として使うと、どの層がどこまで参照できるか」です。

## ざっくり結論

| 層 | 参照できるもの | 参照しないもの |
| --- | --- | --- |
| `netstandard2.0` | BCL の共通部分、契約型、DTO、純粋ロジック | WPF 型、`ConfigurationManager` 直依存、Framework 固有 API |
| `net472` | `netstandard2.0`、Framework 固有 API、旧 SDK | `.NET 8` 専用 API |
| `net8.0+` | `netstandard2.0`、.NET 8 API、DI / Host / WPF 新版 | Framework 固有 API |

## 実務上の目安

### 共有層に置いてよいもの

- `interface`
- `record` / DTO
- enum
- 純粋な変換ロジック
- 設定値を表す型

### 共有層に置かないもの

- WPF / WinForms 型
- `System.Configuration` への強い依存
- ハードウェア SDK の直接呼び出し
- ログ基盤や DI 実装そのもの

## 参照方向

```text
net8.0 UI  ->  netstandard2.0 shared contract  <-  net472 Infrastructure
```

## 典型パターン

1. UI 側が共有契約を参照する
2. Infrastructure 側が契約を実装する
3. 起動時に DI または工場で実装を差し込む
4. 設定値はアプリ起点で読み、共有型へ変換して渡す

## 失敗しやすい点

- 共有層に Framework 固有型を入れてしまう
- DLL 参照のまま放置して、依存方向が不透明になる
- ビルドは通るのに、実行時の型ロードで落ちる
- 設定ファイルのコピー漏れで起動時に失敗する

## 確認観点

- 共有層は `netstandard2.0` でビルドできるか
- UI 側が Infrastructure 実装の詳細を知らないか
- Framework 側が UI 型を逆参照していないか
- 実行時に必要な設定・DLL が出力先へ揃っているか

