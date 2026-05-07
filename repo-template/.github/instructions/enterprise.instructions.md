---
description: Enterprise Windows build 向けの追加ルール
applyTo: "scripts/**/*.cmd,src-tauri/**/*,package.json,README.md"
---

# Enterprise Windows desktop instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは enterprise ネットワーク下の desktop build に閉じた局所ルールだけを定義する。
- Cargo / Tauri のネットワーク設定は、可能なら git config の `http.proxy`、`https.proxy`、`http.sslCAInfo` を source of truth とし、build script から環境変数へ橋渡しする。
- `CRYPT_E_NO_REVOCATION_CHECK` の回避は proxy が有効な build に限定し、常時グローバル設定にはしない。
- 社内証明書や proxy の個人依存パスをコードへハードコードせず、git config / script / 環境変数から解決する。
- 開発者向け build workflow と一般ユーザー向け install workflow は分けて保ち、`build` と `install` の責務を混ぜない。
