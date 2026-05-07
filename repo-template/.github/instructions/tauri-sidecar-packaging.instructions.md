---
description: Tauri + Node sidecar packaging 向けの追加ルール
applyTo: "scripts/build-sidecar.js,scripts/smoke-sidecar.js,scripts/**/*.cmd,src-tauri/**/*,desktop/src/**/*,package.json,README.md"
---

# Tauri sidecar packaging instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは Tauri + Node sidecar の packaging stability に閉じた追加ルールだけを定義する。
- packaged sidecar の変更では、raw CLI 単体成功だけで判定せず、`scripts/smoke-sidecar.js` 相当の **packaged-sidecar gate** を維持する。
- `externalBin`、shell capability、frontend 側の sidecar 呼び出し名は 1 セットで整合させ、どれか 1 つだけ直さない。
- `@yao-pkg/pkg` Standard は既定、SEA は candidate として扱い、同じ smoke gate に通してから比較する。
- `Function#toString()` 依存ライブラリを含む sidecar では、bytecode 有効化を慎重に扱い、source-preserving packaging 要件を崩さない。
- enterprise proxy 配下の SEA は runtime prefetch と checksum verification を前提にし、`CRYPT_E_NO_REVOCATION_CHECK` 系 workaround は proxy 条件に限定する。
- MSI build 成功と install 後起動成功は分けて扱い、payload 確認・install 後起動・clean Windows validation を昇格条件として意識する。
- clean Windows validation が未完了なら、SEA を release default へ昇格した前提で書き換えない。
