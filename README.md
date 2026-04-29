# happy_ai_life_coding_Environment

> 楽しく AI とコーディングライフを続けるための環境を、いつでもどこでも再現できるようにする母艦リポジトリ。

## Overview

このリポジトリは、Copilot CLI の reusable skills / agents と repo-local bootstrap 資産を管理する母艦です。
公開・共有向けの primary distribution は Copilot CLI plugin です。作者本人や信頼済みローカル環境の再現には、従来どおり `home-template/.copilot/` を home sync できます。

思想と背景は [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) を参照してください。

## Getting Started

### Primary: Copilot CLI marketplace install

公開・共有用途では、この repo を owner-managed marketplace として追加してから plugin をインストールします。

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life_coding_Environment
copilot plugin install happy-ai-life@happy-ai-life-marketplace
```

この plugin は `plugins/happy-ai-life` の curated package で、reusable skills と narrow agent（`tdd-coder`）を配布します。repo-local instructions、hooks、Git client hooks、MCP server 設定は plugin install の副作用として書き込みません。

Copilot CLI は direct repository / URL / local path install を deprecated として警告するため、primary path は `plugin@marketplace` 形式にします。ローカル checkout では package 構造を確認し、branch push 後に marketplace add / browse / install を smoke test してください。

既に direct install 版を使っている場合は、marketplace 版と共存して重複表示されるため、先に direct install 版を uninstall してから marketplace 版を入れてください。

```powershell
copilot plugin uninstall happy-ai-life
copilot plugin marketplace add RyoMurakami1983/happy_ai_life_coding_Environment
copilot plugin install happy-ai-life@happy-ai-life-marketplace
```

Direct install は短期的な fallback としては動作しますが、今後の Copilot CLI では unsupported になる可能性があるため primary path にはしません。

marketplace 版の plugin と marketplace 登録を外す場合は、plugin を先に uninstall してから marketplace を remove します。

```powershell
copilot plugin uninstall happy-ai-life@happy-ai-life-marketplace
copilot plugin marketplace remove happy-ai-life-marketplace
```

### Optional: Context7 external plugin

Context7 はこの repo の `mcp-config.sample.json` では配布しません。必要な場合は、外部 Copilot CLI plugin として導入します。以下は Context7 側の marketplace plugin 構成に基づく導入例です。実行前に現在の Copilot CLI と Context7 plugin 側の案内も確認してください。

Copilot CLI の interactive session では slash command を使います。

```text
/plugin marketplace add upstash/context7
/plugin install context7-plugin@context7-marketplace
```

terminal から実行する場合の等価コマンドです。

```powershell
copilot plugin marketplace add upstash/context7
copilot plugin install context7-plugin@context7-marketplace
```

### Trusted local author bootstrap: home sync

`home sync` は、作者本人や信頼済みローカル環境を再現するための bootstrap です。公開・共有向けの推奨導線ではありません。

```powershell
uv sync --dev
uv run app.py home --dry-run
uv run app.py home
```

通常は次の順で実行します。

1. まず差分確認

   ```powershell
   uv run app.py home --dry-run
   ```

   `skills/` と `agents/` の追加・更新予定、`repo-template/` と `.github/hooks/` の managed surface の変更予定が表示されます。

2. 問題なければ本適用

   ```powershell
   uv run app.py home
   ```

3. 更新前バックアップが必要だった場合は archive を確認

   ```powershell
   Get-ChildItem $HOME\copilot_archives\skills
   Get-ChildItem $HOME\copilot_archives\agents -Recurse
   ```

   `skills/` は `%USERPROFILE%\copilot_archives\skills\<skill-name>\`、`agents/` は `%USERPROFILE%\copilot_archives\agents\...` に 1 世代だけ退避されます。

4. 必要なら手動で復元

   ```powershell
   Copy-Item $HOME\copilot_archives\skills\<skill-name> $HOME\.copilot\skills\<skill-name> -Recurse -Force
   Copy-Item $HOME\copilot_archives\agents\<agent-file> $HOME\.copilot\agents\<agent-file> -Force
   ```

   archive は自動復元ではなく、当面は manual operation 前提です。

### Repo-local bootstrap: instructions and hooks

repo instructions、path-specific instructions、Copilot hooks、Git client hooks は target repo のローカル資産として配布します。plugin install では target repo を変更しません。

```powershell
%USERPROFILE%\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo -DryRun
%USERPROFILE%\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\path\to\your-repo
%USERPROFILE%\.copilot\scripts\install-git-hooks.ps1 -TargetRepoPath C:\path\to\your-repo
%USERPROFILE%\.copilot\scripts\repo-secure-check.ps1 -TargetRepoPath C:\path\to\your-repo
```

母艦 repo 直下の `./scripts/` は正本であり、template 開発や検証で使います。運用で target repo を bootstrap するときは `%USERPROFILE%\.copilot\scripts\` を既定導線とします。

`sync-to-repo.ps1` は `repo-template/.github/` を target repo に配布するため、`.github/copilot-instructions.md` と `.github/instructions/*.instructions.md` もこの導線で入ります。`/sdd` で pilot / downstream repo を触る前に、target repo 側へこの配布が済んでいるか、`git init` 済みか、fixed build/test/launch command があるか確認してください。

> **注意: `home` sync の同期境界について**
> home sync は次の境界で挙動が分かれます。
> - `skills/`: skill directory 単位で diff 同期。extra skill は残し、同名更新時は `%USERPROFILE%\copilot_archives\skills\<skill-name>\` に旧版を 1 世代だけ退避します。
> - `agents/`: `*.agent.md` 単位で diff 同期。extra agent は残し、同名更新時は `%USERPROFILE%\copilot_archives\agents\...` に旧版を 1 世代だけ退避します。
> - `repo-template/`
> - `.github/hooks/`
>
> さらに次の tracked 項目を追加・更新します。
> - `docs/furikaeri/`
> - `scripts/sync-to-repo.ps1`
> - `scripts/install-git-hooks.ps1`
> - `scripts/repo-secure-check.ps1`
> - `scripts/home_sync_planner.py`
> - `copilot-instructions.md`
>
> `repo-template/` と `.github/hooks/` は managed surface として template に無い項目を削除します。`skills/` と `agents/` の extra 項目は削除しません。`docs/furikaeri/`、既存の `%USERPROFILE%\.copilot\` 配下にある runtime data、live `mcp-config.json` のような user-owned file も削除しません。
> home sync の dry-run は robocopy ログではなく、自前の filesystem diff を正本にしています。repo sync の `-Mirror`（`$HOME\.copilot\scripts\sync-to-repo.ps1 -Mirror`）は引き続き同期先にのみ存在するファイルを**完全削除**するため、使用前に必ず `-DryRun` で事前確認してください。

### First run when `uv` is missing

Copilot からは、この母艦 repo 専用の `.github/skills/initial_setup_happy_env` skill を使う前提です。
手動で始める場合は、先に `uv` を導入してから `uv sync --dev` を実行します。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync --dev
```

## Structure

- `plugins/happy-ai-life/`: 公開・共有向けの primary Copilot CLI plugin package。reusable skills / agents を curated copy として含む
- `.github/`: 母艦 repo 自身の Copilot instructions / hooks / workflows / repo 専用 skills
- `repo-template/.github/.gitignore`: target repo に配布する local ignore の正本
- `repo-template/.github/instructions/`: target repo に配布する言語別 instructions の正本
- `repo-template/docs/furikaeri/`: target repo に配布する共有ふりかえり保存先の雛形
- `home-template/.copilot/`: 信頼済みローカル author bootstrap 用テンプレート。home sync では `skills/`、`agents/`、`docs/furikaeri/`、`copilot-instructions.md`、`repo-template/`、`.github/hooks/`、bootstrap 用 scripts、`scripts/home_sync_planner.py` を HOME 配下へ配布する
- `home-template/.copilot/docs/furikaeri/`: home 側に同期されるふりかえり archive の雛形
- `home-template/.copilot/agents/`: home sync で配る custom agents の置き場。現状は `tdd-coder` を含み、将来は最大 3 agent までを保持する前提
- `scripts/`: 同期スクリプト
- `app.py`: trusted local home sync 用 launcher。`uv run app.py` で GUI、`uv run app.py home` で CLI 実行
- `docs/PHILOSOPHY.md`: この母艦の思想と開発憲法

## Development

このリポジトリはアプリ本体ではありませんが、Copilot CLI plugin package、運用用 launcher、quality command は持ちます。
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
