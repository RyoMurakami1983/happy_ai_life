# Enterprise Security Issue Roadmap

## 目的

Copilot CLI を用いた AI 共同作業環境を、企業利用にも耐える安全性・安定性・再現性を持つ構成へ強化する。

この Roadmap は、Issue を atomic に分割し、Copilot CLI に順番通り依頼するための基準である。

## 共通方針

- 1 Issue = 1 branch = 1 PR を原則とする。
- security / hooks / workflow / MCP / skill を触る PR は人間レビュー必須とする。
- repo-scoped hooks は信頼の根ではなく補助ガードとする。
- user-level / enterprise-level guard を最上位の安全弁とする。
- protected path 変更は明示的に扱う。
- docs と実装が矛盾する場合は、先に docs を直して判断基準を固定する。
- Issue の「非対象」に書かれた作業は行わない。

## 共通 Reference

各 Issue は、必要に応じて次の文書を参照する。

- `docs/ENTERPRISE_SECURITY_REVIEW.md`
- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/ISSUE_ROADMAP_ENTERPRISE_SECURITY.md`
- `docs/adr/2026-05-08-enterprise-global-guard-policy.md`
- `docs/copilot-prompts/resolve-enterprise-security-issue.md`

## Phase 0: 判断基準を固定する

### 1. [P0] Enterprise security review reference documents を追加する

目的:

- 今回の enterprise security review を repository 内の Reference として固定する。

実装範囲:

- `docs/ENTERPRISE_SECURITY_REVIEW.md`
- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/ISSUE_ROADMAP_ENTERPRISE_SECURITY.md`
- `docs/adr/2026-05-08-enterprise-global-guard-policy.md`
- `docs/copilot-prompts/resolve-enterprise-security-issue.md`

非対象:

- script 実装変更
- hooks 変更
- workflow 変更

完了条件:

- [ ] Reference docs が追加されている。
- [ ] repo-scoped hooks を信頼の根にしない方針が明記されている。
- [ ] Issue Roadmap に順番と依存関係がある。
- [ ] Copilot CLI 用 prompt がある。

### 2. [P0] repo-scoped hooks は信頼の根ではなく補助ガードであることを明文化する

目的:

- `.github/hooks/` の位置づけを補助ガードとして明確化する。

実装範囲:

- `docs/TRUST_BOUNDARY.md`
- `docs/HOOKS_GOVERNANCE.md`
- `docs/REFERENCE.md`
- 必要なら `docs/REPO_BOOTSTRAP.md`

非対象:

- hook script の変更
- home sync の変更

完了条件:

- [ ] repo-scoped hooks の trust level が明記されている。
- [ ] user-level / enterprise-level guard が優先されることが明記されている。
- [ ] Repo Bootstrap の説明と矛盾していない。

### 3. [P0] home instructions の Hooks 方針を user-level guard 優先へ修正する

目的:

- `home-template/.copilot/copilot-instructions.md` の Hooks 方針を現実の設計に合わせる。

実装範囲:

- `home-template/.copilot/copilot-instructions.md`
- 必要なら `docs/HOME_SYNC.md`

非対象:

- hook script の変更
- `config.json` merge logic の変更

完了条件:

- [ ] repo hooks を正とする表現が削除または修正されている。
- [ ] user-level guard を最上位の安全弁とする方針が書かれている。
- [ ] repo-specific instructions は repository 事実に限って優先される、と書かれている。

### 4. [P0] user-level safety hook を enterprise/global guard として正式化する

目的:

- `$HOME/.copilot/config.json` に入る managed な enterprise/global guard entry を正式名称として docs / naming に反映する。

実装範囲:

- `scripts/sync-to-home.ps1`
- `docs/HOME_SYNC.md`
- `docs/HOOKS_GOVERNANCE.md`
- test がある場合は該当 test

非対象:

- protected path detection の本格実装
- permissionRequest hook 追加

完了条件:

- [ ] managed enterprise/global guard entry の位置づけが説明されている。
- [ ] user-owned `config.json` を壊さない方針が維持されている。
- [ ] 既存 hook id との互換性が考慮されている。

## Phase 1: global guard の安全性を上げる

### 5. [P0] protected path 変更を global guard で検出・制御する

目的:

- hooks / workflows / instructions / MCP / skills などの protected path を AI が不用意に変更しないようにする。

実装範囲:

- user-level guard script
- protected path list
- docs / tests

非対象:

- repo-scoped hook の改修
- GitHub Rulesets の設定

完了条件:

- [ ] protected path list が定義されている。
- [ ] `edit` / `create` による protected path 変更が検出対象になる。
- [ ] block / ask / allow の方針が tests または docs に反映されている。

### 6. [P0] hook 実行に必要な依存ツールの preflight check を追加する

目的:

- hooks が動いているつもりで実際は依存 tool 不足により機能していない状態を避ける。

実装範囲:

- `repo-secure-check.ps1`
- 必要なら user-level guard script
- docs / tests

非対象:

- tool の自動インストール

完了条件:

- [ ] `git` / `gitleaks` / `pwsh or powershell` の存在確認がある。
- [ ] active な thin wrapper から shared Python engine を起動できる `python3 or python or py -3` の存在確認がある。
- [ ] session-continuity 有効時に `node` の存在確認がある。
- [ ] GitHub 連携機能使用時に `gh` の存在確認がある。

### 7. [P0] `ExecutionPolicy Bypass` の既定使用をやめ opt-in 化する

目的:

- 企業管理端末での PowerShell 実行ポリシーを尊重する。

実装範囲:

