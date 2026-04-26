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
uv run app.py home
```

### First run when `uv` is missing

Copilot からは、この母艦 repo 専用の `.github/skills/initial_setup_happy_env` skill を使う前提です。
手動で始める場合は、先に `uv` を導入してから `uv sync --dev` を実行します。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync --dev
```

### Direct PowerShell fallback

home sync 済みの環境では、PowerShell を直接叩く運用導線として `%USERPROFILE%\.copilot\scripts\` を優先します。
ここから実行すると、script の既定値で `%USERPROFILE%\.copilot` が `SourceRoot` として使われます。

```powershell
%USERPROFILE%\.copilot\scripts\sync-to-home.ps1
%USERPROFILE%\.copilot\scripts\sync-to-home.ps1 -DryRun
%USERPROFILE%\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo
%USERPROFILE%\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo -DryRun
%USERPROFILE%\.copilot\scripts\install-git-hooks.ps1 -TargetRepoPath C:\path\to\your-repo
%USERPROFILE%\.copilot\scripts\repo-secure-check.ps1 -TargetRepoPath C:\path\to\your-repo
```

母艦 repo 直下の `./scripts/` は正本であり、template 開発や検証で使います。運用で target repo を bootstrap するときは `%USERPROFILE%\.copilot\scripts\` を既定導線とします。

`sync-to-repo.ps1` は `repo-template/.github/` を target repo に配布するため、`.github/copilot-instructions.md` と `.github/instructions/*.instructions.md` もこの導線で入ります。`/sdd` で pilot / downstream repo を触る前に、target repo 側へこの配布が済んでいるか、`git init` 済みか、fixed build/test/launch command があるか確認してください。

> **注意: `home` sync の managed directory について**
> home sync は次の **managed directory** を常に template 一致へ同期します。
> - `skills/`
> - `agents/`
> - `repo-template/`
> - `.github/hooks/`
>
> さらに次の tracked 項目を追加・更新します。
> - `docs/furikaeri/`
> - `scripts/sync-to-repo.ps1`
> - `scripts/install-git-hooks.ps1`
> - `scripts/repo-secure-check.ps1`
> - `copilot-instructions.md`
> - `mcp-config.sample.json`
>
> managed directory の中では template に無い項目を削除しますが、`docs/furikaeri/`、既存の `%USERPROFILE%\.copilot\` 配下にある runtime data、`mcp-config.json` のような user-owned file は削除しません。  
> repo sync の `-Mirror`（`$HOME\.copilot\scripts\sync-to-repo.ps1 -Mirror`）は robocopy の `/MIR` に相当し、同期先にのみ存在するファイルを**完全削除**します（ゴミ箱には入りません）。使用前に必ず `-DryRun` で事前確認してください。

### MCP config initialization

home sync は `%USERPROFILE%\.copilot\mcp-config.json` を上書きしません。
初回だけ `%USERPROFILE%\.copilot\mcp-config.sample.json` を `mcp-config.json` にコピーし、API キーを設定してください。

## Structure

- `.github/`: 共有する Copilot instructions / hooks / workflows / repo 専用 skills
- `repo-template/.github/.gitignore`: target repo に配布する local ignore の正本
- `repo-template/.github/instructions/`: target repo に配布する言語別 instructions の正本
- `repo-template/docs/furikaeri/`: target repo に配布する共有ふりかえり保存先の雛形
- `home-template/.copilot/`: 個人環境向けテンプレート。home sync では `skills/`、`agents/`、`docs/furikaeri/`、`copilot-instructions.md`、`mcp-config.sample.json` に加え、`repo-template/`、`.github/hooks/`、bootstrap 用 scripts を HOME 配下へ配布する
- `home-template/.copilot/docs/furikaeri/`: home 側に同期されるふりかえり archive の雛形
- `home-template/.copilot/agents/`: home sync で配る custom agents の置き場。現状は `tdd-coder` を含み、将来は最大 3 agent までを保持する前提
- `scripts/`: 同期スクリプト
- `app.py`: 公開 launcher。home sync 専用。`uv run app.py` で GUI、`uv run app.py home` で CLI 実行
- `docs/PHILOSOPHY.md`: この母艦の思想と開発憲法

## Development

このリポジトリはアプリ本体ではありませんが、運用用 launcher と quality command は持ちます。
変更時は、同期先への影響（scripts、hooks、workflows、instructions）を確認してください。
Skill / Agent / repository instructions authoring の公開入口は `home-template/.copilot/skills/copilot-authoring` です。設計は `design-workshop`、計画は PLAN mode を使い、custom agent は原則増やさず、必要時だけ `tdd-coder` のような narrow specialist を `/fleet` または明示指名で使います。repo-wide と path-specific instructions は `copilot-authoring` 配下の instructions authoring ルートで扱い、常時読み込む rule と詳細 workflow を分離します。実装中の独立 gate は `implementation-eval-gate` を使い、`/sdd` から bootstrap checkpoint → contract checkpoint → generator → eval の順でつなぎます。
Git の client hooks は `repo-template/.githooks/` を正本にし、`core.hooksPath` で有効化します。GitHub の branch protection / ruleset は別途必須です。
downstream repo の local safety valve を確認するときは `$HOME\.copilot\scripts\repo-secure-check.ps1` を使い、repo instructions / Copilot hooks / `.githooks` / `core.hooksPath` の不足があれば `$HOME\.copilot\scripts\sync-to-repo.ps1` と `$HOME\.copilot\scripts\install-git-hooks.ps1` で補います。
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

### Troubleshooting: gitleaks not found in PATH

If you see the error `gitleaks is required for the pre-commit secret scan, but it was not found`, the hook cannot locate the gitleaks binary. Follow these steps to resolve it:

#### Step 1: Find the gitleaks executable path

**Windows:**
```powershell
where gitleaks
# or if you installed via scoop:
scoop which gitleaks
```

**macOS / Linux:**
```bash
which gitleaks
```

#### Step 2: Retry the commit with GITLEAKS_BIN set

Once you have the path, retry the commit by setting the `GITLEAKS_BIN` environment variable:

**Windows (PowerShell):**
```powershell
$env:GITLEAKS_BIN="C:\Program Files\gitleaks.exe"
git commit -m "your message"
# or as a one-liner:
$env:GITLEAKS_BIN="C:\Program Files\gitleaks.exe"; git commit -m "your message"
```

**macOS / Linux (bash/zsh):**
```bash
GITLEAKS_BIN=/usr/local/bin/gitleaks git commit -m "your message"
```

#### Step 3 (optional): Make it permanent

To avoid setting `GITLEAKS_BIN` on every commit, add it to your shell profile:

**Windows (PowerShell):**
Add this line to your PowerShell profile (`$PROFILE`):
```powershell
$env:GITLEAKS_BIN="C:\Program Files\gitleaks.exe"
```

**macOS / Linux:**
Add this line to `~/.bashrc`, `~/.zshrc`, or your shell's rc file:
```bash
export GITLEAKS_BIN=/usr/local/bin/gitleaks
```

Then reload your shell or open a new terminal window.

## License

TODO: Add license.
