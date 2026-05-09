# Home Sync（個人環境同期）

Home sync は、この repo の最小 bootstrap 資産を `$HOME/.copilot/` に同期するための仕組みです。

**位置づけ:** 信頼済みのローカル環境を再現するための導線です。共有配布の主導線ではありません。

## home sync とは

`home-template/.copilot/copilot-instructions.md` と、repo bootstrap に必要な一部 script / managed な user-level safety hook entry をローカルの `$HOME/.copilot/` に反映します。作者用または信頼済み環境の再現に向いています。

**重要な境界:** repo が管理するファイルだけを更新し、ユーザー所有のファイルは残します。安全弁の優先順位は user-level guard を最上位とし、repo ごとの instructions や hooks は補助として扱います。

## 同期されるもの

### 管理対象

- `copilot-instructions.md`
- `repo-template/`
- `scripts/sync-to-repo.ps1`
- `scripts/install-git-hooks.ps1`
- `scripts/repo-secure-check.ps1`
- `hooks/scripts/guard_pre_tool.ps1`
- `config.json` の managed な user-level safety hook entry

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

1. `copilot-instructions.md`、repo bootstrap 用 script、hook script を `$HOME/.copilot/` にコピー
2. 既知の legacy ファイルを整理
3. `config.json` は managed な user-level safety hook entry だけを更新
4. user-owned surface は保持
5. 置き換え前のファイルは `$HOME/copilot_archives/` に退避

### 4. 確認

```powershell
cat $HOME/.copilot/copilot-instructions.md
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
`config.json` 全体を上書きするのではなく、managed な user-level safety hook entry だけを更新し、それ以外の設定は保持します。

⚠️ **`skills/` `agents/` `docs/` は触らない**  
これらは plugin install / user-owned surface として扱うため、home sync では作成・更新・削除しません。

## 関連

- [はじめに](GETTING_STARTED.md)
- [Repo Bootstrap（repo 初期導入）](REPO_BOOTSTRAP.md)
