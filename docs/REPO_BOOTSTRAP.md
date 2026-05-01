# Repo Bootstrap: Adding Copilot to Your Project

<!-- TODO: 詳細な repo bootstrap ガイドを記述
構成：
- repo bootstrap とは何か
- Step 1-4 の手順
- Verify checklist
- トラブルシューティング

参考: 現在の README の「Repo-local bootstrap」セクション（91-124行）と注意セクション（112-124行）
-->

## Overview

Repo bootstrap adds Copilot guidance and safety checks to a target repository.

## Steps

### Step 1: Review what will be synced

```powershell
%USERPROFILE%\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\your-repo -DryRun
```

### Step 2: Apply bootstrap

```powershell
%USERPROFILE%\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\your-repo
```

### Step 3: Install Git hooks

```powershell
%USERPROFILE%\.copilot\scripts\install-git-hooks.ps1 -TargetRepoPath C:\your-repo
```

### Step 4: Verify safety setup

```powershell
%USERPROFILE%\.copilot\scripts\repo-secure-check.ps1 -TargetRepoPath C:\your-repo
```

## What gets checked?

<!-- TODO: Verification checklist テーブル -->

## Troubleshooting

<!-- TODO: Common issues -->

See [Troubleshooting](TROUBLESHOOTING.md) for more help.

## See also

- [Home Sync](HOME_SYNC.md)
- [Getting Started](GETTING_STARTED.md)
