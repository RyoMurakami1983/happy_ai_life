# [P?] Issue title

## Goal

この Issue で達成する最終状態を書く。

## 背景

なぜ必要かを書く。  
特に AI 再現性、安定性、セキュリティのどれに効くかを書く。

## Reference

- `docs/COPILOT_CLI_HANDOFF_AI_REPRO_SECURITY.md`
- `docs/AI_REPRO_SECURITY_ROADMAP.md`
- `docs/ENTERPRISE_SECURITY_REVIEW.md`
- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/ENTERPRISE_SECURITY.md`

## 実装範囲

- 変更してよい file / directory を列挙する。

## 非対象

- この Issue ではやらないことを列挙する。

## 制約条件

- AI 再現性を下げない。
- security policy を弱めない。
- repo-scoped hooks を信頼の根にしない。
- docs / policy / tests / script の整合を崩さない。
- 通常開発を過剰に block しない。

## 完了条件

- [ ] Goal を満たしている。
- [ ] 非対象に触れていない。
- [ ] tests が追加または更新されている。
- [ ] docs が必要に応じて更新されている。
- [ ] protected path 変更がある場合、理由と rollback が明記されている。
- [ ] local 確認コマンドが実行されている。
- [ ] 実行できない確認は理由が書かれている。

## 確認コマンド

[Windows: PowerShell]
```powershell
$ uv sync --dev --frozen
$ uv run pytest -q
$ uv run ruff check .
$ uv run ty check .
$ & $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath . -Strict
```

[Linux:]
```bash
$ uv sync --dev --frozen
$ uv run pytest -q
$ uv run ruff check .
$ uv run ty check .
```

## Rollback

問題が起きた場合の戻し方を書く。
