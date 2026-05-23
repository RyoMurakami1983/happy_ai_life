# トラブルシューティング

## インストール時の問題

### 問題: gitleaks が見つからない

Git hook や `repo-secure-check.ps1` で次のように言われる場合です。

#### 症状

```text
Error: gitleaks is required for the pre-commit secret scan, but it was not found in PATH
```

#### 原因

`gitleaks` の実行ファイルが PATH に入っていません。

#### 対処

**Step 1: gitleaks の場所を確認**

[Windows: PowerShell]

```powershell
where gitleaks
```

[macOS / Linux: bash]

```bash
which gitleaks
```

何も返らなければ、まず `gitleaks` をインストールしてください。  
https://github.com/gitleaks/gitleaks

**Step 2: 再実行**

[Windows: PowerShell]

```powershell
cd <your-repo>
git commit -m "test message"
```

**Step 3: 必要なら固定**

標準パス以外に入れた場合は `GITLEAKS_BIN` を設定します。

[Windows: PowerShell] 一時設定

```powershell
$env:GITLEAKS_BIN = "C:\path\to\gitleaks.exe"
git commit -m "test message"
```

[Windows: PowerShell] 恒久設定

```powershell
notepad $PROFILE
```

次を追記します。

[Windows: PowerShell]

```powershell
$env:GITLEAKS_BIN = "C:\path\to\gitleaks.exe"
```

[Windows: PowerShell] 読み直し

```powershell
. $PROFILE
```

[macOS / Linux: bash] 一時設定

```bash
export GITLEAKS_BIN=/usr/local/bin/gitleaks
git commit -m "test message"
```

[macOS / Linux: bash] 恒久設定

```bash
export GITLEAKS_BIN=/usr/local/bin/gitleaks
```

[macOS / Linux: bash] 読み直し

```bash
source ~/.bashrc
# zsh の場合
source ~/.zshrc
```

## Home Sync の問題

### 問題: 権限エラーで sync できない

**症状**

```text
Error: Access denied when writing to $HOME/.copilot/
```

**対処**

- `$HOME/.copilot/` に書き込み権限があるか確認
- その配下を開いている editor や terminal を閉じる
- 先に `uv run app.py home --dry-run` で差分確認する
- hook の反映先は `settings.json` ではなく `config.json` の `hooks` を確認する
- `config.json` 先頭の `//` コメントは保持されるので、その下の JSON 本体が壊れていないかを見る

### 問題: WSL2 / Linux で bootstrap script が見つからない

**症状**

```text
bash: .../sync-to-repo.sh: No such file or directory
```

**対処**

- 先に `uv run app.py home --no-interactive` で `$HOME/.copilot/scripts/` を更新
- `test -f "$HOME/.copilot/scripts/sync-to-repo.sh"` で配置を確認

### 問題: WSL2 / Linux で rsync または jq が見つからない

**症状**

```text
rsync is required for sync-to-repo.sh on Linux/WSL2.
```

または

```text
必要な依存の一部が不足しています。
```

**対処**

[Ubuntu / WSL2: bash]
```bash
sudo apt update
sudo apt install -y rsync jq
```

`rsync` は `sync-to-repo.sh` / `install-git-hooks.sh` に必要です。
`jq` は bash variant の `guard_pre_tool.sh` が有効な host で必要です。

### 問題: 古いファイルが残る

**症状**

- 古い user-owned ファイルが残る
- archive だけ増える

**対処**

- `skills/`、`agents/`、`docs/` は home sync の管理対象ではないため、残っていても現行仕様です
- 置き換え前の managed file は `$HOME/copilot_archives/` を確認
- 不要な user-owned ファイルだけを手動で整理

## Repo Bootstrap の問題

### 問題: `.github/copilot-instructions.md` が既にある

**症状**

```text
Error: File already exists: .github/copilot-instructions.md
```

**対処**

必要なら先に退避します。

[Windows: PowerShell]

```powershell
mv .github/copilot-instructions.md .github/copilot-instructions.md.bak
```

その後、再実行します。

[Windows: PowerShell]

```powershell
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath .
```

### 問題: bootstrap 後すぐに Git hooks が失敗する

**症状**

- `sync-to-repo.ps1` は通ったのに最初の commit が失敗する

**対処**

[Windows: PowerShell]

```powershell
& $HOME/.copilot/scripts/install-git-hooks.ps1 -TargetRepoPath .
git config core.hooksPath
```

`.githooks` と表示されるか確認してください。

### 問題: `repo-secure-check.sh` で `core.hooksPath` が不足と出る

**症状**

```text
[MISSING] core.hooksPath
```

**原因**

これは、Git に「どの hook を使うか」という置き場所メモがまだ入っていない状態です。  
家のドアはあるのに、どの鍵を使うか札が付いていないイメージです。

**対処**

[Linux / WSL2: bash]

```bash
bash "$HOME/.copilot/scripts/install-git-hooks.sh" -TargetRepoPath .
git config --local --get core.hooksPath
```

母艦 repo では `repo-template/.githooks`、target repo では `.githooks` と表示されれば正常です。

### 問題: `repo-secure-check.sh` で `hook tool dependencies` が不足と出る

**症状**

```text
[MISSING] hook tool dependencies
```

**原因**

hook を動かすための道具が、この PC にまだ足りない状態です。  
たとえば Linux / WSL2 では `jq` がないと、bash 版の safety guard が設定ファイルを読めません。

**対処**

[Linux / WSL2: bash]

```bash
sudo apt update
sudo apt install -y jq
```

`repo-secure-check.sh` の詳細欄に、どの道具が不足しているか表示されます。

## Plugin の問題

### 問題: marketplace が見つからない

**症状**

```text
Error: marketplace "happy-ai-life-marketplace" not found
```

**対処**

[Windows: PowerShell]

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

### 問題: plugin が重複表示される

**症状**

- 旧 direct install 版と marketplace 版が両方見える

**対処**

[Windows: PowerShell]

```powershell
copilot plugin uninstall happy-ai-life
copilot plugin list
```

## 困ったときの参照先

- [はじめに](GETTING_STARTED.md)
- [開発ガイド](DEVELOPMENT.md)
- GitHub の Issue
