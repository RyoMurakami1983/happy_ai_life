---
name: tauri-sidecar-stability
description: >
  Tauri v2 + Node sidecar の packaged-only failure を、smoke gate・MSI・
  clean Windows validation まで含めて安定化する。Use when:
  `externalBin`、shell capability、`@yao-pkg/pkg` Standard/SEA、enterprise proxy、
  MSI install 後だけ壊れる挙動をまとめて扱いたいとき。
---

# Tauri + Node sidecar の配布安定性を固める

この skill は、**build 成功だけでは見えない packaged-sidecar failure** を先に捕まえるための hot path です。中心になる考え方は、raw CLI と packaged sidecar を同一視せず、`build -> packaged smoke -> MSI -> clean Windows` の順で昇格条件を固定することです。

## こんなときに使う

- Tauri desktop で Node CLI を sidecar として再利用しているとき
- `externalBin`、shell capability、frontend の sidecar 名の整合が不安なとき
- `@yao-pkg/pkg` Standard と SEA のどちらを既定にすべきか判断したいとき
- enterprise proxy / CA 証明書配下で SEA build や MSI build が不安定なとき
- install 後だけ壊れる sidecar 挙動を、build 時点の gate で早めに検出したいとき

## 関連スキル

- `tauri-node-sidecar-windows-distribution` — Node sidecar を Tauri MSI 配布へ組み込む全体像
- `enterprise-rust-tauri-network-build` — 社内 proxy / CA 証明書配下で Rust / Tauri build を通す
- `debug` — 失敗を証拠ベースで再現し、正常系と異常系を比較する

## 前提条件

- sidecar になる Node CLI が単独で実行できる
- Tauri v2 の `externalBin` と shell plugin 基盤がある
- Windows 配布を前提にできる
- build / smoke / install の責務を分離できる

## なぜこの順序が効くか

sidecar 問題は、Node CLI 単体では再現せず **package 後の exe だけで壊れる** ことがあります。Puppeteer の `Function#toString()` 依存、`pkg` / SEA の runtime 差、install 後の working directory 差はその典型です。だから、raw CLI の動作確認より前に packaged-sidecar の比較可能ハーネスを固定したほうが、失敗位置を局所化できます。

## 判断表

| 状況 | まず選ぶ行動 | 次に確認すること |
| --- | --- | --- |
| raw CLI は通るのに desktop 版だけ壊れる | packaged-sidecar smoke を実行する | raw CLI と同じ入力で exe を直接起動できるか |
| `Passed function cannot be serialized!` が出る | bytecode を疑う | `--no-bytecode --public --public-packages "*"` が維持されているか |
| SEA build が proxy 配下で失敗する | runtime prefetch を疑う | `fetch()` に頼らず proxy + checksum で Node runtime を取れるか |
| desktop から sidecar が起動しない | sidecar 契約を点検する | `externalBin`、capability、frontend 呼び出し名が一致しているか |
| MSI 後だけ失敗する | install layout を疑う | payload に exe が入り、install 後の path / cwd 差で壊れていないか |
| clean Windows 検証環境が無い | 代替検証で止める | blocked と promotion gate 未達を明示できているか |

## ワークフロー: packaged-sidecar の安定性を評価する

### ステップ 1 — raw CLI と packaged sidecar の差を前提にする

最初に `node src\index.js` の成功をゴールにしないと決めます。比較対象は次の 2 つです。

1. raw CLI 実行
2. package 後の sidecar exe を直接起動した実行

この差がある前提で、同じ `--demo` や dry-run env を流し、結果を比較できるようにします。

### ステップ 2 — packaged-sidecar smoke gate を作る

smoke gate は、Tauri 経由ではなく **生成済み sidecar exe を直接起動** して確認します。最低限、次を固定します。

- sidecar 実体の絶対パス
- demo / dry-run の env
- 代表レコード到達の確認
- 既知 failure string の fail-fast

パッケージング回帰は「exe が起動したか」ではなく、**代表フローまで壊れず到達したか** で判定します。

### ステップ 3 — Standard と SEA を別 candidate として扱う

`@yao-pkg/pkg` の Standard と SEA は同じ「成功」でも failure mode が違います。Standard は bytecode 有無、SEA は runtime 取得や stock Node 依存が支配的です。だから、mode を切り替えられる build 入口を用意し、**同じ smoke gate に通してから** 比較します。

### ステップ 4 — enterprise proxy / CA は build script に閉じ込める

proxy や CA 証明書は開発者の一時セッションへ散らさず、git config か script から解決します。特に SEA で Node runtime を取得するときは、`fetch()` が proxy をうまく見ないことがあるため、**prefetch + checksum verification** で deterministic にしたほうが再現性が上がります。

### ステップ 5 — MSI payload と install 後検証を分ける

MSI 生成成功は install 後動作の証明ではありません。先に payload に desktop exe と sidecar exe が入っているかを見て、その後で install 後起動を確認します。これで「bundle 設定の欠落」と「install 後 runtime failure」を分けて見られます。

### ステップ 6 — clean Windows validation を昇格条件にする

SEA を既定にしたいなら、local machine の build 成功だけでは足りません。**Node 未導入の clean Windows** で MSI install 後に起動し、sidecar が代表レコードまで到達することを promotion gate にします。環境が無い場合は代替検証をしてもよいですが、その場合は **blocked であること** を曖昧にしません。

## 失敗時の標準切り分け

1. **serialization failure**
   - bytecode を疑う
   - `Function#toString()` 依存ライブラリを疑う
   - Standard mode の flags を確認する

2. **SEA build failure**
   - runtime prefetch の有無
   - proxy / CA
   - `CRYPT_E_NO_REVOCATION_CHECK` の適用条件

3. **desktop から sidecar 起動不可**
   - `externalBin`
   - shell capability
   - frontend 側の sidecar program 名

4. **MSI install 後だけ失敗**
   - payload に exe が入っているか
   - relative path / cwd / resource path
   - install 先で sidecar が直接起動できるか

## 注意点

- **raw CLI の green を release gate にしない**: packaged-sidecar の失敗を見落とします。
- **Standard と SEA を同じ failure mode で語らない**: build 成功でも壊れ方が違います。
- **proxy workaround を常時有効にしない**: enterprise 条件に限定したほうが安全です。
- **clean Windows 検証が無いなら既定昇格しない**: 代替検証済みと promotion 完了は分けて扱います。

## クイックリファレンス

```powershell
npm run build:sidecar
npm run smoke:sidecar
npm run desktop:release-check
npm run desktop:release-check:sea
scripts\desktop.cmd build
```

## 共通リソース

- `tauri-node-sidecar-windows-distribution` — sidecar 配布の全体像
- `enterprise-rust-tauri-network-build` — enterprise ネットワーク配下の build
- [Tauri sidecar guide](https://v2.tauri.app/develop/sidecar/)
- [Tauri Windows installer guide](https://v2.tauri.app/distribute/windows-installer/)
