# Team Repo Setup

Team Repo Setup は、既存の別 repo に HappyDefault の Copilot guidance、Git hooks、品質ゲートを入れるための advanced 手順です。

日常利用の入口ではありません。個人作業やこの repo の通常開発だけなら不要です。

## 入るもの

- `.github/copilot-instructions.md`
- `.github/hooks/`
- `.github/workflows/*.yml`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `policy/guard-policy.json`
- `policy/guard-policy.schema.json`

## 手順

[Windows: PowerShell]
```powershell
# まず状態確認
& $HOME\.copilot\scripts\repo-secure-check.ps1 -TargetRepoPath C:\your-repo

# dry-run
& $HOME\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\your-repo -DryRun

# HappyDefault で反映
& $HOME\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\your-repo -PolicyProfile HappyDefault

# Git hooks を有効化
& $HOME\.copilot\scripts\install-git-hooks.ps1 -TargetRepoPath C:\your-repo
```

## profile

| profile | 用途 |
|---|---|
| `HappyDefault` | 軽量な既定 |
| `Secure` | security baseline を明示したい repo |
| `EnterpriseStrict` | 重い governance を opt-in する場合 |
| `WindowsDesktop` | Windows desktop / Tauri / proxy 前提を意識する repo |

`Default` は `HappyDefault`、`Enterprise` は `EnterpriseStrict` の互換 alias です。

## 注意

- 変更は対象 repo に commit されます。
- secret scan、hook bypass 禁止、force push 禁止、破壊的操作の禁止は弱めません。
- 旧 `REPO_BOOTSTRAP.md` は `archive/enterprise-hardening/docs/REPO_BOOTSTRAP.md` に退避しています。
