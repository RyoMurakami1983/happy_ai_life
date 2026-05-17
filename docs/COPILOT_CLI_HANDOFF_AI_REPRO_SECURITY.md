# Copilot CLI Handoff: AI 再現性・安定性・セキュリティ強化

## 目的

この資料は、`happy_ai_life` を **AI との共同作業を再現可能・安定・セキュアに行うための開発基盤**として強化するための Copilot CLI 向け handoff である。

単なるセキュリティ強化ではない。目的は次の 3 つを同時に満たすこと。

1. **AI 再現性** — 同じ Issue、同じ Reference、同じ policy なら、OS や shell によって AI の判断がぶれない。
2. **安定性** — local と CI の確認結果が一致し、導入漏れや tool 不足が早期に検出される。
3. **セキュリティ** — repo-scoped hooks を信頼の根にせず、user-level / enterprise-level guard と server-side governance で補う。

## 最上位 GOAL

### G0: AI が安全に、同じ判断基準で、同じ作業境界を再現できる状態にする

成功状態:

- PowerShell / Bash / Windows / macOS / Linux で guard の判断結果が一致する。
- protected path、deny command、required tools、review-required path が単一の policy から説明できる。
- AI が security boundary を触る場合は、明示的な `ask` または human review に進む。
- 通常の source code / docs / tests 変更は過剰に止めない。
- local の品質確認と CI の品質確認が一致する。
- policy、docs、tests、script が drift しない。

## 非 GOAL

この作業でやらないこと。

- セキュリティを理由に AI の通常開発能力を狭めすぎること。
- すべての protected path 変更を無条件 deny すること。
- repo-scoped hooks を信頼の根に戻すこと。
- hooks を脆弱性 scanner や EDR の代替にすること。
- organization policy や GitHub Rulesets をこの repository だけで完全自動設定すること。
- user-owned な `$HOME/.copilot/mcp-config.json` や個人設定を上書きすること。

## 絶対制約

### C1: AI 再現性を犠牲にしない

セキュリティ強化は、AI の判断基準を明確にし、再現性を上げる方向で行う。

悪い例:

- OS ごとに別々の deny 条件を持つ。
- docs と script で protected path が違う。
- CI では一部 test しか見ず、local guide だけ full check を要求する。
- false positive が多すぎて通常開発が止まる。

良い例:

- `policy/guard-policy.json` と `policy/guard-policy.schema.json` を source of truth にする。
- PowerShell / Bash wrapper は同じ policy engine を呼ぶだけにする。
- protected path 変更は原則 `ask` にし、明確な bypass / destructive command だけ `deny` にする。
- local と CI で同じ確認コマンドを走らせる。

### C2: repo-scoped hooks を信頼の根にしない

`.github/hooks/**` は repository 内で変更できるため、信頼の根ではない。  
user-level / enterprise-level guard、GitHub Rulesets / Branch Protection / Required checks を上位に置く。

### C3: policy drift を作らない

protected path、deny command、tool dependency、review-required path は、可能な限り一箇所に集約する。

最低限、次の一致を tests で確認する。

- policy JSON
- guard engine
- docs
- tests
- generated / referenced protected path list

### C4: 1 Issue = 1 branch = 1 PR

特に guard、CI、workflow、security docs、MCP、skills、CODEOWNERS の変更は混ぜない。  
レビュー不能になるため、複数テーマの同時修正は禁止する。

### C5: 通常開発を過剰に止めない

guard は通常の source code、docs、tests、lint、format を止めない。  
security boundary に触る変更だけを `ask` または `deny` にする。

### C6: 日本語主体を維持する

README、docs、Issue、PR 本文、commit message は日本語を既定にする。  
CLI command、path、API 名、tool 名は英語のままでよい。

## 現状評価から見えた主要課題

### 課題 1: PowerShell guard と Bash guard の policy parity が崩れている

PowerShell 側には `create` / `edit` の protected path 監視、`permissionRequest` 分岐、Git hooks 無効化系 command の検出が入っている。  
一方、Bash 側は shell command 監視中心で、file operation 監視や `permissionRequest` 対応が弱い。

これは OS によって AI の許可判断が変わるため、AI 再現性の問題である。

目標:

- PowerShell / Bash は同じ policy engine を呼ぶ thin wrapper にする。
- 判断ロジックは単一実装にする。
- OS 差異は wrapper と path normalization に閉じ込める。

### 課題 2: CI が full quality gate になっていない

README では `pytest` / `ruff` / `ty` を PR 前確認としているが、現行 CI は `gitleaks` と hook parity が中心で、full test / lint / type check が必ず走る構成ではない。

目標:

- CI に full pytest / ruff / ty を追加する。
- local guide と CI の確認コマンドを一致させる。
- AI が「CI が source of truth」と判断できる状態にする。

### 課題 3: protected path policy が分散している

protected path が docs、PowerShell script、tests に分散している。  
このままだと、今後 Copilot CLI に複数 Issue を処理させたときに drift する。

目標:

