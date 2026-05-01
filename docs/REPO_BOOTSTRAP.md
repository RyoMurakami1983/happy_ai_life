# Repo Bootstrap: Adding Copilot to Your Project

Repo bootstrap adds Copilot guidance, Git hooks, and quality checks to a target repository.

**Best for:** Enabling structured development practices across a team repository.

## Overview

When you bootstrap Copilot to a repository, the following are added:

- **.github/copilot-instructions.md** — Guidance and conventions for developers
- **.github/hooks/** — Copilot CLI hook configurations
- **.github/workflows/*.yml** — GitHub Actions for quality gates (gitleaks, etc.)
- **.githooks/pre-commit** — Client-side secret scanning hook
- **.githooks/pre-push** — Client-side secret scanning hook before push
- **repo-template/** files — Bootstrap configuration templates

All changes are committed to the repository so all developers use the same setup.

## Steps

### Step 1: Check current setup

Before bootstrapping, verify your repository's existing Copilot setup:

```powershell
& $HOME/.copilot/scripts/repo-secure-check.ps1 -RepoPath C:\your-repo
```

This checks for:
- ✅ `.github/copilot-instructions.md` (Copilot guidance)
- ✅ `.github/hooks/` (Copilot hooks)
- ✅ `.github/workflows/quality.yml` (Quality gates)
- ✅ `.githooks/pre-commit` (Git hook)
- ✅ `.githooks/pre-push` (Git hook)
- ✅ `core.hooksPath` configured

If any are missing, proceed to Step 2.

### Step 2: Bootstrap the repository

```powershell
# Preview what will be added (DRY RUN)
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath C:\your-repo -DryRun

# Apply bootstrap
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath C:\your-repo
```

This syncs from `$HOME/.copilot/repo-template/` to your target repository.

### Step 3: Install Git hooks

```powershell
& $HOME/.copilot/scripts/install-git-hooks.ps1 -RepoPath C:\your-repo
```

This enables the `.githooks/pre-commit` and `.githooks/pre-push` hooks.

### Step 4: Verify the setup

```powershell
cd C:\your-repo

# Check that files were added
git status

# Verify hooks are active
git config core.hooksPath
# Should output: .githooks

# Run the verification script again
& $HOME/.copilot/scripts/repo-secure-check.ps1 -RepoPath .
```

## What gets checked?

| Item | What it does | Failure = |
|------|------------|-----------|
| gitleaks (pre-commit) | Scans staged files for secrets before commit | Commit rejected |
| gitleaks (pre-push) | Scans commits about to push | Push rejected |
| gitleaks (GitHub Action) | Scans PR for any secrets | PR check fails |
| Copilot instructions | Provides guidance to Copilot for your repo | (informational) |

## Important warnings

⚠️ **These changes are committed to your repository**

All bootstrap files are committed (not local-only). This ensures:
- All developers use the same instructions
- All developers use the same Git hooks
- CI/CD uses the same quality gates

To exclude specific files from being committed, add them to `.gitignore` BEFORE running bootstrap.

⚠️ **gitleaks blocks commits with secrets**

If a developer commits a secret accidentally, the pre-commit hook will reject the commit. If the secret reaches history:
1. Alert the service provider immediately and rotate the secret
2. Use `git filter-branch` or `BFG Repo-Cleaner` to remove it from history
3. Force-push the corrected branch

⚠️ **All developers need gitleaks installed**

After bootstrap, every developer must have `gitleaks` installed for Git hooks to work. See [Troubleshooting - gitleaks not found](TROUBLESHOOTING.md#issue-gitleaks-not-found).

## Customization

### Modify Copilot instructions

Edit `.github/copilot-instructions.md` after bootstrap to customize guidance for your team.

### Customize gitleaks rules

Edit `.gitleaks.toml` to:
- Add patterns to detect project-specific secrets
- Add allowlist entries to suppress false positives

### Customize Git hooks

Edit `.githooks/pre-commit` and `.githooks/pre-push` to add additional checks.

## Troubleshooting

See [Troubleshooting](TROUBLESHOOTING.md) for common issues:
- [gitleaks not found](TROUBLESHOOTING.md#issue-gitleaks-not-found)
- [Git hooks fail after bootstrap](TROUBLESHOOTING.md#issue-git-hooks-fail-immediately-after-bootstrap)
- [File already exists errors](TROUBLESHOOTING.md#issue-githubcopilot-instructionsmd-already-exists)

## See also

- [Home Sync](HOME_SYNC.md)
- [Getting Started](GETTING_STARTED.md)
- [Quality Gates](QUALITY_GATES.md)
