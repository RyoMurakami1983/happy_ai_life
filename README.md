# happy_ai_life_coding_Environment

> 楽しく AI とコーディングライフを続けるための環境を、いつでもどこでも再現できるようにする母艦リポジトリ。

## Overview

このリポジトリは、Copilot の共通設定を配布するためのテンプレートです。
`.github/` を各 Repository に、`home-template/.copilot/` をホームディレクトリに同期し、同じ開発体験を再現します。

思想と背景は [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) を参照してください。

## Getting Started

PowerShell でリポジトリ直下から実行します。

1. ホームディレクトリへ同期

```powershell
./scripts/sync-to-home.ps1
```

2. 任意の Repository へ `.github/` を同期

```powershell
./scripts/sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo
```

3. 変更内容を事前確認したい場合

```powershell
./scripts/sync-to-home.ps1 -DryRun
./scripts/sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo -DryRun
```

4. Git の main 保護を有効化する

```powershell
# この母艦リポジトリでローカル保護を有効化する場合
git config --local core.hooksPath repo-template/.githooks

# 別リポジトリへ hooks をインストールする場合
./scripts/install-git-hooks.ps1 -TargetRepoPath C:\path\to\your-repo
```

## Structure

- `.github/`: 共有する Copilot instructions / hooks / workflows
- `home-template/.copilot/`: 個人環境向けテンプレート（skills / agents を含む）
- `scripts/`: 同期スクリプト
- `docs/PHILOSOPHY.md`: この母艦の思想と開発憲法

## Development

このリポジトリはアプリ本体ではないため、通常の build/run はありません。
変更時は、同期先への影響（scripts、hooks、workflows、instructions）を確認してください。
PR 前の深掘り事前レビューは `deep-review-preflight` skill を入口に、`code-quality-review` / `security-review` agent で実施します。
Git の client hooks は `repo-template/.githooks/` を正本にし、`core.hooksPath` で有効化します。GitHub の branch protection / ruleset は別途必須です。

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