- `scripts/sync-to-home.ps1`
- `.github/hooks/safety-guard.json`
- docs / tests

非対象:

- 署名済み script 配布

完了条件:

- [ ] 既定では `-ExecutionPolicy Bypass` を付けない。
- [ ] 必要時のみ環境変数で opt-in できる。
- [ ] migration note が docs にある。

### 8. [P1] `permissionRequest` hook を追加して tool 許可前の安全確認を行う

目的:

- permission service より前に global guard を通し、CI / pipe mode でも安全判断できるようにする。

実装範囲:

- user-level hook entry
- guard script
- docs / tests

非対象:

- repo-scoped hook の permissionRequest 化

完了条件:

- [ ] `permissionRequest` hook が managed entry に追加されている。
- [ ] deny 時の message が agent に返る。
- [ ] fallback behavior が明記されている。

### 9. [P1] `edit` / `create` tool による protected path 書き換えを監視する

目的:

- shell command 以外の file operation で protected path が変更される経路を塞ぐ。

実装範囲:

- guard script
- tests
- docs

非対象:

- full policy engine 化

完了条件:

- [ ] `edit` tool の payload から path を抽出できる。
- [ ] `create` tool の payload から path を抽出できる。
- [ ] protected path では deny または ask になる。

## Phase 2: Git / CI bypass 対策

### 10. [P0] `repo-secure-check.ps1` に `-Strict` を追加し失敗時に non-zero exit する

目的:

- 導入漏れを CI / automation で失敗扱いにできるようにする。

実装範囲:

- `scripts/repo-secure-check.ps1`
- tests
- docs

非対象:

- 脆弱性 scanner 化

完了条件:

- [ ] `-Strict` 指定時、missing があれば non-zero exit する。
- [ ] `-AsJson` と併用できる。
- [ ] 既定挙動との互換性がある。

### 11. [P1] Git hook 無効化につながる Git コマンドを guard に追加する

目的:

- AI が Git hooks を無効化する操作を防ぐ。

実装範囲:

- guard script
- tests
- docs

非対象:

- GitHub Rulesets 実装

完了条件:

- [ ] `git config core.hooksPath` を検出する。
- [ ] `git update-index --skip-worktree` を検出する。
- [ ] `git update-index --assume-unchanged` を検出する。

### 12. [P1] 危険コマンド blocklist を企業利用向けに拡張する

目的:

- destructive command や bypass command の検出範囲を広げる。

実装範囲:

- guard script
- tests
- docs

非対象:

- sandbox 実行基盤

完了条件:

- [ ] `git push -f` を検出する。
- [ ] `git push --force-with-lease` を検出する。
- [ ] `EncodedCommand` / `Invoke-Expression` / `iex` を検出する。
- [ ] `curl | sh` / `wget | sh` を検出する。

### 13. [P1] Branch Protection / Rulesets の必須設定手順を docs 化する

目的:

- Git hooks だけに依存しない server-side governance を明確化する。

実装範囲:

- `docs/ENTERPRISE_SECURITY.md` または dedicated docs
- README / REFERENCE からの導線

非対象:

- GitHub API での自動設定

完了条件:

- [ ] Direct push 禁止が書かれている。
- [ ] Required status checks が書かれている。
- [ ] gitleaks required check が書かれている。
- [ ] CODEOWNERS review が書かれている。

### 14. [P1] GitHub Actions の third-party actions を SHA pinning する

目的:

- CI supply chain risk を下げる。

実装範囲:

- `.github/workflows/*.yml`
- `repo-template/.github/workflows/*.yml`
- docs

非対象:

- organization policy 設定

完了条件:

- [ ] third-party actions が SHA pinning されている。
- [ ] 更新手順が docs にある。
- [ ] dependabot 等で更新する方針が書かれている。

## Phase 3: governance 文書を固める

### 15. [P1] `SECURITY.md` を追加し secret 漏洩時の対応手順を定義する

### 16. [P1] `docs/TRUST_BOUNDARY.md` を見直し trust level / protected path / 優先順位を更新する

### 17. [P1] `docs/HOOKS_GOVERNANCE.md` を見直し global guard / repo hook / Git hook の governance を更新する

### 18. [P1] MCP server 追加・変更を governance 対象として docs 化する

### 19. [P1] repo-local skills の `allowed-tools: "*"` を禁止または警告する policy を追加する

## Phase 4: 運用性・保守性

### 20. [P2] `managed-manifest.json` を追加し home sync の管理対象を明示する

### 21. [P2] `sync-to-repo.ps1` に `-PolicyProfile Enterprise` を追加する

### 22. [P2] session-continuity hook 由来の prompt injection 対策を強化する

### 23. [P2] Windows / macOS / Linux の hook parity を確認するテストを追加する

### 24. [P2] enterprise 向け導入手順を `docs/ENTERPRISE_SECURITY.md` にまとめる

## Copilot CLI への依頼文テンプレート

```text
対象 Issue を 1 件だけ解決してください。
必ず docs/ENTERPRISE_SECURITY_REVIEW.md、docs/TRUST_BOUNDARY.md、docs/HOOKS_GOVERNANCE.md、docs/ISSUE_ROADMAP_ENTERPRISE_SECURITY.md、関連 ADR を読んでください。
この Issue の「実装範囲」外の変更はしないでください。
完了条件を満たす最小変更にしてください。
変更後に確認コマンドを実行し、結果を PR 本文に書いてください。
security policy を弱める変更は禁止です。
repo-scoped hooks を信頼の根として扱わないでください。
```

## 共通確認コマンド

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
