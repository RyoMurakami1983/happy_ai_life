# AI Reproducibility / Stability / Security Roadmap

## 目的

Copilot CLI に `happy_ai_life` の改善を依頼するための atomic issue roadmap。  
優先順位は **AI 再現性 → 安定性 → セキュリティ実効性 → 運用性** の順で置く。

## 共通ルール

- 1 Issue = 1 branch = 1 PR。
- Issue の「非対象」に触れない。
- protected path を変更する場合は、PR 本文に理由、影響、rollback を書く。
- local 確認と CI 確認を一致させる。
- docs、policy、tests、script のどれかだけを直して終わらない。

## Phase 0: policy source of truth を作る

### 1. [P0] guard policy を単一 JSON として外部化する

目的:

- protected path、deny command、ask path、required tools、review required path を一箇所に集約する。

実装範囲:

- `policy/guard-policy.json`
- `policy/guard-policy.schema.json`
- policy validation test
- docs から policy への参照

非対象:

- guard script の全面置換
- CI workflow の変更

完了条件:

- [ ] policy JSON がある。
- [ ] schema がある。
- [ ] protected path と deny command が policy に含まれる。
- [ ] docs が policy を source of truth として参照している。
- [ ] validation test がある。

### 2. [P0] protected path list を governance docs / scripts / home-template まで拡張する

目的:

- security boundary に関わる docs と scripts を protected path に含める。

実装範囲:

- `policy/guard-policy.json`
- docs
- tests

非対象:

- guard engine の実装変更

完了条件:

- [ ] `docs/TRUST_BOUNDARY.md` が protected path に含まれる。
- [ ] `docs/HOOKS_GOVERNANCE.md` が protected path に含まれる。
- [ ] `scripts/sync-to-home.ps1` が protected path に含まれる。
- [ ] `scripts/sync-to-repo.ps1` が protected path に含まれる。
- [ ] `scripts/repo-secure-check.ps1` が protected path に含まれる。
- [ ] `home-template/.copilot/**` が protected path に含まれる。

## Phase 1: guard parity を作る

### 3. [P0] shared guard policy engine を追加する

目的:

- PowerShell / Bash で判断ロジックを二重実装しない。

実装範囲:

- `.github/hooks/scripts/guard_policy.py` または `scripts/guard_policy.py`
- unit tests

非対象:

- wrapper の置換
- policy 内容の大幅変更

完了条件:

- [ ] hook payload を parse できる。
- [ ] `permissionRequest` / `preToolUse` の response を分けられる。
- [ ] `bash` / `powershell` command を評価できる。
- [ ] `create` / `edit` path を評価できる。
- [ ] deny / ask / allow を返せる。

### 4. [P0] PowerShell / Bash guard を thin wrapper 化する

目的:

- OS による判断差をなくす。

実装範囲:

- `.github/hooks/scripts/guard_pre_tool.ps1`
- `.github/hooks/scripts/guard_pre_tool.sh`
- home sync の配布対象
- tests

非対象:

- 新しい deny rule の追加

完了条件:

- [ ] PowerShell wrapper は shared engine を呼ぶだけになる。
- [ ] Bash wrapper は shared engine を呼ぶだけになる。
- [ ] wrapper 固有の policy 判断が残っていない。
- [ ] Windows / macOS / Linux で同じ fixture が同じ結果になる。

### 5. [P0] create / edit protected path 監視を cross-platform fixture で検証する

目的:

- file operation 監視を shell 依存にしない。

実装範囲:

- guard engine tests
- hook parity tests

非対象:

- protected path の追加変更

完了条件:

- [ ] `create` payload で protected path が ask になる。
- [ ] `edit` payload で protected path が ask になる。
- [ ] nested JSON / stringified JSON payload を処理できる。
- [ ] `permissionRequest` では ask せず normal flow に渡る。

## Phase 2: CI を local guide と一致させる

### 6. [P0] CI に full pytest / ruff / ty を追加する

目的:

- README / DEVELOPMENT に書かれた local quality gate と CI を一致させる。

実装範囲:

- `.github/workflows/quality.yml`
- docs
- tests if needed

非対象:

- workflow action の SHA pinning 方針変更

完了条件:

- [ ] CI で `uv sync --dev --frozen` が走る。
- [ ] CI で `uv run pytest -q` が走る。
- [ ] CI で `uv run ruff check .` が走る。
- [ ] CI で `uv run ty check .` が走る。
- [ ] README / DEVELOPMENT と矛盾しない。

