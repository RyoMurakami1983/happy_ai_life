---
name: impl-and-ship
description: >
  plan artifact を受け取り、bootstrap 確認・実装（TDD）・eval・review・furikaeri・PR・PR review
  までの後半サイクルを 1 つの入口で進める。multirepository 環境では parallel または sequential で実行。
  Use when: 計画が揃っていて実装サイクルを開始したいとき、
  fleet で並列実装するか判断したいとき、実装後の review・furikaeri・PR を一気に進めたいとき。
---

# impl-and-ship — 実装から出荷まで

plan artifact を受け取り、bootstrap 確認から実装・eval gate・review・furikaeri・PR サイクルまでを 1 つの入口でつなぐ skill です。「fleet タイムアウト後の迷い（実装に入るべきか不明）」と「後半フローの責務不在」を解消するために存在します。

## こんなときに使う

このスキルは次のようなときに使います:
- sdd で plan が完成し、実装フェーズに入りたいとき
- plan artifact はあるが、bootstrap が済んでいるか自信がないとき
- fleet で並列実装するか自分で進めるか迷ったとき
- 実装が終わり、review・furikaeri・PR まで一気に通したいとき
- 中断した実装を途中から再開したいとき

## ワークフロー: plan から ship まで通す

### ステップ 1 — plan artifact の確認

plan artifact（plan.md / todos / PLAN summary）を受け取り、実装を開始できる状態かを確認します。以下が揃っているかをチェックします:
- todo リストと受け入れ条件
- 技術的な前提条件とテスト方針の下地
- 戻り先の条件（FAIL → 実装修正、REPLAN_REQUIRED → PLAN mode / design-workshop）

不足があれば PLAN mode に戻ります。

### ステップ 2 — bootstrap 確認

実装対象 repo に入る前に、以下を確認します:
- `repo-secure-check` で local safety valve（repo instructions / Copilot hooks / `.githooks` / `core.hooksPath`）と `.github/workflows/*.yml|*.yaml` を確認する
- `.github/instructions/` が配布済みか確認する。未配布なら `scripts/sync-to-repo.ps1 -TargetRepoPath PATH` で配布するか、理由を plan artifact に残す
- `.github/workflows/` が不足している場合は、repo の技術スタックに合う workflow template を明示的に選んで導入する。CI workflow は repo ごとの差が大きいため、対象 runtime と意図を確認せずに汎用追加しない
- `git init` 済みか、fixed build/test/launch command があるかを確認する
- interactive app なら `impl-and-ship/references/interactive-app-bootstrap-checklist.md` の最低条件を満たすか確認する

Branch Protection / Ruleset はローカルでは未確認として別 warning にします。

### ステップ 3 — contract checkpoint を固定する

今回の slice で何を done とみなすかを固定します。contract（リポ間の provide/require、モジュール間の統合）を含め、最低でも次を残します:
- 今回の対象振る舞い
- 非対象
- 主要な test 観点
- test artifact path / test command / runtime launch command
- multirepository なら、当該リポの他リポへの依存と提供を明示
- `FAIL` なら実装修正、`REPLAN_REQUIRED` なら PLAN mode / design-workshop へ戻る条件

1 受け入れ条件または 1 ユーザー行動を 1 slice として切ります。

### ステップ 4 — fleet 判定

bootstrap と contract が固まった時点で、並列実装を使うか判断します:
- slice が独立しており、タスク数が多く、相互依存が少ない → fleet を検討する
- slice 間に依存があるか、1-2 slice のみ → 自分で順次進める

fleet を選ぶ場合は `/fleet` コマンドで narrow generator として `tdd-coder` を起動します。

### ステップ 4a — 複数リポ環境での Contract 検証（fleet orchestrated のときのみ）

複数リポを fleet で並列実装する場合、実装開始前に **contract_verify** checkpoint を実行し、すべての依存リポの成果物が正しいバージョンで利用可能か確認します:

#### Contract Verification の対象

plan.md の YAML front-matter に `dependencies.contracts.requires` が定義されている場合:
- 各 required artifact が指定パスに存在するか確認
- 各 artifact の SHA256 checksum が plan.md 記載の値と一致するか検証
- 1 つでも不一致 → 実装を開始せず `FAIL` を返し、詳細なエラーメッセージを表示

#### エラーメッセージ例

**Missing artifact**:
```
Contract verification failed:
  - Missing artifact: openapi
    Path: docs/openapi.yaml
    Action: Check if upstream repo merged PR with this artifact
    Remediation: Wait for upstream impl-and-ship to complete
```

