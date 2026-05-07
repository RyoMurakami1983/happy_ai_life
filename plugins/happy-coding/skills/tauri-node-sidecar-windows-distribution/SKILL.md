---
name: tauri-node-sidecar-windows-distribution
description: >
  Tauri v2 と Node.js sidecar を組み合わせて、Windows 向け MSI 配布へ落とし込む。
  Use when: 既存 Node CLI の desktop 化、`pkg` sidecar、`externalBin`、shell plugin、
  MSI 配布、ユーザー向け install script をまとめて扱いたいとき。
---

# Tauri + Node sidecar を Windows 配布する

この skill は、**既存の Node CLI を捨てずに Tauri デスクトップアプリへ包む**ときの hot path です。中心になる考え方は、UI は Tauri、既存処理は sidecar、配布は MSI に分けて、責務を混ぜないことです。

## こんなときに使う

- 既存の Node.js CLI やスクレイパーを desktop app 化したいとき
- フロントを Tauri にしつつ、Node 実行ロジックを再利用したいとき
- `pkg` で sidecar exe を作り、`externalBin` で同梱したいとき
- Windows 一般ユーザー向けに MSI 配布したいとき
- 開発者向け build とエンドユーザー向け install を script で分けたいとき

## 関連スキル

- `enterprise-rust-tauri-network-build` — 社内 proxy / CA 証明書配下で Rust / Tauri build を通す
- `typescript-tauri-setup` — Tauri 初回導入の基本順序を整える

## 前提条件

- 既存の Node CLI が単独実行できる
- Tauri v2 の基本セットアップが済んでいる
- Windows 向け配布を前提にできる
- MSI を作るなら WiX / Tauri bundle が使える

## なぜ sidecar 方式が効くか

Node ロジックを Rust へ書き直すより、まず sidecar に切り出すほうが **既存資産を保ったまま desktop 化** できます。特に Puppeteer、既存 SDK、社内認証周りのように Node 依存が深い処理では、全面移植より sidecar のほうが安全です。

## 判断表

| 状況 | まず選ぶ行動 | 次に確認すること |
| --- | --- | --- |
| 既存 CLI をそのまま再利用したい | sidecar 化する | CLI 入口が引数 / env で駆動できるか |
| Tauri から外部実行したい | shell plugin を使う | capabilities で sidecar 実行許可があるか |
| Windows 配布したい | `bundle.targets = msi` を選ぶ | icon / WiX / externalBin がそろっているか |
| 設定に API トークンがある | Tauri 側で暗号化保存する | sidecar には実行時 env で渡せるか |
| 開発者とユーザーの手順を分けたい | `build` と `install` script を分離する | ダブルクリック UX を誰向けに最適化するか |

## ワークフロー: sidecar 配布を組み立てる

### ステップ 1 — CLI 入口を sidecar 向けに整える

既存の Node CLI を、`require.main === module` で直接実行できる入口と、外部から呼ばれる実装に分けます。最低限そろえるとよいのは次です。

- `--demo` や `--dry-run` のような明示フラグ
- `process.cwd()` 依存を減らす出力先指定
- `.env` 必須ではなく env 注入でも動く構造

### ステップ 2 — sidecar exe を deterministic に作る

```cmd
pkg src\index.js --targets node18-win-x64 --output src-tauri\binaries\my-sidecar-x86_64-pc-windows-msvc.exe
```

ポイントは、**repo 全体ではなく sidecar の entry script だけ** を package 対象にすることです。そうしないと UI 側依存まで巻き込みやすくなります。

### ステップ 3 — Tauri 側へ同梱と実行権限を設定する

- `tauri.conf.json` の `bundle.externalBin`
- `capabilities/default.json` の shell 実行許可
- Rust 側で `tauri-plugin-shell::init()`
- フロントで `Command.sidecar(...)`

ここがそろうと、Tauri UI から sidecar を exe として起動できます。

### ステップ 4 — 設定保存は Tauri 側、実行は sidecar 側に分ける

資格情報は Tauri / Rust 側で暗号化保存し、実行時だけ env で sidecar に渡します。これで Node 側へ平文設定ファイルを常設せずに済みます。

### ステップ 5 — 開発者 build とユーザー install を分離する

おすすめは次の 3 モードです。

1. `setup-build` — Rust / MSVC / Tauri build 前提を整える  
2. `build` — sidecar build → Tauri build → MSI 生成  
3. `install` — MSI を一般ユーザー端末へ入れる  

1 本の `desktop.cmd` にまとめてもよいですが、**引数なしダブルクリックの UX** と **開発者向け build UX** は分けて考えたほうが保守しやすいです。

## 注意点

- **sidecar に UI 依存を持ち込まない**: Tauri frontend のコードまで package 対象にしないほうが安全です。
- **`process.cwd()` 依存を減らす**: インストール後は作業ディレクトリが変わりやすいです。
- **installer と app compile を分けて考える**: exe ができても MSI が失敗することがあります。
- **一般ユーザー向け UX を build script に混ぜない**: `build` と `install` は役割を分けたほうが迷いません。

## クイックリファレンス

```powershell
npm run build:sidecar
npm run desktop:build
Command.sidecar('binaries/my-sidecar', [], { env })
```

## 共通リソース

- [Tauri sidecar guide](https://v2.tauri.app/develop/sidecar/)
- [Tauri Windows installer guide](https://v2.tauri.app/distribute/windows-installer/)
- [pkg](https://github.com/vercel/pkg)
