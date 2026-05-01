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

Windows PowerShell:

```powershell
where gitleaks
```

macOS / Linux:

```bash
which gitleaks
```

何も返らなければ、まず `gitleaks` をインストールしてください。  
https://github.com/gitleaks/gitleaks

**Step 2: 再実行**

```powershell
cd <your-repo>
git commit -m "test message"
```

**Step 3: 必要なら固定**

標準パス以外に入れた場合は `GITLEAKS_BIN` を設定します。

Windows PowerShell（一時）:

```powershell
$env:GITLEAKS_BIN = "C:\path\to\gitleaks.exe"
git commit -m "test message"
```

Windows PowerShell（恒久）:

```powershell
notepad $PROFILE
```

次を追記します。

```powershell
$env:GITLEAKS_BIN = "C:\path\to\gitleaks.exe"
```

読み直し:

```powershell
. $PROFILE
```

macOS / Linux（一時）:

```bash
export GITLEAKS_BIN=/usr/local/bin/gitleaks
git commit -m "test message"
```

macOS / Linux（恒久）:

```bash
export GITLEAKS_BIN=/usr/local/bin/gitleaks
```

その後:

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

### 問題: 古いファイルが残る

**症状**

- 古い skill ファイルが残る
- archive だけ増える

**対処**

- `$HOME/copilot_archive/` を確認
- 競合する古いファイルを手動で整理
- `uv run app.py home` を再実行

## Repo Bootstrap の問題

### 問題: `.github/copilot-instructions.md` が既にある

**症状**

```text
Error: File already exists: .github/copilot-instructions.md
```

**対処**

必要なら先に退避します。

```powershell
mv .github/copilot-instructions.md .github/copilot-instructions.md.bak
```

その後、再実行します。

```powershell
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath .
```

### 問題: bootstrap 後すぐに Git hooks が失敗する

**症状**

- `sync-to-repo.ps1` は通ったのに最初の commit が失敗する

**対処**

```powershell
& $HOME/.copilot/scripts/install-git-hooks.ps1 -RepoPath .
git config core.hooksPath
```

`.githooks` と表示されるか確認してください。

## Plugin の問題

### 問題: marketplace が見つからない

**症状**

```text
Error: marketplace "happy-ai-life-marketplace" not found
```

**対処**

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

### 問題: plugin が重複表示される

**症状**

- 旧 direct install 版と marketplace 版が両方見える

**対処**

```powershell
copilot plugin uninstall happy-ai-life
copilot plugin list
```

## 困ったときの参照先

- [FAQ](FAQ.md)
- [リファレンス](REFERENCE.md)
- GitHub の Issue
