# Home Sync: Local Development Setup

<!-- TODO: 詳細な home sync ガイドを記述
構成：
- home sync とは何か
- 何が sync されるか（managed vs user-owned）
- dry-run と apply フロー
- トラブルシューティング
- Rollback 手順

参考: 現在の README の「Trusted local author bootstrap」セクション（65-124行）
-->

## What is home sync?

Home sync synchronizes your `$HOME/.copilot/` directory with this repository's `home-template/`.

<!-- TODO: 詳細説明 -->

## What gets synced?

### Managed (updated from repo)

<!-- TODO: リスト -->

### NOT synced (user-owned)

<!-- TODO: リスト -->

## How to use

### Step 1: Preview changes

```powershell
uv sync --dev
uv run app.py home --dry-run
```

### Step 2: Apply

```powershell
uv run app.py home
```

### Step 3: Verify

```powershell
cat $HOME/.copilot/copilot-instructions.md
```

## Rollback

<!-- TODO: Rollback 手順 -->

## See also

- [Getting Started](GETTING_STARTED.md)
- [Repo Bootstrap](REPO_BOOTSTRAP.md)
