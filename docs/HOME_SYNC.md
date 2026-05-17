# Home Sync（個人環境同期）

Home sync は、この repo の最小 bootstrap 資産を `$HOME/.copilot/` に同期するための仕組みです。

**位置づけ:** 信頼済みのローカル環境を再現するための導線です。共有配布の主導線ではありません。

## home sync とは

`home-template/.copilot/copilot-instructions.md` と、repo bootstrap に必要な一部 script / managed な user-level safety hook entry（正式な enterprise/global guard）をローカルの `$HOME/.copilot/` に反映します。managed entry は `preToolUse` と `permissionRequest` の両方をそろえ、作者用または信頼済み環境の再現に向いています。

管理対象は `$HOME/.copilot/managed-manifest.json` にも出力され、managed file / managed directory / managed entry / user-owned surface の境界を確認できます。

**重要な境界:** repo が管理するファイルだけを更新し、ユーザー所有のファイルは残します。ローカルで運用する安全弁の範囲では user-level guard を最上位とし、この managed entry を全 repository 共通の enterprise/global guard として扱います。enterprise managed policy / device policy を上書きするものではなく、repo ごとの instructions や hooks は補助として扱います。

## 同期されるもの

### 管理対象

- `copilot-instructions.md`
- `managed-manifest.json`
- `repo-template/`
- `scripts/sync-to-repo.ps1`
- `scripts/install-git-hooks.ps1`
- `scripts/repo-secure-check.ps1`
- `scripts/enter-copilot-maintenance-mode.ps1`
- `scripts/exit-copilot-maintenance-mode.ps1`
- `scripts/guard_policy.py`
- `hooks/scripts/guard_pre_tool.ps1`
- `policy/guard-policy.json`
- `policy/guard-policy.schema.json`
- `config.json` の managed な user-level safety hook entry（enterprise/global guard）

### 同期しないもの

- `mcp-config.json`
- `config.json` の user-owned な他設定
- `skills/`、`agents/`、`docs/`
- session data や履歴
- 個人の認証情報や secret

## 使い方

### 前提

- Copilot CLI が入っている
- `uv` が使える
- `$HOME/.copilot/` に書き込める

### 1. repo を取得

```powershell
git clone https://github.com/RyoMurakami1983/happy_ai_life.git
cd happy_ai_life
```

### 2. 変更予定を確認

```powershell
uv sync --dev
uv run app.py home --dry-run
```

何が追加・更新・削除されるかを、反映前に確認できます。

### 3. 反映

```powershell
uv run app.py home
```

実行すると次を行います。

1. `copilot-instructions.md`、repo bootstrap 用 script、shared guard engine、hook script、guard policy を `$HOME/.copilot/` にコピー
2. `managed-manifest.json` をコピーして、管理対象の一覧を見える化
3. 既知の legacy ファイルを整理
4. `config.json` は managed な user-level safety hook entry（enterprise/global guard）だけを更新
5. maintenance mode の入退場 script を `$HOME/.copilot/scripts/` に同期
6. user-owned surface は保持
7. 置き換え前のファイルは `$HOME/copilot_archives/` に退避

### 3.1 ExecutionPolicy migration note

既存の managed entry に `-ExecutionPolicy Bypass` が入っている場合は、次のどちらかで更新します。

```powershell
uv run app.py home
```

一時的に Bypass が必要な端末だけ、環境変数を付けて再同期します。

```powershell
$env:HAPPY_ENV_ALLOW_POLICY_BYPASS = "1"
uv run app.py home
```

環境変数を付けずに再同期すると、managed entry は既定の non-bypass 呼び出しに戻ります。PowerShell 7 / Core host では script をそのまま呼び、Windows PowerShell host でも `pwsh` が見つかればそちらを優先します。

### 4. 確認

```powershell
cat $HOME/.copilot/copilot-instructions.md
cat $HOME/.copilot/managed-manifest.json
copilot status
```

## 戻したいとき

置き換え前のファイルは `$HOME/copilot_archives/` に保存されます。必要なものだけ戻してください。

全体を戻すときの例:

```powershell
Get-ChildItem $HOME/copilot_archives -Recurse | Copy-Item -Destination $HOME/.copilot -Force
```

## 注意

⚠️ **必ず dry-run を先に見る**  
`uv run app.py home` はファイルを置き換えるので、意図した差分か確認してから実行してください。

⚠️ **チーム共有には向かない**  
team repo に配る場合は marketplace install または repo bootstrap を使ってください。

⚠️ **`config.json` は一部だけ更新される**  
`config.json` 全体を上書きするのではなく、managed な user-level safety hook entry（enterprise/global guard）だけを更新し、それ以外の設定は保持します。managed entry は `preToolUse` と `permissionRequest` に 1 件ずつ維持します。

⚠️ **管理対象は manifest で確認する**  
`managed-manifest.json` には、home sync が更新する managed file / managed directory / managed entry と、触らない user-owned path / entry を記録します。review 時は docs だけでなく、この manifest も source of truth として確認してください。

⚠️ **既存 hook id との互換性を維持する**
home sync は `env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"` を持つ既存 entry を同じ managed entry として更新します。managed entry には `env.HAPPY_AI_LIFE_HOOK_EVENT` も付き、`preToolUse` / `permissionRequest` のどちら向けかを script 側へ伝えます。user-owned な他の hook entry や `config.json` の他設定は保持します。

⚠️ **ExecutionPolicy Bypass は既定では入らない**  
企業管理端末の実行ポリシーを尊重するため、managed entry は既定で `-ExecutionPolicy Bypass` を付けません。既定では PowerShell 7 / Core host をそのまま使い、Windows PowerShell host でも `pwsh` があればそちらを優先して `guard_pre_tool.ps1` を実行します。既存ユーザーは home sync を再実行して migration してください。どうしても必要な場合だけ `HAPPY_ENV_ALLOW_POLICY_BYPASS=1` を付けて再同期します。

⚠️ **`skills/` `agents/` `docs/` は触らない**  
これらは plugin install / user-owned surface として扱うため、home sync では作成・更新・削除しません。

## 関連

- [はじめに](GETTING_STARTED.md)
- [Repo Bootstrap（repo 初期導入）](REPO_BOOTSTRAP.md)