- `policy/guard-policy.json` と `policy/guard-policy.schema.json` を source of truth にする。
- docs / tests / guard engine は policy を参照するか、一致を検証する。

### 課題 4: tool version の再現性が弱い

Python dependencies は `uv.lock` で固定されているが、`git`、`gitleaks`、`pwsh`、`jq`、`node`、`gh`、`dotnet` の version policy は弱い。

目標:

- `policy/tool-versions.json` または `policy/guard-policy.json` に最低 version を持つ。
- `repo-secure-check.ps1 -Strict` で最低 version を検査する。

### 課題 5: `Enterprise` profile の意味が広すぎる

現在の `enterprise.instructions.md` は Windows desktop / Tauri / Cargo / proxy 寄りであり、名前の `Enterprise` より狭い。

目標:

- `EnterpriseSecurity` と `EnterpriseWindowsDesktop` などに分ける。
- AI が enterprise = Windows desktop と誤解しないようにする。

## 目標アーキテクチャ

```text
policy/
├── guard-policy.json
├── guard-policy.schema.json
└── tool-versions.json              # 必要なら分離

.github/hooks/scripts/
├── guard_pre_tool.ps1              # thin wrapper
└── guard_pre_tool.sh               # thin wrapper

scripts/
└── guard_policy.py                 # 単一 policy engine

tests/
├── test_guard_policy_engine.py
├── test_guard_policy_docs_consistency.py
├── test_guard_wrappers.py
├── test_workflow_quality_gate.py
└── test_repo_secure_check.py
```

## policy engine の責務

policy engine が担当すること:

- hook payload を parse する。
- `toolName` / `tool_name` を正規化する。
- `toolArgs` / `tool_input` を正規化する。
- `bash` / `powershell` command を評価する。
- `create` / `edit` の path payload を評価する。
- protected path に一致する場合は `ask` を返す。
- 明確な bypass / destructive command は `deny` を返す。
- event が `permissionRequest` の場合、`ask` ではなく通常 permission flow へ流す。
- response schema を event ごとに正しく出す。

policy engine が担当しないこと:

- 外部 tool の自動 install。
- GitHub remote Rulesets の自動設定。
- secret の本文表示。
- organization policy の置き換え。

## deny / ask / allow の基準

### deny

明確な bypass / destructive command は deny。

例:

- `git commit --no-verify`
- `git commit -n`
- `git push --no-verify`
- `git push -f`
- `git push --force`
- `git push --force-with-lease`
- `git reset --hard`
- `git config core.hooksPath ...`
- `git config --unset core.hooksPath`
- `git -c core.hooksPath=...`
- `git update-index --skip-worktree ...`
- `git update-index --assume-unchanged ...`
- `powershell -EncodedCommand`
- `pwsh -EncodedCommand`
- `Invoke-Expression`
- `iex`
- `curl ... | sh`
- `wget ... | sh`
- `rm -rf /`
- `rm -rf .`

### ask

security boundary に触るが、正当な変更もあり得るものは ask。

例:

- `.github/hooks/**`
- `.githooks/**`
- `.github/workflows/**`
- `.github/copilot-instructions.md`
- `.github/instructions/**`
- `.github/skills/**`
- `.agents/skills/**`
- `.claude/skills/**`
- `.github/mcp.json`
- `.mcp.json`
- `.gitleaks.toml`
- `SECURITY.md`
- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/ENTERPRISE_SECURITY_REVIEW.md`
- `docs/ENTERPRISE_SECURITY.md`
- `docs/ISSUE_ROADMAP_ENTERPRISE_SECURITY.md`
- `scripts/sync-to-home.ps1`
- `scripts/sync-to-repo.ps1`
- `scripts/repo-secure-check.ps1`
- `home-template/.copilot/**`
- `$HOME/.copilot/**`

### allow

通常開発は allow。

例:

- application source code の変更
- tests の追加
- docs の通常追記
- lint / format / test 実行
- read-only investigation

## 確認コマンド

local と CI で同じ品質ゲートを目指す。

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

## Copilot CLI への作業原則

Copilot CLI は次を守る。

1. 対象 Issue を 1 件だけ解決する。
2. この handoff、Roadmap、Trust Boundary、Hooks Governance を先に読む。
3. GOAL、制約、非 GOAL、完了条件を満たす最小変更にする。
4. policy を弱めない。
5. AI 再現性を下げる二重実装や暗黙挙動を増やさない。
6. 実装後に確認コマンドを実行する。
7. 実行できない確認は、理由と代替確認を PR 本文に書く。
8. protected path 変更は PR 本文に理由、影響、rollback を書く。

## Definition of Done

全体完了条件:

- policy が単一 source of truth になっている。
- PowerShell / Bash / Windows / macOS / Linux で guard 判断が一致する。
- CI が full pytest / ruff / ty / gitleaks / hook parity を実行する。
- `repo-secure-check.ps1 -Strict` が導入漏れと tool version 不足を検出する。
- protected path 変更が `ask` または human review に乗る。
- docs / tests / script が policy と矛盾しない。
- AI の通常開発が過剰に block されない。
