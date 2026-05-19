# Resolve Enterprise Security Issue

この prompt は、Copilot CLI に enterprise security hardening の Issue を 1 件ずつ解決させるために使う。

## 必ず読む

作業前に次を読むこと。

- `docs/ENTERPRISE_SECURITY_REVIEW.md`
- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/ISSUE_ROADMAP_ENTERPRISE_SECURITY.md`
- `docs/adr/2026-05-08-enterprise-global-guard-policy.md`
- 対象 Issue 本文

## 作業ルール

- 対象 Issue を 1 件だけ解決する。
- Issue に書かれた実装範囲を超えない。
- Issue に書かれた非対象は実施しない。
- security policy を弱めない。
- repo-scoped hooks を信頼の根として扱わない。
- protected path を変更する場合は、理由、影響、確認方法を PR 本文に書く。
- 変更は最小化する。
- docs と実装が矛盾しないようにする。
- 実行できる確認は実行する。
- 実行できない確認は、理由と代替確認を PR 本文に書く。

## 禁止事項

- `--no-verify` を使わない。
- `git commit -n` を使わない。
- force push しない。
- hook / CI / secret scan を弱めない。
- protected path を unrelated change として変更しない。
- Issue 外の大規模 refactor をしない。
- session-continuity hooks を標準で有効化しない。

## PR に書くこと

PR 本文には次を必ず書く。

~~~markdown
## 対応 Issue

Closes #<issue-number>

## 変更内容

- 

## 変更しなかったこと

- 

## 確認結果

[Windows: PowerShell]
```powershell
$ <実行したコマンド>
```

結果:

```text
<結果の要約>
```

## Security impact

- protected path 変更: あり / なし
- hook 変更: あり / なし
- workflow 変更: あり / なし
- MCP / skill 権限変更: あり / なし

## 残課題

- 
~~~

## 確認コマンド候補

[Windows: PowerShell]
```powershell
$ uv run pytest -q
$ uv run ruff check .
$ uv run ty check .
```

[Windows: PowerShell]
```powershell
$ & $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath .
```

`-Strict` 追加後:

[Windows: PowerShell]
```powershell
$ & $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath . -Strict
```
