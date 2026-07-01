---
name: loop-engineering
description: >
  Observe -> Plan -> Act -> Verify -> Evaluate -> Reflect -> Patch -> Stop or Loop
  の型で、AI 開発や authoring の改善ループを回す。Use when: 単発対応ではなく、
  検証、PrivateEval、ふりかえり、最小修正をつなげて品質を上げたいとき。
---

# Loop Engineering

Loop Engineering は、AI に「作らせて終わり」にせず、観察、計画、実行、検証、評価、ふりかえり、修正、停止判断を明示して回すための型です。
目的はループ回数を増やすことではなく、**客観的な検証と PrivateEval で止めどきを決め、落ちた軸だけを最小差分で直す**ことです。

## こんなときに使う

- 実装、PR レビュー対応、skill / prompt authoring などを 1 回で終わらせず品質ゲートまで通したいとき
- test / lint / typecheck / build の結果と、AI による自己評価を混ぜずに扱いたいとき
- レビュー指摘や失敗ログから、改善する軸だけを選んで再実行したいとき
- 後続のテンプレート、README、ADR、PR 本文へ Why を残す判断をしたいとき

## 起動トリガー例

- 失敗ログ、review 指摘、既知の TODO を見ながら、原因切り分けから修正、検証、次の改善まで一気通貫で進めたい
- 1 回の修正で終わらず、「何が落ちたか」「どの軸だけ直すか」を分けて安定駆動させたい
- 実装だけでなく、follow-up Issue、ふりかえり、公開可能な知識化まで残して次に接続したい

## dispatch / handoff

Loop Engineering は万能入口ではなく、**改善ループの進行型**です。各段階で次の専門 skill へ委譲します。

- 要求や用語の曖昧さが残る: `grill-with-docs`
- 実装契約を切る必要がある: `design-and-plan`
- ローカル実装と focused verify に入る: `implement`
- 評価観点や prompt 実験を深める: `skill-eval`, `empirical-prompt-tuning`
- Happy AI Life 側への改善要望を残す: `happy-add-issue`
- 現 repo の後続 Issue を丁寧に具体化する / 公開向け匿名化まで見る: `gh-issue-create`
- 公開知識へ残す: `knowledge-capture`

## 使わない場面

- 単純な質問への回答だけで、Act や Verify がない
- `skill-eval` の benchmark / empirical 評価だけを実行したい
- 既に `implement`、`gh-pr-respond`、`copilot-authoring` などの専門 skill が明確に担当している作業を置き換えたい

## Core Loop

```text
Observe -> Plan -> Act -> Verify -> Evaluate -> Reflect -> Patch -> Stop or Loop
```

| 段階 | 目的 | 出力 |
|---|---|---|
| Observe | 要求、コード、テスト、ログ、差分を事実として読む | Fact / Inference / Unknown |
| Plan | 成功条件、非対象、検証方法、最小 slice を決める | 実行契約 |
| Act | 契約に沿って最小差分を入れる | 変更差分 |
| Verify | test / lint / typecheck / build など機械判定を通す | 検証結果 |
| Evaluate | PrivateEval 5軸で成果物を評価する | 落ちた軸 |
| Reflect | なぜ落ちたか、次回に残す知識があるかを見る | 改善仮説 |
| Patch | 落ちた軸だけを最小修正する | 追加差分 |
| Stop or Loop | 停止条件を満たすか、人間レビューに切り替えるか決める | Stop / Continue / Human Review |

## PrivateEval

Evaluate では次の 5 軸を使います。詳細な採点基準は `references/private-eval.md` を参照します。

| 評価軸 | 見ること |
|---|---|
| 構造化精度 | 問題、原因、変更範囲、検証方法を分けられているか |
| 形式知化力 | Why、判断理由、再現手順、次回に使える知識を残せているか |
| 完了条件設計力 | 「作業した」ではなく「完了した」と客観的に判断できるか |
| 組織視点 | 個人の速さだけでなく、チームの保守性、安全性、自走、レビューしやすさに効くか |
| 再利用性 | 一回限りで終わらず、次回も使える型や手順になるか |

## ワークフロー: ループを回す

### Step 1 — Observe: 事実と推測を分ける

まず、要求、関連 docs、コード、テスト、CI、レビューコメントを読みます。
この段階では直し始めず、次を分けます。

- **Fact**: 実際に読んだ code / docs / test / log / review comment
- **Inference**: fact から導いた判断
- **Unknown**: 次の Plan を止める未確認事項

Unknown が作業方針を変えるなら、先に `grill-with-docs` またはユーザー確認へ戻します。

### Step 2 — Plan: 最小の実行契約を作る

次を 1-2 段落に圧縮します。

