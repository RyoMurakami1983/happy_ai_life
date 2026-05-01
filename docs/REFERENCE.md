# リファレンス

## CLI コマンド

### Home Sync（個人環境同期）

```powershell
# 差分確認
uv run app.py home --dry-run

# 反映
uv run app.py home
```

詳しくは [Home Sync（個人環境同期）](HOME_SYNC.md) を参照してください。

### Repo Bootstrap（repo 初期導入）

```powershell
# 差分確認
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath <path> -DryRun

# 反映
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath <path>

# Git hooks の有効化
& $HOME/.copilot/scripts/install-git-hooks.ps1 -RepoPath <path>

# 安全弁の確認
& $HOME/.copilot/scripts/repo-secure-check.ps1 -RepoPath <path>
```

詳しくは [Repo Bootstrap（repo 初期導入）](REPO_BOOTSTRAP.md) を参照してください。

### Plugin 管理

```powershell
# 一覧
copilot plugin list

# marketplace 追加
copilot plugin marketplace add RyoMurakami1983/happy_ai_life

# install
copilot plugin install happy-core@happy-ai-life-marketplace

# uninstall
copilot plugin uninstall happy-core@happy-ai-life-marketplace
```

## skills 一覧の見方

### happy-core

workflow と運用寄りの skill 群です。

| 確認方法 | 内容 |
|----------|------|
| `copilot skill list happy-core` | 利用可能な skill 一覧を見る |
| `plugins/happy-core/README.md` | plugin 全体の構成を見る |

### happy-coding

仕様、設計、実装、review 寄りの skill 群です。

| 確認方法 | 内容 |
|----------|------|
| `copilot skill list happy-coding` | 利用可能な skill 一覧を見る |
| `plugins/happy-coding/README.md` | plugin 全体の構成を見る |

## ADR

ADR 全体は [docs/adr/](../docs/adr/) を参照してください。

### 主な分類

- **Distribution Strategy** — plugin の配布方針
- **Home Sync Governance** — 管理対象とユーザー所有の境界
- **Security Layers** — secret 保護の多層構成
- **Documentation Structure** — docs / ADR / reference の分担

### 並び順

時系列の一覧は [docs/adr/README.md](../docs/adr/README.md) を参照してください。

## 環境変数

| 変数 | 用途 | 既定値 |
|------|------|--------|
| `GITLEAKS_BIN` | gitleaks の実行パス | `gitleaks` |
| `COPILOT_CLI_PATH` | Copilot CLI の実行パス | system PATH |

困ったときは [トラブルシューティング](TROUBLESHOOTING.md) を参照してください。

## hooks と設定

### Git hooks

`.githooks/` にあります。

- `pre-commit` — staged files を gitleaks で検査
- `pre-push` — push 対象 commit を gitleaks で検査

有効化:

```powershell
git config core.hooksPath .githooks
```

### Copilot hooks

`.github/hooks/` にあります。

- `*.json` — hook 定義
- `scripts/` — hook script

詳しくは [品質ゲート](QUALITY_GATES.md) を参照してください。

## 関連

- [開発ガイド](DEVELOPMENT.md)
- [作成ガイド](AUTHORING.md)
- [docs/adr/](../docs/adr/)
