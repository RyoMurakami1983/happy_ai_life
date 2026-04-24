---
name: typescript-tauri-setup
description: >
  TypeScript プロジェクトに Tauri v2 のデスクトップ配布基盤を追加する。
  こんなときに使う: 既存の TypeScript/HTML/CSS アプリを Windows で
  軽量なデスクトップアプリとして動かしたいとき、MSVC・Rust・Tauri CLI の
  導入順序と初回ビルド確認を安全にそろえたいとき。
metadata:
  author: RyoMurakami1983
  tags: [tauri, rust, msvc, desktop, typescript, windows]
  invocable: false
---

# TypeScript 向け Tauri セットアップ

既存の Web フロントエンドを、Windows 上で Tauri v2 デスクトップアプリとして動かすための最短ルートです。親 skill では hot path だけに絞り、長いトラブルシュートや比較表は `references/` に逃がします。

## こんなときに使う

- 既存の TypeScript/HTML/CSS プロジェクトを軽量なデスクトップアプリ化したいとき
- Windows 開発機で Tauri の初回セットアップを再現可能な順序で進めたいとき
- チームメンバーへ「まず何を入れ、どこで詰まりやすいか」を短く渡したいとき
- `link.exe`、WiX、`frontendDist` ずれのような定番トラブルを先回りしたいとき
- Electron より小さい配布物を狙いつつ、TypeScript 主体で進めたいとき

## 関連スキル

- `typescript-setup-dev-environment` — Node.js / npm / TypeScript の前提を先に整える
- `git-initial-setup` — 初回セットアップ変更を安全な branch で進める
- `git-commit-practices` — 依存導入と設定変更を atomic に commit する

## 前提条件

- `typescript-setup-dev-environment` が完了している
- Windows 10/11 と WebView2 runtime が利用できる
- Visual Studio 2022 以降で **Desktop development with C++** workload を入れられる
- Rust crate と npm package を取得できるネットワークがある

## なぜこの順序が効くか

Tauri の初回セットアップは、**MSVC → Rust → Tauri CLI → init → build** の依存鎖です。先に Rust を入れても `link.exe` が無ければ詰まり、`tauri init` だけ先に進めても frontend build と `frontendDist` が噛み合わないと空画面になります。順序を固定して各段で検証すると、失敗位置を局所化できます。

## 判断表

| 状況 | まず選ぶ行動 | 次に確認すること |
| --- | --- | --- |
| 新しい Windows 開発機を立ち上げる | MSVC を先に入れる | `cl.exe` と linker が使えるか |
| 既存 TypeScript プロジェクトへ追加する | `@tauri-apps/cli` と `@tauri-apps/api` を入れる | `npx tauri --version` が通るか |
| `tauri build` が失敗する | `references/windows-troubleshooting.md` を見る | 失敗が PATH / linker / WiX / `frontendDist` のどれか |
| dev は動くが build 後に空画面になる | `tauri.conf.json` の `frontendDist` を点検する | `npm run build` の出力先と一致するか |
| ARM Windows で x64 配布したい | Rust target を追加する | `--target x86_64-pc-windows-msvc` で build できるか |

## ワークフロー: Windows で Tauri を立ち上げる

### ステップ 1: MSVC C++ build tools を先に入れる

Rust の Windows linker は MSVC に依存します。Visual Studio Installer で **Desktop development with C++** workload を有効化し、必要なら次で確認します。

```powershell
& "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
cl.exe
```

### ステップ 2: Rust を入れて PATH を更新する

Rust は Tauri のネイティブ側を build するために必要です。導入直後は同じシェルで PATH を更新して、その場で確認します。

```powershell
winget install Rustlang.Rustup
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
rustc --version
cargo --version
```

### ステップ 3: TypeScript 側へ Tauri CLI と API を追加する

既存プロジェクトのルートで次を実行します。CLI は build/dev 用、API は TypeScript からネイティブ機能を呼ぶための runtime 依存です。

```powershell
npm install --save-dev @tauri-apps/cli
npm install @tauri-apps/api
npx tauri --version
```

### ステップ 4: `tauri init` で土台を作る

`src-tauri/` を生成し、frontend との接続点を埋めます。最低限、次の対応をそろえてください。

- `frontendDist` → build 後の `index.html` がある場所
- `devUrl` → 開発サーバーの URL
- `beforeBuildCommand` → ふつうは `npm run build`
- `bundle.targets` → Windows 配布なら `msi` または `nsis`

```powershell
npx tauri init
```

### ステップ 5: 初回 build で end-to-end を確認する

まず debug build で配線確認をします。初回は Rust 依存の compile で時間がかかります。

```powershell
npx tauri build --debug
```

成功したら、生成物は通常 `src-tauri\target\debug\` 配下に出ます。以後の切り分けは「frontend build は単体で成功するか」「`tauri.conf.json` はその出力先を指しているか」を先に見ます。

## 注意点

- **Rust より先に MSVC を入れる**: `rustc` が入っていても `link.exe` 不足で失敗します。
- **Rust 導入直後は PATH を更新する**: 同じターミナルで続けるなら再起動待ちにしないほうが再現性が高いです。
- **`tauri:dev` と `tauri:build` は参照先が違う**: dev は `devUrl`、build は `frontendDist` を使います。
- **`frontendDist` は `src-tauri/` からの相対パス**: ルート直下の `dist/` なら多くの構成で `../dist` です。
- **MSI に WiX が要ることがある**: アプリ本体の build と installer 生成の失敗は分けて見ると判断しやすいです。

## クイックリファレンス

```powershell
# 1. MSVC workload を Visual Studio Installer で追加

# 2. Rust
winget install Rustlang.Rustup
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
rustc --version

# 3. Tauri
npm install --save-dev @tauri-apps/cli
npm install @tauri-apps/api
npx tauri init
npx tauri build --debug
```

## 共通リソース

- `references/windows-troubleshooting.md` — PATH / linker / WiX / 空画面 / ARM Windows の補助資料
- [Tauri v2 documentation](https://v2.tauri.app/)
- [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/)
- [Rust installation guide](https://www.rust-lang.org/tools/install)