### 7. [P1] workflow policy tests を CI に含める

目的:

- SHA pinning、hook parity、policy consistency を CI で検出する。

実装範囲:

- `.github/workflows/quality.yml`
- tests

非対象:

- policy 内容の大幅変更

完了条件:

- [ ] `tests/test_workflow_sha_pinning.py` が CI で走る。
- [ ] policy consistency tests が CI で走る。
- [ ] hook parity job と full quality job の責務が明確に分かれている。

## Phase 3: review governance を実効化する

### 8. [P1] `.github/CODEOWNERS` を追加する

目的:

- security boundary 変更を human review に乗せる。

実装範囲:

- `.github/CODEOWNERS`
- docs

非対象:

- GitHub UI 上の Rulesets 自動設定

完了条件:

- [ ] `.github/**` に owner がある。
- [ ] `.githooks/**` に owner がある。
- [ ] `scripts/**` に owner がある。
- [ ] `home-template/.copilot/**` に owner がある。
- [ ] security governance docs に owner がある。

### 9. [P1] PR template に AI 再現性・security boundary 確認欄を追加する

目的:

- Copilot CLI が PR 本文で同じ情報を出すようにする。

実装範囲:

- `.github/PULL_REQUEST_TEMPLATE.md`
- docs

非対象:

- Issue template 全面整備

完了条件:

- [ ] Goal が書ける欄がある。
- [ ] Non-goal / 非対象が書ける欄がある。
- [ ] protected path 変更の有無が書ける。
- [ ] 確認コマンド結果が書ける。
- [ ] rollback が書ける。

## Phase 4: toolchain 再現性を上げる

### 10. [P1] tool version policy を追加する

目的:

- git / gitleaks / pwsh / jq / node / gh / dotnet の最低 version を明確にする。

実装範囲:

- `policy/tool-versions.json` または `policy/guard-policy.json`
- docs
- tests

非対象:

- tool の自動 install

完了条件:

- [ ] required tool と minimum version が定義されている。
- [ ] OS / feature に応じた optional tool が定義されている。
- [ ] docs に install ではなく確認方針が書かれている。

### 11. [P1] `repo-secure-check.ps1 -Strict` で tool version を検査する

目的:

- tool が存在するだけでなく、互換性がある version か確認する。

実装範囲:

- `scripts/repo-secure-check.ps1`
- tests
- docs

非対象:

- tool の自動更新

完了条件:

- [ ] version parse がある。
- [ ] minimum version 未満なら `toolDependencies` missing または warning になる。
- [ ] `-Strict` では non-zero exit になる。
- [ ] 既定モードの互換性が維持される。

## Phase 5: naming と profile を整理する

### 12. [P1] `Enterprise` profile を分割または改名する

目的:

- `Enterprise` が Windows desktop / Tauri / proxy build を意味してしまう曖昧さを消す。

実装範囲:

- `scripts/sync-to-repo.ps1`
- `repo-template/.github/instructions/*.instructions.md`
- docs
- tests

非対象:

- 新しい enterprise policy の全面設計

完了条件:

- [ ] security general profile と Windows desktop profile が分かれている。
- [ ] 既存 profile との migration note がある。
- [ ] 既定 profile は `HappyDefault` で、`EnterpriseStrict` は opt-in になっている。
- [ ] AI が enterprise = Windows desktop と誤解しない説明になっている。

## Phase 6: remote governance を補助する

### 13. [P2] remote Rulesets / Branch Protection check の設計文書を追加する

目的:

- local check で見えない GitHub remote 設定の確認方針を定義する。

実装範囲:

- docs
- optional script design

非対象:

- GitHub API 実装

完了条件:

- [ ] local check と remote check の責務が分かれている。
- [ ] `gh` / GitHub API で確認できる項目が整理されている。
- [ ] GitHub UI 目視が必要な項目が整理されている。

### 14. [P2] `repo-remote-security-check` を追加する

目的:

- Rulesets / Branch Protection / Required checks の一部を機械確認する。

実装範囲:

- new script
- docs
- tests where possible

非対象:

- organization policy の変更

完了条件:

- [ ] required check `gitleaks` の存在を確認できる。
- [ ] branch protection / ruleset の取得失敗を明確に report できる。
- [ ] 権限不足時に false OK を返さない。