- Goal: 何が成立したら終わりか
- Success criteria: 観測可能な完了条件
- Out of scope: やらないこと
- Verification: 実行する test / lint / typecheck / build / manual check
- Stop rule: どこまで通れば止めるか

実装契約が必要なら `design-and-plan`、ローカル実装に入るなら `implement` に渡します。

### Step 3 — Act: 最小差分で実行する

Plan に直接効く差分だけを入れます。

- 仕様変更とリファクタを混ぜない
- エラーを握りつぶさない
- 不要な依存関係を足さない
- 破壊的操作や secret 操作は自動実行しない

### Step 4 — Verify: 機械判定を先に通す

PrivateEval より先に、客観的に判定できる確認を優先します。

```text
test / lint / typecheck / build / security scan > rule check > PrivateEval
```

どの command を実行するかは repo の source of truth に従います。失敗した場合は AI 評価で合格扱いにせず、原因を見て同じ slice に戻ります。

### Step 5 — Evaluate: PrivateEval で落ちた軸を特定する

5 軸を 1〜5 点で採点し、落ちた軸だけを改善対象にします。
全軸を同時に直そうとすると差分が膨らむため、1 iteration では関連する 1 テーマに絞ります。

### Step 6 — Reflect: Why と再利用価値を見る

次を短く確認します。

- なぜその失敗が起きたか
- 次回も起きそうか
- README、ADR、PR、commit、skill、template のどこへ Why を残すべきか
- 残すと公開・共有して安全か

公開されうる知識へ変換する場合は `knowledge-capture` の匿名化観点を使います。

### Step 7 — Patch: 落ちた軸だけ直す

Patch は「評価で落ちた軸に対する最小修正」です。

- 完了条件設計力が低い: test / acceptance / stop rule を補う
- 形式知化力が低い: Why や判断理由を PR / README / commit に残す
- 構造化精度が低い: 事実、推測、判断、差分を分け直す
- 組織視点が低い: レビューしやすさ、安全性、保守境界を整える
- 再利用性が低い: checklist、template、skill、reference 化を検討する

### Step 8 — Stop or Loop: 停止条件を決める

停止条件:

- 必須の test / lint / typecheck / build / security check が通っている
- Critical 要件がすべて OK
- PrivateEval 総合点が 22/25 以上
- 構造化精度、形式知化力、完了条件設計力が各 4 点以上
- 2 回連続で新しい重大指摘が出ない
- 差分だけ増えて品質が上がらない場合は Human Review に切り替える

低リスクな小タスクでは、PrivateEval を表形式にせず、落ちた軸と停止理由だけを短く残してよいです。

## 判断表

| 状況 | 使う skill |
|---|---|
| 要求や用語の曖昧さを先に潰す | `grill-with-docs` |
| 実装契約と vertical slice を作る | `design-and-plan` |
| ローカル実装を TDD で進める | `implement` |
| Happy AI Life 側への改善要望を母艦 repo に返す | `happy-add-issue` |
| 現 repo の follow-up を公開向けに丁寧に具体化する | `gh-issue-create` |
| skill / agent / instructions を作る・直す | `copilot-authoring` |
| skill / prompt の評価方法を選ぶ | `skill-eval` |
| 別実行者に指示明瞭性を実証検査させる | `empirical-prompt-tuning` |
| PR レビューコメントへ対応する | `gh-pr-respond` |
| 知識を公開可能な形に捕捉する | `knowledge-capture` |

Loop Engineering はこれらを置き換える親プロセスではありません。ループの中で、必要な専門 skill へ委譲するための進行型です。

## 注意点

- エラーを握りつぶす
- test を削除して通す
- AI 評価だけで機械判定の失敗を無視する
- 原因を特定せず修正する
- 仕様変更とリファクタを混ぜる
- 大量の無関係な整形を含める
- Why を残さない
- 評価で落ちた軸と関係ない差分を増やす

## 関連スキル / 共通リソース

- `references/private-eval.md` — PrivateEval の採点基準
- `references/eval-scenarios.md` — ループが機能するかを確認する代表シナリオ
- `references/verify-commands.md` — 機械判定を先に通すための検証コマンド例
- `assets/templates/loop-report.md` — ループ結果を残すテンプレート
- `assets/templates/pr-body.md` — PR 本文へ Why と PrivateEval を残すテンプレート
- `assets/templates/commit-message.md` — commit message へ Why と Verify を残すテンプレート
- `assets/templates/adr.md` — 戻しにくい判断を ADR 化するテンプレート
- `happy-add-issue` — Happy AI Life 側への意見を母艦 repo に返す入口
- `gh-issue-create` — 現 repo の follow-up Issue を切って次のループへつなぐ
- `skill-eval` — skill / prompt 評価の入口
- `empirical-prompt-tuning` — 指示明瞭性の実証検査
- `knowledge-capture` — 公開されうる知識の匿名化と捕捉
