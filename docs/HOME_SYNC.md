# Home Sync: Local Development Setup

Home sync synchronizes your `$HOME/.copilot/` directory with this repository's `home-template/`.

**Note:** Home sync is for trusted local author bootstrap and personal environment reproduction. It is not the recommended path for sharing or distribution.

## What is home sync?

Home sync clones and synchronizes curated skills, agents, configuration, and repo bootstrap templates from `home-template/.copilot/` into your local `$HOME/.copilot/` directory. This allows you to reproduce the author's personal development environment.

**Key boundary:** Home sync only updates managed files from the repo. User-owned files (custom skills, local configuration, credentials) are preserved.

## What gets synced?

### Managed (updated from repo)

- Curated skills in `skills/` (authoring templates, validation tools)
- Curated agents in `agents/` (custom task executors)
- Repository instructions (`copilot-instructions.md`)
- Repo bootstrap templates (`repo-template/`)
- Git hooks and scripts (`scripts/`, `.githooks/`)
- Configuration samples (`mcp-config.sample.json`)

### NOT synced (user-owned, preserved)

- `mcp-config.json` — Live MCP server configuration (never overwritten)
- `config.json` — User safety hooks and personal settings
- Custom skills or agents you've authored locally
- Session data and history
- Personal credentials and secrets

## How to use

### Prerequisites

- Copilot CLI installed
- uv (Python package manager) available
- Read-write access to `$HOME/.copilot/`

### Step 1: Clone this repository

```powershell
git clone https://github.com/RyoMurakami1983/happy_ai_life.git
cd happy_ai_life
```

### Step 2: Preview changes

```powershell
uv sync --dev
uv run app.py home --dry-run
```

This shows you exactly what will be updated, added, or removed without making any changes.

### Step 3: Apply sync

```powershell
uv run app.py home
```

The sync will:
1. Copy managed files from `home-template/.copilot/` to `$HOME/.copilot/`
2. Clean up known legacy files that are no longer needed
3. Preserve all user-owned files (custom skills, config, credentials)
4. Archive any files it replaces (old version saved to `$HOME/copilot_archive/`)

### Step 4: Verify success

```powershell
cat $HOME/.copilot/copilot-instructions.md
copilot status
```

## Rollback

If you need to restore the previous state after sync, archived files are saved in `$HOME/copilot_archive/`. Check this directory and restore what you need.

If you need to roll back the entire sync:

```powershell
# Restore from the archive
Get-ChildItem $HOME/copilot_archive -Recurse | Copy-Item -Destination $HOME/.copilot -Force
```

## Important Warnings

⚠️ **Data loss risk:** Do not run `uv run app.py home` without first reviewing the `--dry-run` output. The sync replaces files, so verify the changes are intentional.

⚠️ **Not for shared teams:** Home sync is designed for personal or trusted author environments only. For sharing Copilot guidance across a team, use the marketplace plugin installation path instead (see [Getting Started](GETTING_STARTED.md)).

⚠️ **User-owned files are preserved:** Your custom skills, agents, and configuration will not be deleted by home sync, but if a filename matches a managed file, the managed version will overwrite it.

## See also

- [Getting Started](GETTING_STARTED.md)
- [Repo Bootstrap](REPO_BOOTSTRAP.md)
