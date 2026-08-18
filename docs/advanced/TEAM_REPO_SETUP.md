# Team Repo Setup

Team Repo Setup は、既存の別 repo に HappyDefault の Copilot guidance、Git hooks、品質ゲートを入れるための advanced 手順です。

日常利用の入口ではありません。個人作業やこの repo の通常開発だけなら不要です。

## 入るもの

- `.github/copilot-instructions.md`
- `.github/hooks/`
- `.github/workflows/*.yml`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `.gitattributes`
- `policy/guard-policy.json`
- `policy/guard-policy.schema.json`

## 手順

[Windows: PowerShell]
```powershell
# まず状態確認
& $HOME\.copilot\scripts\repo-secure-check.ps1 -TargetRepoPath C:\your-repo

# dry-run
& $HOME\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\your-repo -PolicyProfile BootstrapMinimal -DryRun

# 初回 bootstrap は BootstrapMinimal
& $HOME\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\your-repo -PolicyProfile BootstrapMinimal

# Git hooks を有効化
& $HOME\.copilot\scripts\install-git-hooks.ps1 -TargetRepoPath C:\your-repo

# blocking 項目が OK になったら HappyDefault へ昇格
& $HOME\.copilot\scripts\repo-secure-check.ps1 -TargetRepoPath C:\your-repo -AsJson
& $HOME\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath C:\your-repo -PolicyProfile HappyDefault
```

## profile

| profile | 用途 |
|---|---|
| `HappyDefault` | 軽量な既定 |
| `BootstrapMinimal` | 初回 onboarding 向け。破壊的 deny と safety-hook / policy 保護は維持し、より広い repo-local protected-path prompt を持ち込まない |
| `Secure` | security baseline を明示したい repo |
| `EnterpriseStrict` | 重い governance を opt-in する場合 |
| `WindowsDesktop` | Windows desktop / Tauri / proxy 前提を意識する repo |

`Default` は `HappyDefault`、`Enterprise` は `EnterpriseStrict` の互換 alias です。

## 注意

- 変更は対象 repo に commit されます。
- secret scan、hook bypass 禁止、force push 禁止、破壊的操作の禁止は弱めません。
- `BootstrapMinimal` は初回導入用です。bootstrap 後は `HappyDefault` へ昇格させてください。
- `policy/guard-policy.json` が欠けた場合や壊れた場合、guard fallback は BootstrapMinimal より強い baseline に戻ることがあります。
- Linux / WSL2 で `BootstrapMinimal` を使う場合は `python3` が必要です。
- `.gitattributes` により `.githooks/**` は LF 固定で配布されます。`repo-secure-check` が line ending を警告した場合は、同期漏れか手編集を疑ってください。
- 旧 `REPO_BOOTSTRAP.md` は `archive/enterprise-hardening/docs/REPO_BOOTSTRAP.md` に退避しています。
