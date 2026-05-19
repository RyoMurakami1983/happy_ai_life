# [P?] <Issue title>

## 目的

この Issue で達成することを書く。

## 背景

なぜ必要かを書く。

## Reference

- `docs/ENTERPRISE_SECURITY_REVIEW.md`
- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/ISSUE_ROADMAP_ENTERPRISE_SECURITY.md`
- `docs/adr/2026-05-08-enterprise-global-guard-policy.md`

## 実装範囲

この Issue で変更してよい範囲を書く。

- 

## 非対象

この Issue ではやらないことを書く。

- 

## 完了条件

- [ ] 
- [ ] 
- [ ] tests または確認手段がある。
- [ ] docs と実装が矛盾していない。
- [ ] security policy を弱めていない。

## 確認コマンド

[Windows: PowerShell]
```powershell
$ uv run pytest -q
$ uv run ruff check .
$ uv run ty check .
```

必要に応じて:

[Windows: PowerShell]
```powershell
$ & $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath .
```

## 注意事項

- repo-scoped hooks を信頼の根として扱わない。
- protected path を変更する場合は、理由、影響、確認方法を PR 本文に書く。
- `--no-verify`、force push、hook / CI / secret scan の無効化は禁止。
- Issue の実装範囲外の変更はしない。
