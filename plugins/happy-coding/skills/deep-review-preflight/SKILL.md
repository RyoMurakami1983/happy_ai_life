---
name: deep-review-preflight
description: >
  PR 前の DeepReview を標準フローで進める。一次情報確認、source of truth の確認、
  非破壊性・回帰・配布経路の点検、別タスク review、修正後の再レビューまでを整理する。
  Use when: 「DeepReview」「事前レビュー」「PR前レビュー」「commit前にチェック」の依頼時。
license: Personal
compatibility: "built-in /review or code-review agent"
---

# Deep Review Preflight

PR 前に「まだ reviewer が掘りそうな論点」を先回りで洗うためのスキルです。
単発の diff チェックではなく、**一次情報 -> 深掘り review -> 修正 -> 再 review** の流れを型にします。

## こんなときに使う

- PR を作る前に、別タスクで deep review を回す
- hook / sync / template / instructions のような運用資産を変更する
- 「直したつもりだが、他の観点が刺さりそう」な変更を見直す
- 値オブジェクト風クラス、guard clause、invariant、防御的な例外メッセージの妥当性を reviewer に掘られそうなとき
- reviewer との往復回数を減らす
- 実装タスクと review タスクを分離してコンテキスト汚染を減らす

## 判断表

| 状況 | 次にやること | 使うもの |
|---|---|---|
| ローカル差分の事前レビュー（品質） | Step 1 から開始 | built-in `/review` または `code-review` agent |
| ローカル差分の事前レビュー（セキュリティ） | Step 1 から開始 | built-in `/review` + セキュリティ観点の明示 |
| 認証・権限・migration 等の両面変更 | Step 1 から開始 | built-in `/review` または `code-review` agent |
| 値オブジェクト風クラスの guard / invariant / 例外文言が中心の変更 | Step 2 で guard 観点を追加 | built-in `/review` または `code-review` agent |
| custom agent が未導入 | Step 1 から開始 | built-in `/review` または `code-review` agent |
| すでに PR コメントが来ている | この skill ではなくレビュー応答へ進む | `gh-pr-respond` |
| 軽微な文言修正だけ | 必要最低限の確認に留める | 手動確認 or 軽量 review |

## ワークフロー: PR 前に深くレビューする

### Step 1: 変更対象と一次情報を固定する

差分だけを見て始めず、まず「何を変えたか」と「何を根拠にすべきか」を固定します。

- `git diff --staged` / `git diff` / 必要なら直近コミットを確認する
- 関連 Issue、repository instructions、公式 docs、同期スクリプト、既存 workflow を読む
- 変更が設定配布に関わるなら、**どこが正本か** を先に書き出す

Why: reviewer はコードだけでなく、仕様の穴と責務のズレを掘ってくるからです。

### Step 2: DeepReview 観点を棚卸しする

`references/checklist.md` を使い、今回の変更に当てはまる観点だけを残します。

最低でも次を確認します。

- 一次情報の確認漏れがないか
- source of truth / mirror / generated / template の切り分けができているか
- 非破壊性、legacy migration、DryRun、warning、exit code の説明と実装が一致しているか
- docs / comment / commit message draft と実装が矛盾していないか
- 新しい分岐や配布経路に対する回帰確認手段があるか

guard / invariant 系の変更では、追加で次を確認します。

- guard が domain invariant を守る最小境界に置かれているか
- 同じ前提条件チェックが複数箇所へ重複していないか
- 例外文言が「何が不足か」「次に何を設定・修正すべきか」を開発者に伝えるか
- value object へ寄せるべき責務と、呼び出し側の orchestration 責務が混ざっていないか
- guard 追加で正常系の利用者体験や既存 migration path を不必要に壊していないか

### Step 3: review を別タスクで実行する

review は実装スレッドと分けます。実装中の思考をそのまま正当化しないためです。

優先順:

1. built-in `/review` または `code-review` agent を使う
2. 認証・入力検証・機密データが中心の変更では、trust boundary と攻撃面を見るよう review 観点を明示する

review 依頼時の要件:

- 変更 diff だけでなく、関連ファイル全体を読むよう指示する
- この repo では配布経路と source of truth も見るよう伝える
- **高信頼の指摘だけ** を返すよう指定する
- guard / invariant が主題なら、例外メッセージの actionable 性と責務境界も見るよう伝える

### Step 4: 指摘を triage して修正する

出た指摘は severity ごとに分けます。

- `CRITICAL` / `HIGH`: PR 前に解消する
- `MEDIUM`: 今回解消するか、理由付きで保留する
- `LOW`: ノイズなら捨てる。意味があるなら follow-up に分ける

同時に、今回の修正で reviewer が次に掘りそうな 2〜3 手先も確認します。

### Step 5: 回帰確認と再レビューを行う

修正後は、変更に対応する既存コマンドで再確認します。

- skill を触ったら `validate_skill.py`
- script を触ったら関連テストや DryRun
- workflow / instructions を触ったら配布先と責務整合を確認

その後、**同じ観点で短い再 review** を 1 回だけ回します。

Why: 初回 review の修正で別の穴を作るのを防ぐためです。

### Step 6: PR ワークフローへ受け渡す

DeepReview を通過したら、結果を短く残して `gh-pr-create` へ進みます。

最低限残す内容:

- どの review 手段を使ったか
- blocker が何件あり、どう解消したか
- どのコマンドで回帰確認したか

## 注意点

- **review と実装を混ぜない**: 同一スレッドで self-justification すると観点漏れが増えます。
- **重い review を既定化しすぎない**: 変更規模に応じて built-in review と自己レビューを使い分けます。
- **guard 専用 skill をすぐ増やさない**: workflow が独立していない段階では、DeepReview の観点追加で十分なことが多いです。
- **既存 reviewer の仕事を想像する**: 「今の修正が正しいか」だけでなく、「次にどこを疑われるか」まで見るのが DeepReview です。

## 関連スキル

- **`gh-pr-create`** — DeepReview 後の PR 作成とレビュー待機
- **`gh-pr-respond`** — 実際の PR コメント対応
- **`safe-refactor`** — 振る舞いを変えずに差分を小さくしたいとき

## 同梱リソース

```text
deep-review-preflight/
├── SKILL.md
└── references/
    └── checklist.md
```
