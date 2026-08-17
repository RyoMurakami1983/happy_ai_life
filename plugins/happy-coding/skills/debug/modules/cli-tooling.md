# CLI Tooling Module

Use this module when a CLI, plugin manager, installer, local cache, or update / uninstall path fails.

This module was added from a real Copilot CLI plugin update failure where the visible error was `Access is denied`, but ACL, read-only attributes, and file locks were not the owner.

## Evidence to Capture

- **Command matrix**: compare `install`, `update`, `uninstall`, and `update --all` when available.
- **Version and registry state**: CLI version, installed plugin list, marketplace list, remote manifest version.
- **Filesystem state**: installed path, ACL owner, read-only count, create / delete probe, path length, reserved names.
- **Lock state**: process list and Restart Manager lock check for representative files.
- **Minimal probe**: install a tiny local plugin or equivalent fixture to distinguish product-specific data from common CLI behavior.
- **Recovery proof**: after workaround, show the updated version or discovered skill / command.

## Comparison Pattern

Keep one stimulus fixed at a time.

| Question | Compare |
|---|---|
| Is the marketplace or package broken? | remote manifest fetch vs local marketplace browse |
| Is the plugin content broken? | target plugin update vs minimal local plugin update |
| Is it normal filesystem permission? | CLI failure vs direct create / delete in the same directory |
| Is a file locked? | failure vs Restart Manager result for representative files |
| Is workaround safe? | backup + manual delete + fresh install vs final plugin list |

## Copilot CLI Plugin Update Pattern

If `copilot plugin update <plugin>@<marketplace>` fails with `Access is denied`:

1. Reproduce with the exact update command.
2. First close VS Code completely and retry the same update once.
3. Keep the first comparison read-only: `copilot plugin list`, marketplace browse, remote manifest fetch, ACL, lock check, and manual create / delete.
4. Check whether `install` of a minimal local plugin succeeds but `update` / `uninstall` fails.
5. Verify ACL, read-only attributes, direct create / delete, and file locks before blaming permissions.
6. Only after backup, optionally compare with `copilot plugin update --all` to test whether the update path as a whole is failing.
7. If direct delete succeeds and CLI update / uninstall fails, treat it as an update-path failure and use backup + manual delete + fresh install.

Safe recovery shape:

```powershell
$ErrorActionPreference = 'Stop'
$root = "$HOME\.copilot\installed-plugins\<marketplace>"
$backupRoot = "$HOME\.copilot\plugin-backups\<marketplace>-<timestamp>"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
Copy-Item "$root\<plugin>" "$backupRoot\<plugin>" -Recurse -ErrorAction Stop
[System.IO.Directory]::Delete("$root\<plugin>", $true)
copilot plugin install <plugin>@<marketplace>
if ($LASTEXITCODE -ne 0) { throw "<plugin> install failed with exit code $LASTEXITCODE" }
copilot plugin list
```

Do not delete the whole marketplace directory when other plugins from the same marketplace are still installed.

## Distill to Loop Engineering

After the fix, hand off to `loop-engineering` with:

- Fact / Inference / Unknown from the command matrix
- the chosen workaround and why it is safe
- docs or skill text that should prevent the same misdiagnosis
- whether this deserves an eval case or only troubleshooting guidance
