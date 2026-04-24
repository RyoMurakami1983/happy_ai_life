# Tauri セットアップの Windows トラブルシュート

## 目次

1. PATH が反映されない
2. `link.exe` が見つからない
3. WiX で MSI 生成が失敗する
4. `tauri:dev` は動くのに build 後は空画面になる
5. ARM Windows で x64 build したい

## 1. PATH が反映されない

Rust 導入直後のシェルでは `cargo` / `rustc` が見つからないことがあります。

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
rustc --version
cargo --version
```

## 2. `link.exe` が見つからない

典型例:

```text
error: linker `link.exe` not found
```

原因は多くの場合、MSVC workload 未導入か、Rust を先に入れたことです。Visual Studio Installer で **Desktop development with C++** を入れたうえで再実行します。

## 3. WiX で MSI 生成が失敗する

```text
error: failed to download WiX
```

アプリ本体の build と MSI installer 生成は分けて判断します。MSI が必要なら WiX Toolset v3 を別途導入し、不要なら `nsis` target へ切り替えます。

## 4. `tauri:dev` は動くのに build 後は空画面になる

- `tauri:dev` は `devUrl`
- `tauri:build` は `beforeBuildCommand` 後の `frontendDist`

`npm run build` を単体で実行し、生成された `index.html` の場所と `tauri.conf.json` の `frontendDist` が一致するか確認します。

Vite で `root` を変えている場合は `outDir` の解決先に注意します。

```typescript
// ❌ root が src/editor のとき、src/editor/dist に出る
outDir: "dist"

// ✅ project root の dist に固定する
import { resolve } from "path";
outDir: resolve(__dirname, "dist");
```

## 5. ARM Windows で x64 build したい

Surface など ARM Windows では既定 target が ARM64 のことがあります。x64 配布が必要なら Rust target を追加して明示します。

```powershell
rustup target add x86_64-pc-windows-msvc
npx tauri build -- --target x86_64-pc-windows-msvc
```
