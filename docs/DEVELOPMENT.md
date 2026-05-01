# Development: Contributing to happy_ai_life

## Prerequisites

- Git installed and configured
- Copilot CLI installed
- Python 3.14+ and `uv` package manager
- Text editor or IDE of your choice

## Repository Overview

```
happy_ai_life/
├── plugins/                  # Curated Copilot plugin packages
│   ├── happy-core/           # Core workflow skills
│   ├── happy-coding/         # Development lifecycle skills
│   └── plugin.json           # Plugin definitions
├── home-template/            # Trusted local bootstrap
│   └── .copilot/             # Skills, agents, config
├── repo-template/            # Bootstrap template for target repos
│   ├── .github/              # Actions, hooks, instructions
│   └── .githooks/            # Client-side Git hooks
├── docs/                     # User documentation
├── scripts/                  # Sync and bootstrap scripts
├── tests/                    # Unit and integration tests
├── pyproject.toml            # Python dependencies
├── README.md                 # Project overview
├── LICENSE                   # MIT License
└── .editorconfig             # Editor formatting
```

This repository contains:
- `plugins/happy-core/` — Core Copilot CLI plugin (workflow, authoring, GitHub ops)
- `plugins/happy-coding/` — Coding Copilot CLI plugin (spec, design, impl, review)
- `scripts/` — Sync and bootstrap scripts
- `home-template/` — Local author bootstrap template
- `repo-template/` — Target repo bootstrap template

## Development Workflow

### 1. Setup

```powershell
git clone https://github.com/RyoMurakami1983/happy_ai_life.git
cd happy_ai_life
uv sync --dev
```

### 2. Design Phase

For non-trivial changes, use design-workshop:

```powershell
copilot /design-workshop
```

### 3. Plan Phase

Create a plan for implementation:

```powershell
copilot /plan-mode
```

### 4. Implement

Create feature branch and make changes:

```powershell
git checkout -b feature/your-feature-name
# Edit files...
```

### 5. Test

Run quality checks:

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

### 6. Commit

Use Conventional Commits with Co-authored-by trailer:

```powershell
git commit -m "feat: description

Details here.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### 7. Review

Submit PR for review:

```powershell
git push origin feature/your-feature-name
gh pr create
```

## Build and Test Commands

| Command | Purpose |
|---------|---------|
| `uv sync --dev` | Install dependencies |
| `uv run pytest -q` | Run unit tests |
| `uv run ruff check .` | Lint Python code |
| `uv run ty check .` | Type-check Python |
| `uv run app.py` | Run launcher |

### Running tests

```powershell
# All tests
uv run pytest -q

# Specific test file
uv run pytest -q tests/test_happy_env.py

# Specific test function
uv run pytest -q tests/test_happy_env.py::test_function_name
```

### Code quality

```powershell
# Check linting
uv run ruff check .

# Auto-fix (where possible)
uv run ruff check . --fix

# Type checking
uv run ty check .
```

## Quality Gates

All PRs must pass:

1. **gitleaks** — Secret detection (always on)
2. **textlint** — Markdown linting (optional)

See [Quality Gates](QUALITY_GATES.md) for detailed configuration.

## Creating Skills, Agents, and Instructions

See [Authoring Guide](AUTHORING.md) for comprehensive guidance on:
- Skill structure and templates
- Agent development
- Repository instructions (copilot-instructions.md)
- Validation and testing

## Git Workflow

### Branch naming

```
feature/<description>    # New feature
bugfix/<description>     # Bug fix
docs/<description>       # Documentation
refactor/<description>   # Code refactoring
```

### Commit style

Use Conventional Commits:

```
feat: add new feature
fix: resolve issue #123
docs: update README
refactor: extract utility function
test: add test cases
chore: update dependencies
```

### PR process

1. Create feature branch
2. Make changes and test locally
3. Push to remote
4. Create PR with description
5. Address review feedback
6. Merge when approved

## Security: 5-Layer Protection

This repository implements multi-layer secret protection:

1. **Local editor/IDE** — Use EditorConfig and file templates
2. **Pre-commit hook** — gitleaks scans staged files
3. **Pre-push hook** — gitleaks scans commits to be pushed
4. **GitHub branch protection** — Ruleset blocks pushes without PR
5. **GitHub Action gitleaks** — Final verification on PR

If a secret is detected at any layer, the operation is blocked. See [Troubleshooting - gitleaks not found](TROUBLESHOOTING.md#issue-gitleaks-not-found) for solutions.

## Session Continuity and Retrospectives

Use the `furikaeri` skill to capture session learnings and decisions:

```powershell
copilot /furikaeri
```

This creates a structured record of:
- What you did (Y)
- What you learned (W)
- What's next (T)
- Action items and improvements

## Important Files

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | Repository guidelines |
| `pyproject.toml` | Python dependencies and config |
| `.gitleaks.toml` | Secret detection configuration |
| `.editorconfig` | Editor formatting rules |
| `.github/workflows/quality.yml` | Quality gate workflows |

## See also

- [Authoring Guide](AUTHORING.md)
- [Quality Gates](QUALITY_GATES.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [README](../README.md)
