---
name: implementation-eval-gate
description: >
  批判的な実装評価を行い、PASS / FAIL / REPLAN_REQUIRED を返す。Use when:
  plan artifact に基づく slice 実装の後で、独立した gate として次の行動を決めたいとき。
---

# Implementation Eval Gate

実装中の 1 slice を、generator とは別の視点で批判的に評価する workflow skill です。`tdd-coder` のような narrow generator が小さく前進したあとに、「次の slice へ進めるか」「直して戻すか」「計画や設計へ戻るか」を evidence ベースで判定しやすくします。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


`deep-review-preflight` が PR 前の広い review を扱うのに対し、この skill は **実装中 gate** を扱います。目的は称賛ではなく、甘い自己評価を避けて次の行動を明確にすることです。

## こんなときに使う

このスキルは次のようなときに使います:
- `tdd-coder` や通常実装で 1 slice 進めたあと、次に進んでよいかを独立評価したいとき
- 差分、テスト結果、handoff を読み、fix と replan のどちらへ戻すべきか決めたいとき
- `/sdd` の実装フェーズで、自己正当化を避ける批判的 gate を挟みたいとき

## 判断表

| 状況 | 次にやること | verdict |
| --- | --- | --- |
| contract が明確で、証拠上も要件を満たす | 次の slice へ進める | `PASS` |
| contract は明確だが、実装未達や証拠不足がある | generator に差し戻す | `FAIL` |
| contract / plan / design が曖昧、または前提が崩れた | PLAN mode / design-workshop に戻す | `REPLAN_REQUIRED` |

## ワークフロー: 実装 slice を gate する

### ステップ 1 — 評価境界と入力 artifact を固定する

まず今回の評価対象を 1 slice に絞ります。最低限、次を読みます。

- plan artifact または planning handoff
- 今回の slice contract（done の定義、非対象、主要なテスト観点）
- generator handoff（例: `tdd-coder` の TDD Progress）
- generator handoff 内の test artifact path / test command / runtime launch command
- 差分と test / build / lint の証拠

対象の振る舞いや非対象が曖昧なら、コードの良し悪しを推測で埋めず `REPLAN_REQUIRED` に倒します。ここで評価境界を曖昧にすると、review が scope 拡大や style 議論へ流れやすくなり、実装修正で済む問題と再計画が必要な問題の切り分けも崩れるからです。

### ステップ 2 — 適用する rubric を選ぶ

`references/checklist.md` を使い、今回の slice に関係する観点だけを残します。最低でも以下を見ます。

- 要求適合
- 振る舞いの正しさ
- 回帰リスク
- テストの妥当性
- trust boundary 変更時の安全性

重要なのは、好みや一般論で減点しないことです。高信頼の evidence がある論点だけを残し、generator に返して次の行動へつながる指摘に絞ります。

### ステップ 2.5 — interactive runtime evidence の要件を固定する

interactive app の slice は、unit test や build が通ってもそれだけで `PASS` にしません。最低限、generator handoff の runtime launch command を起点に live behavior を確認し、どの操作を証拠として扱うかを固定します。比較用 pilot の場合は、`/sdd` 側で fixed seed / state dump schema / command runner などの comparable harness contract が先に決まっているかも確認します。

| Stack | 最低限ほしい runtime evidence | `PASS` に必要な状態 |
| --- | --- | --- |
| Web / Playwright | app 起動、初期描画、主要操作、失敗時 screenshot/trace | contract 上の UI 振る舞いが live で確認できる |
| Python GUI / pygame | app 起動、main loop、入力イベント、state 変化 | loop 上の操作結果と expected state が対応している |
| WPF / desktop | app 起動、window 捕捉、主要 control / status / restart | desktop UI の主要操作と状態遷移が live で確認できる |

interactive slice で runtime evidence がない場合は、設計や計画が概ね妥当でも `FAIL` に倒します。何を確認すべきか自体が曖昧なら `REPLAN_REQUIRED` に倒します。

### ステップ 3 — generator と別タスクで評価する

評価は、実装したスレッドと分けて行います。同じ思考の流れで self-review すると「この差分で足りるはず」という前提を引きずりやすいからです。

この skill を使うときの原則:

1. 実装を直し始める前に verdict を固定する
2. `PASS` は evidence があるときだけ返す
3. 実装意図は明確だが要件未達なら `FAIL`
4. contract / plan / design の不足で判断不能なら `REPLAN_REQUIRED`

### ステップ 4 — verdict と次アクションを handoff する

出力は、generator や `/sdd` が次の一歩を迷わない形で返します。

```markdown
## Implementation Eval
- Verdict: PASS | FAIL | REPLAN_REQUIRED
- Slice:
- Scope checked:
- Evidence:
- Failed criteria:
- Required fixes:
- Return path:
- Next action:
```

判定の使い分け:

- `PASS`: 現在の slice contract を満たし、次の slice に進める
- `FAIL`: 現在の計画のまま実装修正すれば前進できる
- `REPLAN_REQUIRED`: plan / design / contract を補わないと安全に進めない

## 注意点

- **実装と評価を混ぜない**: この skill の役割は gate であり、修正そのものではありません。直し始める前に verdict を返します。
- **称賛で埋めない**: 良かった点を長く書くより、次の行動に必要な blocker と evidence を先に返します。
- **PR 前 review と混同しない**: repo 全体の広い事前 review は `deep-review-preflight` へ渡し、この skill は実装中の slice gate に集中します。
- **推測で PASS を出さない**: contract や test evidence が弱ければ `FAIL` または `REPLAN_REQUIRED` に倒したほうが、後工程の手戻りを減らせます。
- **interactive app は live evidence を要求する**: build/test の成功だけで UI slice を `PASS` にしません。runtime launch command を起点にした live evidence を要求します。

## 関連スキル

- `sdd`
- `deep-review-preflight`
- `design-workshop`

## 同梱テンプレ

- `scripts/playwright-eval-template.md` — web app を触る evaluator の基本形
- `scripts/flaui-eval-template.md` — WPF など desktop app を触る evaluator の基本形
- `scripts/python-gui-eval-template.md` — Python GUI / pygame 系を触る evaluator の基本形

## 同梱リソース

```text
implementation-eval-gate/
├── SKILL.md
├── scripts/
│   ├── playwright-eval-template.md
│   ├── flaui-eval-template.md
│   └── python-gui-eval-template.md
└── references/
    └── checklist.md
```
