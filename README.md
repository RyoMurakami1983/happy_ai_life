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

`sync-to-repo.ps1` は `repo-template/.github/` を target repo に配布するため、`.github/copilot-instructions.md` と `.github/instructions/*.instructions.md` もこの導線で入ります。`/sdd` で pilot / downstream repo を触る前に、target repo 側へこの配布が済んでいるか、`git init` 済みか、fixed build/test/launch command があるか確認してください。

> **注意: `-Mirror` フラグについて**
> `repo` sync では `-Mirror`（または `--mirror`）が robocopy の `/MIR` に相当し、同期先にのみ存在するファイルを**完全削除**します（ゴミ箱には入りません）。
>
> `home` sync では `-Mirror` / `--mirror` は**互換オプションとして受け付けるだけで無視**されます。  
> `home-template/.copilot/` 全体を `/MIR` せず、次の tracked 項目だけを whitelist copy します。
> - `skills/`
> - `agents/`
> - `docs/furikaeri/`
> - `copilot-instructions.md`
> - `mcp-config.sample.json`
>
> そのため home sync は、既存の `%USERPROFILE%\.copilot\` 配下にある runtime data や user-owned file を削除しません。  
> 一方で repo sync の `-Mirror` は引き続き削除を伴うため、必ず `-DryRun` で事前確認してください。  
> robocopy の `*EXTRA` は「同期先だけにある項目」を意味し、repo sync の `/MIR` では削除対象です。

### MCP config initialization

home sync は `%USERPROFILE%\.copilot\mcp-config.json` を上書きしません。
初回だけ `%USERPROFILE%\.copilot\mcp-config.sample.json` を `mcp-config.json` にコピーし、API キーを設定してください。

## Structure

- `.github/`: 共有する Copilot instructions / hooks / workflows / repo 専用 skills
- `repo-template/.github/.gitignore`: target repo に配布する local ignore の正本
- `repo-template/.github/instructions/`: target repo に配布する言語別 instructions の正本
- `repo-template/docs/furikaeri/`: target repo に配布する共有ふりかえり保存先の雛形
- `home-template/.copilot/`: 個人環境向けテンプレート。home sync で配るのは `skills/`、`agents/`、`docs/furikaeri/`、`copilot-instructions.md`、`mcp-config.sample.json`
- `home-template/.copilot/docs/furikaeri/`: home 側に同期されるふりかえり archive の雛形
- `home-template/.copilot/agents/`: home sync で配る custom agents の置き場。現状は `tdd-coder` を含み、将来は最大 3 agent までを保持する前提
- `scripts/`: 同期スクリプト
- `app.py`: 公開 launcher。既存 PowerShell を正本のまま呼び出す
- `docs/PHILOSOPHY.md`: この母艦の思想と開発憲法

## Development

このリポジトリはアプリ本体ではありませんが、運用用 launcher と quality command は持ちます。
変更時は、同期先への影響（scripts、hooks、workflows、instructions）を確認してください。
Skill / Agent / repository instructions authoring の公開入口は `home-template/.copilot/skills/copilot-authoring` です。設計は `design-workshop`、計画は PLAN mode を使い、custom agent は原則増やさず、必要時だけ `tdd-coder` のような narrow specialist を `/fleet` または明示指名で使います。repo-wide と path-specific instructions は `copilot-authoring` 配下の instructions authoring ルートで扱い、常時読み込む rule と詳細 workflow を分離します。実装中の独立 gate は `implementation-eval-gate` を使い、`/sdd` から bootstrap checkpoint → contract checkpoint → generator → eval の順でつなぎます。
Git の client hooks は `repo-template/.githooks/` を正本にし、`core.hooksPath` で有効化します。GitHub の branch protection / ruleset は別途必須です。
`pre-commit` の secret guard は、repo ルートに `.gitleaks.toml` がある場合に staged diff を `gitleaks` で検査します。`gitleaks` 導入前に opt-in していない repo では scan をスキップし、`SECRET_GUARD_REQUIRE_CONFIG=1` を設定した場合だけ設定欠如を hard fail にできます。

interactive app を **比較用 pilot** として進める場合は、通常の build/test/launch command に加えて、次の comparable harness contract を先に固定します。

- deterministic seed または同等の固定シナリオ
- 共通 state dump schema
- 共通 command runner

これは pilot 比較のぶれを減らすための要件であり、製品要件として乱数や実装自由度を縛る意図ではありません。

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
The local `pre-commit` hook reuses the same `.gitleaks.toml`, so allowlist tuning is shared between local commits and CI for repositories that opt in to gitleaks scanning by adding the config file.

## License

TODO: Add license.
