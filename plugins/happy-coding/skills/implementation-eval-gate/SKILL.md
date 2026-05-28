---
name: implementation-eval-gate
description: >
  1つの実装 slice を、RED/GREEN/acceptance evidence と実装契約に照らして評価し、PASS / FAIL / REPLAN_REQUIRED を返す。
  Use when: implement の slice 完了後に、次の slice へ進むか、同じ slice を直すか、grill-with-docs / design-and-plan に戻すかを決めたいとき。
---

# Implementation Eval Gate

実装済みの 1 slice を、実装者とは別の視点で gate します。
目的は広い code review ではなく、次の行動を evidence ベースで決めることです。

## 判定

| 状況 | verdict | 次にやること |
| --- | --- | --- |
| slice contract を満たし、RED/GREEN/acceptance evidence がある | `PASS` | 次の slice へ進む |
| contract は明確だが、実装未達または証拠不足がある | `FAIL` | 同じ slice の実装へ戻る |
| contract / design / 前提が曖昧、または実装で前提崩れが見つかった | `REPLAN_REQUIRED` | `grill-with-docs` / `design-and-plan` へ戻る |

## ステップ 1 — 評価対象を 1 slice に絞る

読むもの:

- implementation handoff
- slice contract
- done 条件と非対象
- public interface / test surface
- RED command と失敗理由
- GREEN command
- acceptance command
- 差分

対象の振る舞いや非対象が曖昧なら、コードの良し悪しを推測で埋めず `REPLAN_REQUIRED` に倒します。

## ステップ 2 — evidence を確認する

最低限見るもの:

- RED を実際に見たか
- RED の失敗理由は対象振る舞いと一致したか
- GREEN を実際に見たか
- acceptance command は通ったか
- test は public interface 経由の振る舞いを確認しているか
- docs-only / config-only slice なら、RED の代わりになる verification command が明示されているか

interactive app の slice は、build/test の成功だけで `PASS` にしません。runtime launch command を起点に、初期描画、主要操作、状態変化、必要なら screenshot/trace まで確認します。

## ステップ 3 — 差分を contract に照らす

`references/checklist.md` から関係する観点だけを使います。

見る観点:

- 要求適合
- 振る舞いの正しさ
- 回帰リスク
- テストの妥当性
- speculative code / 不要な抽象化
- trust boundary 変更時の安全性

好みや一般論で減点しません。高信頼の evidence がある論点だけを残します。

## ステップ 4 — verdict と next action を返す

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

## 注意点

- 実装と評価を混ぜない。直し始める前に verdict を固定する。
- `PASS` は evidence があるときだけ返す。
- 証拠不足は `PASS` にしない。計画が明確なら `FAIL`、計画も曖昧なら `REPLAN_REQUIRED`。
- この skill は PR 前 review ではない。1 slice の gate に集中する。

## 同梱リソース

- `references/checklist.md` — slice gate 用 checklist
- `scripts/playwright-eval-template.md` — web app の runtime evidence テンプレ
- `scripts/flaui-eval-template.md` — desktop app の runtime evidence テンプレ
- `scripts/python-gui-eval-template.md` — Python GUI / pygame の runtime evidence テンプレ
