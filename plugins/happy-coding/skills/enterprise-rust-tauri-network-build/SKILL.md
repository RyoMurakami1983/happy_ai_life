---
name: enterprise-rust-tauri-network-build
description: >
  会社ネットワーク配下で、git config の proxy / CA 証明書設定を Cargo・Tauri・WiX build へ橋渡ししながら、
  Windows の Rust / Tauri デスクトップビルドを通す。Use when: corporate proxy、custom CA、
  `CRYPT_E_NO_REVOCATION_CHECK`、crates.io 到達失敗、社内証明書環境での Tauri build を扱うとき。
metadata:
  author: Copilot
  tags: [rust, tauri, cargo, windows, proxy, certificate, enterprise]
  invocable: false
---

# Enterprise ネットワーク下で Rust / Tauri をビルドする

この skill は、**会社ネットワーク配下の Windows 端末** で Rust / Cargo / Tauri のビルドを通すための hot path です。重要なのは、proxy や CA 証明書を「どこに書くか」ではなく、**git config にある source of truth を Cargo / Tauri 実行環境へ橋渡しする**ことです。

## こんなときに使う

- `cargo build` や `tauri build` が社内プロキシ配下で失敗するとき
- `CRYPT_E_NO_REVOCATION_CHECK` や crates.io への HTTPS 接続失敗が出るとき
- git config に `http.proxy` や `http.sslCAInfo` はあるが、Cargo が使ってくれないとき
- Rust / Tauri / WiX を Windows で再現可能にセットアップしたいとき
- `scripts\desktop.cmd build` のような統一入口へ社内ネットワーク対策を埋め込みたいとき

## 関連スキル

- `typescript-tauri-setup` — Tauri v2 の初回セットアップ順序をそろえる
- `typescript-setup-dev-environment` — Node.js / npm 側の前提を整える
- `repo-onboarding` — 既存 repo の build/test/重要ファイルを把握する

## 前提条件

- Windows 10 / 11
- Rust / Cargo と MSVC build tools を導入できる
- `winget`、`git`、`npm` が使える
- 社内プロキシまたは企業 CA 証明書が必要なネットワークである

## なぜ git config を橋渡しするか

git は `http.proxy` や `http.sslCAInfo` を読めますが、Cargo や Tauri はそれを自動継承しません。結果として、**git clone は成功するのに crates.io 取得だけ失敗する**状態が起きます。git config を build script 側で読み取り、`CARGO_HTTP_PROXY`、`CARGO_HTTP_CAINFO`、`SSL_CERT_FILE` へ写すと、ネットワーク設定の正本を 1 つに保ったまま Rust 側へ伝えられます。

## 判断表

| 状況 | まず選ぶ行動 | 次に確認すること |
| --- | --- | --- |
| `cargo` が crates.io に接続できない | git config の proxy / CA を確認する | `CARGO_HTTP_PROXY` と `CARGO_HTTP_CAINFO` に橋渡しされているか |
| `CRYPT_E_NO_REVOCATION_CHECK` が出る | proxy 検出時だけ `CARGO_HTTP_CHECK_REVOKE=false` を入れる | 企業ネットワーク固有 workaround として限定されているか |
| git は通るが Cargo だけ失敗する | git config を build script で読む | Cargo が git config を自動継承しないことを前提にする |
| `link.exe` が無い | MSVC を確認する | `vcvars64.bat` 実行後に `cl.exe` が使えるか |
| Tauri compile は通るが MSI で失敗する | WiX / icon / bundle 設定を見る | installer 生成段だけの問題か |

## ワークフロー: enterprise ネットワーク下で build を通す

### ステップ 1 — git config を source of truth として読む

最初に次を確認します。

- `git config --get http.proxy`
- `git config --get https.proxy`
- `git config --get http.sslCAInfo`

環境変数より先に git config を見る理由は、開発者ごとの PowerShell セッション差分を減らし、**持続する設定**を正本にするためです。

### ステップ 2 — Cargo / Tauri へ環境変数として橋渡しする

build と同じプロセスで次をセットします。

```cmd
set HTTP_PROXY=http://proxy.example:8080
set HTTPS_PROXY=http://proxy.example:8080
set CARGO_HTTP_PROXY=http://proxy.example:8080
set CARGO_HTTP_CAINFO=C:\path\to\ca.crt
set SSL_CERT_FILE=C:\path\to\ca.crt
set CARGO_HTTP_CHECK_REVOKE=false
```

`CARGO_HTTP_CHECK_REVOKE=false` は常用設定ではなく、**proxy が有効な社内ネットワークで revocation check に失敗するときだけ** 入れます。

### ステップ 3 — Rust / MSVC / Tauri を同一セッションで確認する

```powershell
rustc --version
cargo --version
npx tauri --version
cmd /c '"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && cl.exe'
```

ここを分けると、PATH が別セッションで失われて「入っているのに見つからない」失敗に見えやすくなります。

### ステップ 4 — sidecar build と Tauri build を一本化する

Node sidecar があるなら、Tauri build の前に deterministic に sidecar を作ります。

```cmd
scripts\desktop.cmd build
```

repo に統一入口が無い場合も、**npm install → sidecar build → tauri build** の順を 1 本の script に閉じ込めます。

### ステップ 5 — 失敗点を network / toolchain / bundle に分離する

- network: crates.io / GitHub release / WiX download で止まる
- toolchain: `cargo`、`rustc`、`cl.exe`、target triple で止まる
- bundle: icon、WiX、MSI 生成、installer metadata で止まる

build を 1 段ずつ局所化すると、社内ネットワーク問題と Tauri 設定ミスを混同せずに済みます。

## 注意点

- **git config を自動継承すると決めつけない**: Cargo は明示的な橋渡しが必要です。
- **revocation check 回避を常時有効にしない**: proxy 検出時だけに限定したほうが安全です。
- **個人パスを手で埋め込まない**: CA 証明書パスは git config や script から取得します。
- **network 問題と bundle 問題を混ぜない**: crates.io 到達後の失敗は icon / WiX / tauri.conf を優先して見ます。

## クイックリファレンス

```powershell
git config --get http.proxy
git config --get http.sslCAInfo
rustup default stable-x86_64-pc-windows-msvc
rustup target add x86_64-pc-windows-msvc
npx tauri --version
scripts\desktop.cmd build
```

## 共通リソース

- [Cargo configuration reference](https://doc.rust-lang.org/cargo/reference/config.html)
- [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/)
- [WiX Toolset v3 releases](https://github.com/wixtoolset/wix3/releases)
