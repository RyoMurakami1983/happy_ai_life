---
name: implement
description: >
  実装契約を受け取り、bootstrap 確認・実装（TDD）・eval・always の完了処理を進め、
  必要なときだけ review・PR・furikaeri へ続ける入口。multirepository 環境では parallel または sequential で実行。
  Use when: 実装契約が揃っていて実装を始めたいとき、ローカル完了と handoff まで閉じたいとき、
  fleet で並列実装するか判断したいとき、必要なら PR まで進めたいとき。
---

# implement — 実装して閉じる

実装契約を受け取り、bootstrap 確認から実装・eval gate・完了処理までを 1 つの入口でつなぐ skill です。PR、review、furikaeri は必要なときだけ後段へ伸ばします。「fleet タイムアウト後の迷い（実装に入るべきか不明）」と「実装完了後の閉じ方が曖昧」を解消するために存在します。

## こんなときに使う

このスキルは次のようなときに使います:
- grill-with-docs や design-and-plan で実装契約が固まり、実装フェーズに入りたいとき
- 実装契約はあるが、bootstrap が済んでいるか自信がないとき
- fleet で並列実装するか自分で進めるか迷ったとき
- 実装が終わり、ローカル完了と handoff まで自然に閉じたいとき
- 実装後に必要な review・PR・furikaeri だけを追加で進めたいとき
- 中断した実装を途中から再開したいとき
- Issue や実装契約を、vertical slice / tracer bullet に分割して進めたいとき

## ワークフロー: implementation contract から completion まで通す

### ステップ 1 — 実装契約の確認

implementation handoff、todos、または会話で合意した実装契約を受け取り、実装を開始できる状態かを確認します。以下が揃っているかをチェックします:
- todo リストと受け入れ条件
- 技術的な前提条件とテスト方針の下地
- 戻り先の条件（FAIL → 実装修正、REPLAN_REQUIRED → grill-with-docs / design-and-plan）

不足があれば `grill-with-docs` または `design-and-plan` に戻ります。

### ステップ 2 — bootstrap 確認

実装対象 repo に入る前に、以下を確認します:
- `repo-secure-check` で local safety valve（repo instructions / Copilot hooks / `.githooks` / `core.hooksPath`）と `.github/workflows/*.yml|*.yaml` を確認する
- `.github/instructions/` が配布済みか確認する。未配布なら `scripts/sync-to-repo.ps1 -TargetRepoPath PATH` で配布するか、理由を implementation handoff に残す
- `.github/workflows/` が不足している場合は、repo の技術スタックに合う workflow template を明示的に選んで導入する。CI workflow は repo ごとの差が大きいため、対象 runtime と意図を確認せずに汎用追加しない
- `git init` 済みか、fixed build/test/launch command があるかを確認する
- interactive app なら `implement/references/interactive-app-bootstrap-checklist.md` の最低条件を満たすか確認する

Branch Protection / Ruleset はローカルでは未確認として別 warning にします。

### ステップ 3 — contract checkpoint を固定する

今回の slice で何を done とみなすかを固定します。contract（リポ間の provide/require、モジュール間の統合）を含め、最低でも次を残します:
- 今回の対象振る舞い
- 非対象
- public interface 経由で確認する主要な test 観点
- test artifact path / test command / runtime launch command
- multirepository なら、当該リポの他リポへの依存と提供を明示
- `FAIL` なら実装修正、`REPLAN_REQUIRED` なら grill-with-docs / design-and-plan へ戻る条件

1 受け入れ条件または 1 ユーザー行動を 1 vertical slice として切ります。最初の slice は tracer bullet として、UI / API / domain / persistence / test など必要な層を薄く縦断し、実装経路が通ることを確認します。層ごとに「DB だけ」「UI だけ」「テストだけ」を横に広げる horizontal slice は避けます。

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
    Remediation: Wait for upstream implement to complete
```

**Checksum mismatch**:
```
Contract verification failed:
  - Checksum mismatch: openapi
    Path: docs/openapi.yaml
    Expected: abc123...
    Actual:   xyz789...
    Action: Upstream artifact changed since design handoff
    Remediation: Contact upstream team or re-run design-and-plan