**Checksum mismatch**:
```
Contract verification failed:
  - Checksum mismatch: openapi
    Path: docs/openapi.yaml
    Expected: abc123...
    Actual:   xyz789...
    Action: Upstream artifact changed since design handoff
    Remediation: Contact upstream team or re-run design-workshop
```

#### 実装実体

- `checkpoints/contract_verify.py`: `verify_contracts(plan_dict, repo_root) -> CheckpointResult`
- 入力: plan.md YAML front-matter (`dependencies.contracts.requires`)
- 出力: `CheckpointResult(status="PASS"|"FAIL", reason="...")`
- テスト: `tests/test_contract_verify_checkpoint.py`

### ステップ 5 — 実装（TDD の内側ループ）

**このステップは全 slice が完了するまでループします。**

オーケストレーター主導で Red-Green-Refactor サイクルを回しながら実装を進めます。必要なら `tdd-coder` を narrow generator として使います。

- ビルドエラーや計画逸脱が発生したら PLAN mode / `design-workshop` に戻る
- リファクタリングは振る舞い不変を前提に小さく進める
- **セキュリティ中間チェック（イベント駆動）**: 以下の変更が発生したら都度チェックする
  - 認証 / 認可を追加・変更した
  - 外部入力の入口を増やした
  - 機密データの保存 / 転送を追加した
  - 外部 API / Webhook / ファイル I/O / コマンド実行を追加した
  - trust boundary をまたぐデータフローを増やした
  - → 前提が崩れているなら `design-workshop` へ戻す

### ステップ 6 — implementation eval gate（slice ごと）

各 slice の実装後に `implementation-eval-gate` を実行し、verdict を固定します:
- `PASS`: 次の slice へ戻る（ステップ 3 から繰り返す）
- `FAIL`: 同じ plan のまま実装に戻す（ステップ 5 へ）
- `REPLAN_REQUIRED`: PLAN mode または `design-workshop` に戻す

**全 slice が PASS したら外側フロー（ステップ 7 以降）へ進みます。**

### ステップ 7 — pre-PR review（deep-review-preflight）

全 slice 完了後、`deep-review-preflight` を実行して品質とセキュリティを確認します。
- 軽微な変更のみ（設定変更・ドキュメント修正など）の場合は自己レビューで代替できます。
- review で問題が見つかった場合は、該当 slice の修正（ステップ 5）または REPLAN（ステップ 1）に戻します。

### ステップ 8 — PR 作成（github-pr-workflow）

`gh-pr-workflow` を使い、feature branch → PR → レビュー待機 → 人間へのマージ引き継ぎを進めます。

### ステップ 9 — PR review 対応（gh-pr-review-response）

PR にレビューコメントが届いたら `gh-pr-review-response` を使い、分類・修正・返信・再レビュー依頼まで標準フローで進めます。

### ステップ 10 — furikaeri（gh-pr-review-response 完了後）

PR review が一段落したら `furikaeri-practice` で学びを整理します。PR review で得た気づきも含めて振り返ることで、最も充実した記録になります。

## 共通リソース

- `plugins/happy-ai-life/skills/implementation-eval-gate/SKILL.md` — 実装 slice の批判的 gate
- `plugins/happy-ai-life/skills/deep-review-preflight/SKILL.md` — PR 前の DeepReview
- `plugins/happy-ai-life/skills/gh-pr-workflow/SKILL.md` — PR 作成・管理
- `plugins/happy-ai-life/skills/gh-pr-review-response/SKILL.md` — PR レビュー対応
- `plugins/happy-ai-life/skills/furikaeri-practice/SKILL.md` — ふりかえり記録
- `references/interactive-app-bootstrap-checklist.md` — interactive app の bootstrap 前提
- `references/interactive-app-comparable-harness-contract.md` — interactive app の比較前提
- `checkpoints/contract_verify.py` — 複数リポ環境での contract 検証（fleet orchestrated）

## 注意点

- **bootstrap を飛ばさない**: 未配布の instructions や未確認の bootstrap 状態で実装を始めると、後で大きな修正が発生します。
- **fleet 判定は bootstrap + contract 後**: 未確定の slice や未 bootstrap repo に fleet をかけると失敗しやすいです。
- **slice loop と ship flow を混ぜない**: eval gate の `PASS` は「次の slice へ」です。全 slice 完了後に初めて review → PR フローへ進みます。
- **furikaeri は PR review 後**: PR review で得る学びが反映されるよう、原則として `gh-pr-review-response` の後に行います。
- **eval は別タスクで行う**: generator の自己正当化を避けるため、実装と評価を同じ流れに閉じ込めません。
