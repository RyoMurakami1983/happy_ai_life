# Troubleshooting

## Installation Issues

### Issue: gitleaks not found

If a Git hook or `repo-secure-check.ps1` reports that `gitleaks` is required but was not found:

#### Symptom

```
Error: gitleaks is required for the pre-commit secret scan, but it was not found in PATH
```

#### Root Cause

The `gitleaks` binary is not available in your PATH environment variable. This tool is required to scan for accidentally committed secrets.

#### Solution

**Step 1: Find the gitleaks executable**

Windows PowerShell:
```powershell
where gitleaks
```

macOS / Linux:
```bash
which gitleaks
```

If this returns nothing, you need to install gitleaks. See https://github.com/gitleaks/gitleaks for installation instructions for your OS.

**Step 2: Once gitleaks is installed, run the hook again**

PowerShell:
```powershell
cd <your-repo>
git commit -m "test message"
```

**Step 3: Make the fix permanent (Optional)**

If you installed gitleaks to a non-standard location, you can set the `GITLEAKS_BIN` environment variable:

Windows PowerShell (temporary):
```powershell
$env:GITLEAKS_BIN = "C:\path\to\gitleaks.exe"
git commit -m "test message"
```

Windows PowerShell (permanent in $PROFILE):
```powershell
# Edit your PowerShell profile
notepad $PROFILE

# Add this line:
$env:GITLEAKS_BIN = "C:\path\to\gitleaks.exe"

# Then reload:
. $PROFILE
```

macOS / Linux (temporary in shell):
```bash
export GITLEAKS_BIN=/usr/local/bin/gitleaks
git commit -m "test message"
```

macOS / Linux (permanent in ~/.bashrc or ~/.zshrc):
```bash
export GITLEAKS_BIN=/usr/local/bin/gitleaks
```

Then reload:
```bash
source ~/.bashrc
# or for zsh:
source ~/.zshrc
```

## Home Sync Issues

### Issue: Sync fails with permission error

**Symptom:**
```
Error: Access denied when writing to $HOME/.copilot/
```

**Solution:**
- Ensure you have write permissions to `$HOME/.copilot/`
- Close any open text editors or terminals accessing files in this directory
- Run `uv run app.py home --dry-run` first to preview changes

### Issue: Old files not removed after sync

**Symptom:**
- Old skill files still exist after running home sync
- Archived files created but not cleaned up

**Solution:**
- Check `$HOME/copilot_archive/` for backed-up files
- Manually remove old files if they conflict with new ones
- Re-run: `uv run app.py home` to retry the sync

## Repo Bootstrap Issues

### Issue: `.github/copilot-instructions.md` already exists

**Symptom:**
```
Error: File already exists: .github/copilot-instructions.md
```

**Solution:**
- If you want to keep your existing file, back it up first:
  ```powershell
  mv .github/copilot-instructions.md .github/copilot-instructions.md.bak
  ```
- Then re-run the bootstrap:
  ```powershell
  & $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath .
  ```

### Issue: Git hooks fail immediately after bootstrap

**Symptom:**
- First commit fails with hook error even though `sync-to-repo.ps1` succeeded

**Solution:**
- Ensure `install-git-hooks.ps1` was run after `sync-to-repo.ps1`:
  ```powershell
  & $HOME/.copilot/scripts/install-git-hooks.ps1 -RepoPath .
  ```
- Verify hooks are installed:
  ```powershell
  git config core.hooksPath
  ```
  Should output: `.githooks`

## Plugin Issues

### Issue: Plugin marketplace not found

**Symptom:**
```
Error: marketplace "happy-ai-life-marketplace" not found
```

**Solution:**
- Add the marketplace first:
  ```powershell
  copilot plugin marketplace add RyoMurakami1983/happy_ai_life
  ```
- Then install the plugins:
  ```powershell
  copilot plugin install happy-core@happy-ai-life-marketplace
  copilot plugin install happy-coding@happy-ai-life-marketplace
  ```

### Issue: Duplicate plugins after updating

**Symptom:**
- Old "direct install" plugins and new marketplace plugins both showing

**Solution:**
- Uninstall the old version:
  ```powershell
  copilot plugin uninstall happy-ai-life
  ```
- Verify only marketplace versions remain:
  ```powershell
  copilot plugin list
  ```

## Getting Help

- Check [FAQ](FAQ.md) for common questions
- See [Reference](REFERENCE.md) for command reference
- Open an issue on GitHub
