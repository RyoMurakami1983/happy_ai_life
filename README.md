# happy_ai_life_coding_Environment

> 楽しく AI とコーディングライフを続けるための環境を、いつでもどこでも再現できるようにする母艦リポジトリ。

## Overview

このリポジトリは、Copilot の共通設定を配布するためのテンプレートです。
`.github/` を各 Repository に、`home-template/.copilot/` をホームディレクトリに同期し、同じ開発体験を再現します。

思想と背景は [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) を参照してください。

## Getting Started

基本の入口は `app.py` だけです。

```powershell
uv sync --dev
uv run app.py
```

CLI で直接使う場合も `app.py` から呼びます。

```powershell
uv run app.py home --dry-run
uv run app.py repo C:\path\to\your-repo --dry-run
uv run app.py repo C:\path\to\your-repo
uv run app.py hooks C:\path\to\your-repo
```

### First run when `uv` is missing

Copilot からは、この母艦 repo 専用の `.github/skills/initial_setup_happy_env` skill を使う前提です。
手動で始める場合は、先に `uv` を導入してから `uv sync --dev` を実行します。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync --dev
```

### Direct PowerShell fallback

PowerShell を直接叩く既存導線も引き続き使えます。

```powershell
./scripts/sync-to-home.ps1
./scripts/sync-to-home.ps1 -DryRun
./scripts/sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo
./scripts/sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo -DryRun
./scripts/install-git-hooks.ps1 -TargetRepoPath C:\path\to\your-repo
```

> **注意: `-Mirror` フラグについて**
> `-Mirror`（または `--mirror`）は robocopy の `/MIR` に相当し、同期先にのみ存在するファイルを**完全削除**します（ゴミ箱には入りません）。
> 以下の Copilot ランタイムデータは除外済みで削除されません:
> - `session-state/`, `pkg/`, `logs/`, `ide/`, `restart/`（ディレクトリ）
> - `config.json`, `command-history-state.json`（ファイル）
>
> それ以外の `.copilot/` 内データは削除対象になる可能性があるため、必ず `-DryRun` で事前確認してください。

### MCP config initialization

home sync は `%USERPROFILE%\.copilot\mcp-config.json` を上書きしません。
初回だけ `%USERPROFILE%\.copilot\mcp-config.sample.json` を `mcp-config.json` にコピーし、API キーを設定してください。

## Structure

- `.github/`: 共有する Copilot instructions / hooks / workflows / repo 専用 skills
- `repo-template/.github/.gitignore`: target repo に配布する local ignore の正本
- `home-template/.copilot/`: 個人環境向けテンプレート（skills / agents を含む）
- `scripts/`: 同期スクリプト
- `app.py`: 公開 launcher。既存 PowerShell を正本のまま呼び出す
- `docs/PHILOSOPHY.md`: この母艦の思想と開発憲法

## Development

このリポジトリはアプリ本体ではありませんが、運用用 launcher と quality command は持ちます。
変更時は、同期先への影響（scripts、hooks、workflows、instructions）を確認してください。
Skill / Agent authoring の公開入口は `home-template/.copilot/skills/copilot-authoring-beta` です。
PR 前の深掘り事前レビューは `deep-review-preflight` skill を入口に、`code-quality-review` / `security-review` agent で実施します。
Git の client hooks は `repo-template/.githooks/` を正本にし、`core.hooksPath` で有効化します。GitHub の branch protection / ruleset は別途必須です。

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

## Quality Gate

This repository uses a GitHub Actions quality gate on every PR:

| Check | Tool | Trigger |
|-------|------|---------|
| Secret detection | [gitleaks](https://github.com/gitleaks/gitleaks) | Always enabled |
| Markdown lint | [textlint](https://textlint.github.io/) | Uncomment in `.github/workflows/quality.yml` when needed |

### Adding textlint (for Markdown-heavy repos)

1. Uncomment the `textlint` job in `.github/workflows/quality.yml`
2. Copy `.textlintrc.json` and `package.json` from the [github-quality-gate-setup skill](https://github.com/RyoMurakami1983/skills_repository)
3. Run `npm install`
4. Add `textlint` as a required status check in Branch Protection settings

### Customizing gitleaks allowlist

Edit `.gitleaks.toml` to add allowlist entries for documentation example placeholders
that should not be treated as real secrets.

## License

TODO: Add license.
