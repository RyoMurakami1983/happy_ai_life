# Getting Started with happy_ai_life

Choose your installation path based on your use case.

## Path 1: Marketplace Plugin (Recommended for End Users)

**Best for:** Using happy-core and happy-coding skills for your own projects without local development.

### Installation

First, add the repository as a Copilot CLI marketplace source:

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
```

Then install the plugins:

```powershell
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

### Verify

```powershell
copilot plugin list
```

You should see `happy-core` and `happy-coding` listed with version information.

### What you get

- **happy-core**: Workflow automation, authoring tools, GitHub operations, knowledge capture
- **happy-coding**: Specification, design, implementation, review, and developer setup skills

### Using the skills

In Copilot CLI:

```text
/skill list happy-core
/skill list happy-coding
/skill run <skill-name>
```

### Managing plugins

If you already have the older "direct install" version installed, uninstall it first:

```powershell
copilot plugin uninstall happy-ai-life
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

To remove marketplace plugins later:

```powershell
copilot plugin uninstall happy-core@happy-ai-life-marketplace
copilot plugin uninstall happy-coding@happy-ai-life-marketplace
copilot plugin marketplace remove happy-ai-life-marketplace
```

## Path 2: Local Development (For Contributors)

**Best for:** Contributing to happy-core or happy-coding, or customizing skills for your personal use.

### Prerequisites

- Git installed
- Copilot CLI installed
- Python 3.14+ and uv package manager
- Write access to `$HOME/.copilot/`

### Installation

```powershell
git clone https://github.com/RyoMurakami1983/happy_ai_life.git
cd happy_ai_life
uv sync --dev
```

### Setup your personal environment

```powershell
# Preview what will be synced
uv run app.py home --dry-run

# Apply the sync
uv run app.py home
```

This synchronizes your `$HOME/.copilot/` with the repository's `home-template/`.

### Verify

```powershell
copilot status
copilot skill list | head -20
```

You should see skills from both happy-core and happy-coding.

### Development workflow

- Design and plan changes using `/design-workshop` and PLAN mode
- Run quality checks: `uv run pytest -q`, `uv run ruff check .`, `uv run ty check .`
- Submit PRs for review

See [Development](DEVELOPMENT.md) for full details.

## Path 3: Add Copilot to Your Existing Project (Repo Bootstrap)

**Best for:** Adding Copilot guidance, Git hooks, and quality checks to a new or existing project repository.

### What gets added

- Copilot instructions (`copilot-instructions.md`)
- GitHub Actions workflows (quality gates, gitleaks scanning)
- Git client hooks (secret detection, code validation)
- Repository templates and configuration

### Steps

1. **Check your repository** first for any existing Copilot setup

   ```powershell
   & $HOME/.copilot/scripts/repo-secure-check.ps1 -RepoPath <your-repo-path>
   ```

   This confirms whether your repo has the necessary safety guardrails.

2. **Bootstrap** Copilot guidance to your repository

   ```powershell
   & $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath <your-repo-path>
   ```

3. **Install Git hooks**

   ```powershell
   & $HOME/.copilot/scripts/install-git-hooks.ps1 -RepoPath <your-repo-path>
   ```

4. **Verify** the setup

   ```powershell
   cd <your-repo-path>
   git status
   ```

   You should see new files in `.github/` and `.githooks/`

### Important

- These changes are committed to your repository (they're not local-only)
- All developers in your project will use the same Copilot instructions
- The Git hooks run `gitleaks` on every commit to prevent secrets from being committed

See [Repo Bootstrap](REPO_BOOTSTRAP.md) for detailed configuration options.

## Troubleshooting

<!-- TODO: Common issues and solutions -->

See [Troubleshooting](TROUBLESHOOTING.md) for more help.