```

#### 実装実体

- `checkpoints/contract_verify.py`: `verify_contracts(plan_dict, repo_root) -> CheckpointResult`
- 入力: plan.md YAML front-matter (`dependencies.contracts.requires`)
- 出力: `CheckpointResult(status="PASS"|"FAIL", reason="...")`
- テスト: `tests/test_contract_verify_checkpoint.py`

### ステップ 5 — 実装（TDD の内側ループ）

**このステップは全 slice が完了するまでループします。**

オーケストレーター主導で Red-Green-Refactor サイクルを回しながら実装を進めます。必要なら `tdd-coder` を narrow generator として使います。

- ビルドエラーや前提逸脱が発生したら `grill-with-docs` / `design-and-plan` に戻る
- TDD は 1 test → 1 minimal implementation の vertical slice で進め、all tests first の horizontal slicing を避ける
- slice は user-visible behavior または外から観測できる contract を主語にし、内部都合だけで切らない
- 人間判断が必要な HITL slice と、エージェントに任せやすい AFK slice を分ける
- test は public interface 経由の振る舞いを主語にし、private method や内部 collaborator の呼び出し回数を固定しない
- mock は外部 API、時刻、乱数、ファイル I/O など system boundary に限り、自分たちが制御する内部 module は原則 mock しない
- リファクタリングは振る舞い不変を前提に小さく進める
- **セキュリティ中間チェック（イベント駆動）**: 以下の変更が発生したら都度チェックする
  - 認証 / 認可を追加・変更した
  - 外部入力の入口を増やした
  - 機密データの保存 / 転送を追加した
  - 外部 API / Webhook / ファイル I/O / コマンド実行を追加した
  - trust boundary をまたぐデータフローを増やした
  - → 前提が崩れているなら `design-and-plan` へ戻す

### ステップ 6 — implementation eval gate（slice ごと）

各 slice の実装後に `implementation-eval-gate` を実行し、verdict を固定します:
- `PASS`: 次の slice へ戻る（ステップ 3 から繰り返す）
- `FAIL`: 同じ plan のまま実装に戻す（ステップ 5 へ）
- `REPLAN_REQUIRED`: `grill-with-docs` または `design-and-plan` に戻す

**全 slice が PASS したら外側フロー（ステップ 7 以降）へ進みます。**

### ステップ 7 — 完了処理と handoff（always）

全 slice 完了後、まず今回の実装フェーズを done とみなすための後始末を行います。

- 実装で確定した成果物、残件、戻り先を短く固定する
- `docs/plan/NNN_PLAN.md` がある場合は `docs/plan/NNN_PLAN_DONE.md` へリネームする
- 未完了項目が残るなら、次の `NNN+1_PLAN.md` または handoff に切り出す

ここまでが always の完了処理です。PR、review、ふりかえりが今回不要なら、この時点で handoff して終了してよいです。

### ステップ 8 — optional tail を選ぶ

ここから先は、今回の依頼や運用に必要な tail だけを選びます。

- PR 前の品質確認が必要 → ステップ 9
- PR を作成したい → ステップ 10
- PR レビュー対応が必要 → ステップ 11
- ふりかえりを残したい → ステップ 12

### ステップ 9 — pre-PR review（optional）

必要な場合だけ `deep-review-preflight` を実行して品質とセキュリティを確認します。
- 軽微な変更のみ（設定変更・ドキュメント修正など）の場合は自己レビューで代替できます。
- review で問題が見つかった場合は、該当 slice の修正（ステップ 5）または REPLAN（ステップ 1）に戻します。

### ステップ 10 — PR 作成（optional）

必要な場合だけ `gh-pr-create` を使い、feature branch → PR → レビュー待機 → 人間へのマージ引き継ぎを進めます。

### ステップ 11 — PR review 対応（optional）

必要な場合だけ `gh-pr-respond` を使い、レビューコメントの分類・修正・返信・再レビュー依頼まで進めます。

### ステップ 12 — furikaeri（optional）

必要な場合だけ `furikaeri` で学びを整理します。PR review 後に行うと学びが最も充実しますが、今回不要なら省略して構いません。

## 共通リソース

- `plugins/happy-coding/skills/implementation-eval-gate/SKILL.md` — 実装 slice の批判的 gate
- `plugins/happy-coding/skills/deep-review-preflight/SKILL.md` — PR 前の DeepReview
- `plugins/happy-core/skills/gh-pr-create/SKILL.md` — PR 作成・管理
- `plugins/happy-core/skills/gh-pr-respond/SKILL.md` — PR レビュー対応
- `plugins/happy-core/skills/furikaeri/SKILL.md` — ふりかえり記録
- `references/interactive-app-bootstrap-checklist.md` — interactive app の bootstrap 前提
- `references/interactive-app-comparable-harness-contract.md` — interactive app の比較前提
- `checkpoints/contract_verify.py` — 複数リポ環境での contract 検証（fleet orchestrated）

## 注意点

- **bootstrap を飛ばさない**: 未配布の instructions や未確認の bootstrap 状態で実装を始めると、後で大きな修正が発生します。
- **fleet 判定は bootstrap + contract 後**: 未確定の slice や未 bootstrap repo に fleet をかけると失敗しやすいです。
- **slice loop と完了処理を混ぜない**: eval gate の `PASS` は「次の slice へ」です。全 slice 完了後に初めてステップ 7 の完了処理へ進みます。
- **optional tail を必須扱いしない**: PR、review、furikaeri は毎回必須ではありません。今回の依頼に必要な tail だけを選びます。
- **furikaeri は任意だが、やるなら review 後が濃い**: PR review で得る学びが反映されるよう、行う場合は原則として `gh-pr-respond` の後が向いています。
- **eval は別タスクで行う**: generator の自己正当化を避けるため、実装と評価を同じ流れに閉じ込めません。
