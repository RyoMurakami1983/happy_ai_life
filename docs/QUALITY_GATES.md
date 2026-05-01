# Quality Gates Configuration

This repository uses GitHub Actions to enforce quality standards on all pull requests. These gates prevent common issues before code is merged.

## What are quality gates?

Quality gates are automated checks that run on every PR:

1. **Secret detection (gitleaks)** — Scans for accidentally committed secrets, API keys, credentials
2. **Markdown lint (textlint, optional)** — Enforces documentation standards

All checks must pass before a PR can be merged.

## Secret Detection with gitleaks

### What gets checked

- All staged files in the PR
- Commit history in the PR branch
- Common secret patterns: API keys, tokens, AWS keys, database passwords, etc.

### How gitleaks works

1. **Pre-commit hook** (client-side)
   - Runs when you type `git commit`
   - Scans staged files only
   - Stops the commit if secrets are detected

2. **Pre-push hook** (client-side)
   - Runs when you type `git push`
   - Scans commits you're about to push
   - Extra safety check before remote push

3. **GitHub Action** (server-side)
   - Runs on every PR
   - Full repository scan
   - Public verification that PR is secret-free

### Configuration

The default gitleaks rules are active. To customize detection patterns:

1. Create or edit `.gitleaks.toml` in your repository root (see [.gitleaks.toml](../.gitleaks.toml) in this repo for example)
2. Add entries to `allowlist` to suppress false positives for documentation or non-secret content
3. Restart gitleaks for changes to take effect

### If a secret is detected

1. **In pre-commit hook:** The commit will be rejected. Review the flagged content and remove or obscure the secret.
2. **In pre-push hook:** The push will be rejected. Use the same approach.
3. **In GitHub Action:** The PR check will fail. You must fix it before merging:
   - Remove the secret from the file
   - If it was already committed to history, use `git filter-branch` or `BFG Repo-Cleaner` to remove it from history
   - Force-push the corrected branch

### Best practices

- Never commit secrets intentionally
- Use environment variables or `.env` files (which are `.gitignore`'d) for local secrets
- Use GitHub Secrets for CI/CD credentials
- If you commit a secret accidentally, rotate the secret immediately on the service

## Markdown Linting (textlint, Optional)

### Enabling textlint

Markdown linting is optional. To enable it:

1. Uncomment the `textlint` job in `.github/workflows/quality.yml`
2. Copy `.textlintrc.json` and `package.json` from this repository
3. Run `npm install` locally
4. Add `textlint` as a required status check in GitHub Branch Protection settings

### Configuration

Textlint rules are defined in `.textlintrc.json`. Customize rules to match your documentation style.

## Local Pre-commit Hooks

### gitleaks on commit

The `pre-commit` hook (`.githooks/pre-commit`) runs gitleaks on staged content before each commit:

```powershell
git commit -m "Update documentation"
# Hook runs: scans staged files for secrets
# If secrets found: commit rejected
# If no secrets: commit proceeds
```

### gitleaks on push

The `pre-push` hook (`.githooks/pre-push`) runs gitleaks on the range of commits you're about to push:

```powershell
git push origin main
# Hook runs: scans all commits not yet on remote
# If secrets found: push rejected
# If no secrets: push proceeds
```

### Installing hooks

If hooks are not yet installed in your repository:

```powershell
cd <repository>
git config core.hooksPath .githooks
```

Verify:
```powershell
git config core.hooksPath
# Should output: .githooks
```

## Troubleshooting

See [Troubleshooting](TROUBLESHOOTING.md) for common issues, especially:
- [gitleaks not found in PATH](TROUBLESHOOTING.md#issue-gitleaks-not-found)
- [Pre-commit hooks failing](TROUBLESHOOTING.md#issue-git-hooks-fail-immediately-after-bootstrap)

## See also

- [README](../README.md)
- [Development](DEVELOPMENT.md)
