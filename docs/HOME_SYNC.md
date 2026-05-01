# Home Sync（個人環境同期）

Home sync は、この repo の `home-template/` を `$HOME/.copilot/` に同期するための仕組みです。

**位置づけ:** 信頼済みのローカル環境を再現するための導線です。共有配布の主導線ではありません。

## home sync とは

`home-template/.copilot/` にある curated skills、agents、設定、repo bootstrap 用テンプレートをローカルの `$HOME/.copilot/` に反映します。作者用または信頼済み環境の再現に向いています。

**重要な境界:** repo が管理するファイルだけを更新し、ユーザー所有のファイルは残します。

## 同期されるもの

### 管理対象

- `skills/` 配下の curated skills
- `agents/` 配下の curated agents
- `copilot-instructions.md`
- `repo-template/`
- `scripts/` や `.githooks/` などの補助資産
- `mcp-config.sample.json` などの sample

### 同期しないもの

- `mcp-config.json`
- `config.json`
- ローカルで自作した skills / agents
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

1. 管理対象ファイルを `$HOME/.copilot/` にコピー
2. 既知の legacy ファイルを整理
3. ユーザー所有ファイルは保持
4. 置き換え前のファイルは `$HOME/copilot_archive/` に退避

### 4. 確認

```powershell
cat $HOME/.copilot/copilot-instructions.md
copilot status
```

## 戻したいとき

置き換え前のファイルは `$HOME/copilot_archive/` に保存されます。必要なものだけ戻してください。

全体を戻すときの例:

```powershell
Get-ChildItem $HOME/copilot_archive -Recurse | Copy-Item -Destination $HOME/.copilot -Force
```

## 注意

⚠️ **必ず dry-run を先に見る**  
`uv run app.py home` はファイルを置き換えるので、意図した差分か確認してから実行してください。

⚠️ **チーム共有には向かない**  
team repo に配る場合は marketplace install または repo bootstrap を使ってください。

⚠️ **同名ファイルは上書きされる**  
ユーザー所有ファイルは基本残りますが、管理対象と同名なら管理側が優先されます。

## 関連

- [はじめに](GETTING_STARTED.md)
- [Repo Bootstrap（repo 初期導入）](REPO_BOOTSTRAP.md)
