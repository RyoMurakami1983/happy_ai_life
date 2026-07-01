# はじめに

用途に合わせて導入方法を選んでください。
迷ったら、README の「迷ったらこれだけ」から次の 3 パスを選んでください。

## パス 1: 通常利用（Marketplace Plugin）

**向いている人:** この repo を編集せずに、happy-core と happy-coding を自分の作業で使いたい人。

### インストール

まず marketplace を追加します。

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
```

次に plugin を入れます。

```powershell
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

### 確認

```powershell
copilot plugin list
```

`happy-core` と `happy-coding` が表示されれば完了です。

### 入るもの

- **happy-core**: workflow、authoring、GitHub 運用、知識化まわり
- **happy-coding**: 仕様、設計、実装、review、開発環境まわり

### skill の使い方

```text
/skill list happy-core
/skill list happy-coding
/skill run <skill-name>
```

### 旧 direct install 版を使っている場合

重複表示を避けるため、先に旧版を外します。

```powershell
copilot plugin uninstall happy-ai-life
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

あとで外す場合は次を実行します。

```powershell
copilot plugin uninstall happy-core@happy-ai-life-marketplace
copilot plugin uninstall happy-coding@happy-ai-life-marketplace
copilot plugin marketplace remove happy-ai-life-marketplace
```

## パス 2: この repo を改善する（ローカル開発）

**向いている人:** この repo 自体を改善したい人、repo bootstrap script や instructions をローカルで確認したい人。

### 前提

- Git
- Copilot CLI
- Python 3.14 以上
- `uv`
- `$HOME/.copilot/` に書き込めること

### 準備

```powershell
git clone https://github.com/RyoMurakami1983/happy_ai_life.git
cd happy_ai_life
uv sync --dev
```

### 個人環境へ反映

最短では `uv run app.py` だけで home sync を実行できます。まず差分確認したい場合だけ `home --dry-run` を使います。

[Windows: PowerShell]
```powershell
# 何が変わるか確認
uv run app.py home --dry-run

# 反映
uv run app.py
uv run app.py home
```

[Linux / WSL2: bash]
```bash
# 何が変わるか確認
uv run app.py home --dry-run --no-interactive

# 反映
uv run app.py --no-interactive
uv run app.py home --no-interactive
```

これで `copilot-instructions.md`、repo bootstrap 用 script、managed な user-level safety hook entry を `$HOME/.copilot/` に同期できます。hook entry は `settings.json` ではなく `config.json` に入ります。

### 確認

[Windows: PowerShell]
```powershell
copilot status
cat $HOME/.copilot/copilot-instructions.md
```

[Linux / WSL2: bash]
```bash
copilot status
cat "$HOME/.copilot/copilot-instructions.md"
```

### 開発の流れ

- `grill-with-docs`、必要に応じた `prototype` / `design-and-plan` で整理し、実装は `implement` で進める
- 失敗ログや review 対応を含めて改善を回すときは、`loop-engineering` を起点にしてから必要な専門 skill へ渡す
- 変更範囲に合う focused test と `uv run ruff check .` を流す
- PR を作って review を受ける

詳しくは [開発ガイド](DEVELOPMENT.md) を参照してください。

## パス 3: 既存 repo に導入する（Team Repo Setup）

**向いている人:** チームの repo に instructions、hooks、品質ゲートを入れたい人。

### 入るもの

- `copilot-instructions.md`
- GitHub Actions workflow
- Git client hooks
- repo bootstrap 用テンプレート

### 手順

1. まず現在の状態を確認します。

   [Windows: PowerShell]
   ```powershell
   & $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath <your-repo-path>
   ```

   [Linux / WSL2: bash]
   ```bash
   bash "$HOME/.copilot/scripts/repo-secure-check.sh" -TargetRepoPath <your-repo-path>
   ```

2. repo に bootstrap を入れます。

   [Windows: PowerShell]
   ```powershell
   & $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath <your-repo-path> -PolicyProfile HappyDefault
   ```

   [Linux / WSL2: bash]
   ```bash
   bash "$HOME/.copilot/scripts/sync-to-repo.sh" -TargetRepoPath <your-repo-path> -PolicyProfile HappyDefault
   ```

3. Git hooks を有効化します。

   [Windows: PowerShell]
   ```powershell
   & $HOME/.copilot/scripts/install-git-hooks.ps1 -TargetRepoPath <your-repo-path>
   ```

   [Linux / WSL2: bash]
   ```bash
   bash "$HOME/.copilot/scripts/install-git-hooks.sh" -TargetRepoPath <your-repo-path>
   ```

4. 反映を確認します。

   ```powershell
   cd <your-repo-path>
   git status
   ```

   `.github/`、`.githooks/`、`.gitattributes` の追加が見えれば正常です。

### 注意

- これらの変更は repo にコミットされます
- チーム全員が同じ instructions を使う前提です
- `gitleaks` により commit 時に secret を検査します
- Linux / WSL2 では `bash`、`git`、`rsync` が必要です。bash variant の safety guard を使う host では `jq` も必要です
- `.gitattributes` で `.githooks/**` の LF を固定します。`repo-secure-check` で line ending 指摘が出たら、まず `sync-to-repo` を再実行してください

通常は上の手順だけで十分です。重い governance や追加 profile は既定導線から外しています。

## 困ったとき

[トラブルシューティング](TROUBLESHOOTING.md) を参照してください。
