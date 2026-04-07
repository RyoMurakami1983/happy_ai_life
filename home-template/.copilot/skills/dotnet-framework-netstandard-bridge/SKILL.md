---
name: dotnet-framework-netstandard-bridge
description: >
  .NET Framework 4.x のレガシー層と .NET 8+ の UI/アプリ層を netstandard2.0 の共有層でつなぐ。
  Use when: 既存の .NET Framework 依存を残しつつ UI やアプリ本体を .NET 8 へ段階移行したいとき、
  または共有境界をどこに置くべきか判断したいとき。
compatibility: ".NET Framework 4.7.2+, .NET Standard 2.0, .NET 8+"
---

# .NET Framework × .NET Standard 2.0 ブリッジ

レガシーな .NET Framework 資産を捨てずに、.NET 8+ のアプリ層へ段階移行するための判断と実装をまとめるスキルです。  
このスキルの主役は「どこを `netstandard2.0` に切るか」であり、互換性のある共有境界を薄く保つことです。

## こんなときに使う

このスキルは次のようなときに使います:
- .NET Framework 4.x の Infrastructure を残したまま UI だけ .NET 8 へ上げたい
- ハードウェア SDK や旧 API が .NET Framework に縛られている
- 共有層を `netstandard2.0` に切るべきか、DLL 参照でしのぐべきか迷っている
- 段階移行の境界、参照方向、設定読み込みの分離を整理したい

## このスキルで扱わないもの

- いきなりの完全書き換え
- IPC / 別プロセス化そのものの詳細設計
- WPF 固有の MVVM 実装手順
- `global.json`、`.slnx`、既存 repo の build contract 診断。まずは `dotnet-setup-dev-environment` を使う

## 基本原則

1. **共有契約を先に切る** — 型、DTO、インターフェース、設定モデルを `netstandard2.0` に寄せる。
2. **レガシー実装は隔離する** — Framework 依存は Infrastructure 側に閉じ込める。UI へ漏らさない。
3. **参照方向を一方通行にする** — .NET 8 側は共有層を参照し、Framework 側は共有契約を実装する。
4. **薄いブリッジに保つ** — 共有層はロジックを盛りすぎない。捨てやすさを残す。
5. **設定・I/O を境界で吸収する** — `ConfigurationManager` やファイル読み込みはアプリ起点に寄せる。

> **Values**: 温故知新 — 既存の .NET Framework 資産を活かしながら、移行コストを分割する。

## ワークフロー: ブリッジ境界を作る

### Step 1: 依存境界を棚卸しする

まず、Framework 固有の API、WPF 固有の型、設定読み込み、ハードウェア接続を洗い出します。  
ここで `netstandard2.0` に移せるものと、残すべきものを分けます。

**判断の目安**
- 移せる: DTO、インターフェース、列挙型、入力検証用の純粋ロジック
- 残す: UI 実装、Framework 固有 API、ドライバやベンダー SDK 呼び出し

> **Values**: 基礎と型 — 先に境界を決めると、後の移行が実装論ではなく構造論になる。

### Step 2: `netstandard2.0` の共有層を作る

共有層には、双方が必要とする契約だけを置きます。  
まずは `interface`、設定モデル、軽い DTO、例外型、enum から始めます。

```csharp
public interface IDeviceReader
{
    string ReadStatus();
}

public sealed record DeviceSettings(string PortName, int TimeoutMs);
```

**重要ルール**
- Framework 専用 API を置かない
- `System.Configuration` や WPF 型を持ち込まない
- 共有層は「契約」と「純粋な型」に寄せる

> **Values**: 余白の設計 — 共有層を薄く保つほど、後で別ホスト化しても壊しにくい。

### Step 3: Framework 側を契約実装に寄せる

`net472` 側は共有契約を実装するだけに寄せ、上位層へ Framework 依存を漏らさないようにします。  
必要ならアダプタを挟み、UI へ返す型を共有層の型に揃えます。

```csharp
public sealed class DeviceReader : IDeviceReader
{
    public string ReadStatus()
    {
        // NI API や旧 SDK をここに閉じ込める
        return "OK";
    }
}
```

**重要ルール**
- 旧 API 呼び出しは実装クラスに閉じる
- UI へは共有型だけ返す
- 例外や失敗は契約の外形に合わせて整える

### Step 4: .NET 8 側から共有層だけを参照する

.NET 8 側は共有層を中心に組み立て、Framework 実装は差し替え可能な依存として扱います。  
この時点で、UI は「何が背後で動いているか」を知らなくてよくなります。

**実務の目安**
- WPF / WinForms / Console / Worker など、.NET 8 側を先に上げる
- 共有層を通じてだけ値を受け渡す
- 設定初期化は起動時にまとめる

> **Values**: ニュートラルな視点 — UI は UI の仕事だけを持ち、実装方式の違いは境界の内側に隠す。

### Step 5: 破綻しやすい点を確認する

移行後は、参照の向き、設定コピー、ビルド出力、ランタイムのロード失敗を確認します。  
「コンパイルは通るが起動しない」系の問題が出やすいので、実行確認までをセットにします。

## 注意点

- **共有層を肥大化させない**: 便利だからといってロジックを増やすと、後で切り離せなくなる。
- **Framework 型を漏らさない**: `netstandard2.0` に置けない型を共有契約に混ぜると、境界が崩れる。
- **DLL 参照を永続解にしない**: 一時的な橋としては有効でも、長期的には参照構造を明確にする。
- **設定の読み取り場所を固定しない**: アプリ起点に寄せて、共有層は設定値だけを受け取る。

## 早見表

| 置き場所 | 役割 |
| --- | --- |
| `netstandard2.0` | 共有契約、DTO、設定モデル、純粋ロジック |
| `net472` | 旧 API、NI / ベンダー SDK、実装アダプタ |
| `net8.0+` | UI、起動、DI、アプリ全体のオーケストレーション / ブリッジの呼び出し元 |

## Related Skills

- `dotnet` — .NET 系の入口
- `dotnet-setup-dev-environment` — 既存 repo 診断と build contract の入口
- `dotnet-modern-csharp-coding-standards` — 共有型や契約型をどう表現するか
