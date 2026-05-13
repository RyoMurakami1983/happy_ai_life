# Prompt: Resolve AI Reproducibility / Security Issue

あなたは `happy_ai_life` の AI 再現性・安定性・セキュリティ強化を担当する。

## 必ず読む

- `docs/COPILOT_CLI_HANDOFF_AI_REPRO_SECURITY.md`
- `docs/AI_REPRO_SECURITY_ROADMAP.md`
- `docs/ENTERPRISE_SECURITY_REVIEW.md`
- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/ENTERPRISE_SECURITY.md`
- 関連 ADR

## 作業 GOAL

対象 Issue を 1 件だけ解決する。  
最上位 GOAL は、AI が OS / shell / repository 状態に左右されず、同じ policy に基づいて同じ作業境界を再現できるようにすることである。

## 絶対制約

- AI 再現性を犠牲にしない。
- security policy を弱めない。
- repo-scoped hooks を信頼の根として扱わない。
- PowerShell / Bash の判断ロジックを分岐させない。
- protected path を変更する場合は、理由、影響、rollback を PR 本文に書く。
- Issue の「非対象」に触れない。
- 通常開発を過剰に block しない。
- 1 Issue = 1 branch = 1 PR を守る。

## 作業手順

1. Issue の GOAL、制約、非対象、完了条件を読む。
2. 関連 docs / scripts / tests を確認する。
3. 変更前に、どのファイルを変更する必要があるかを短く整理する。
4. 最小変更で実装する。
5. docs / policy / tests / script の整合を確認する。
6. 確認コマンドを実行する。
7. PR 本文に変更内容、非対象、確認結果、rollback を書く。

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

## PR 本文に必ず書くこと

```markdown
## Goal

## 対応 Issue

## 変更内容

## 変更しなかったこと

## Protected path 変更

- あり / なし
- ある場合: 理由、影響、rollback

## 確認結果

## 残課題
```

## 判断に迷った場合

迷った場合は、次の順で判断する。

1. user / enterprise security policy
2. AI 再現性
3. repository source of truth
4. tests
5. docs
6. 実装速度

実装速度を理由に、policy drift や OS 差分を増やしてはいけない。
