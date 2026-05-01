# Reference: Commands, Skills, and Decisions

## CLI Commands

### Home Sync

```powershell
# Preview changes
uv run app.py home --dry-run

# Apply sync
uv run app.py home
```

See [Home Sync](HOME_SYNC.md) for detailed guide.

### Repo Bootstrap

```powershell
# Preview repo bootstrap changes
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath <path> -DryRun

# Apply repo bootstrap
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath <path>

# Install Git hooks
& $HOME/.copilot/scripts/install-git-hooks.ps1 -RepoPath <path>

# Check repo security setup
& $HOME/.copilot/scripts/repo-secure-check.ps1 -RepoPath <path>
```

See [Repo Bootstrap](REPO_BOOTSTRAP.md) for detailed guide.

### Plugin Management

```powershell
# List installed plugins
copilot plugin list

# Add marketplace
copilot plugin marketplace add RyoMurakami1983/happy_ai_life

# Install plugin
copilot plugin install happy-core@happy-ai-life-marketplace

# Uninstall plugin
copilot plugin uninstall happy-core@happy-ai-life-marketplace
```

## Skills Directory

### happy-core

Workflow automation and core operations:

| Skill | Purpose | Invocation |
|-------|---------|-----------|
| (See plugins/happy-core/README.md) | | `/skill run <skill-name>` |

### happy-coding

Development lifecycle support:

| Skill | Purpose | Invocation |
|-------|---------|-----------|
| (See plugins/happy-coding/README.md) | | `/skill run <skill-name>` |

For full skills list:
```powershell
copilot skill list happy-core
copilot skill list happy-coding
```

## Architecture Decision Records

See [docs/adr/](../docs/adr/) for full archive.

### By Category

- **Distribution Strategy**: How plugins are packaged and distributed
- **Home Sync Governance**: Boundaries between managed and user-owned files
- **Security Layers**: Multi-layer secret protection
- **Documentation Structure**: Organization of docs, ADRs, and reference materials

### By Date

ADRs are dated and indexed. Check [docs/adr/README.md](../docs/adr/README.md) for chronological list.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `GITLEAKS_BIN` | Path to gitleaks binary | `gitleaks` (auto-detect) |
| `COPILOT_CLI_PATH` | Path to Copilot CLI | (system PATH) |

See [Troubleshooting](TROUBLESHOOTING.md) for solutions to common environment issues.

## Hooks and Configuration

### Git Hooks

Located in `.githooks/`:

- `pre-commit` — Scans staged files with gitleaks
- `pre-push` — Scans commits to be pushed with gitleaks

Enable with:
```powershell
git config core.hooksPath .githooks
```

### Copilot Hooks

Located in `.github/hooks/`:

- `pre-commit.json` — Copilot CLI hook configurations
- `scripts/` — Hook implementation scripts

See [Quality Gates](QUALITY_GATES.md) for details.

## See also

- [Development](DEVELOPMENT.md)
- [Authoring Guide](AUTHORING.md)
- [docs/adr/](../docs/adr/) — Full ADR archive
