---
name: benchmark
description: >
  baseline / legacy / current を比較し、skill の行動変化を測定する。trigger 精度、出力品質、回帰リスクを実証的に確認したいとき。
---

# スキルをベンチマーク比較する

静的レビューだけでは足りないときに、skill が本当に挙動改善を生むかを比較評価する sub-skill です。比較で見る理由は、単発の好例ではなく、baseline / legacy / current の差分として改善を確かめるためです。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

- should-trigger / near-miss ケースを実運用に近い形で設計したいとき
- 同じ prompt で baseline / legacy / current を比較したいとき
- benchmark summary や history ledger を生成したいとき
- 採用、改訂、ケース追加の次アクションを決めたいとき

## ワークフロー: スキルをベンチマーク比較する

### ステップ 1 — 良い eval ケースを設計する

should-trigger と should-not-trigger を、実際の user request に近い形で作ります。near-miss case は false positive を見つけやすいので、明らかに無関係な prompt より重要です。

### ステップ 2 — 3 variant を同条件で実行する

`_eval/agents/runner.md` を使い、各ケースを baseline / legacy / current で実行します。条件が揃っていない比較は信用できません。

### ステップ 3 — 結果を集計する

```
uv run python plugins/happy-core/skills/skill-eval/_eval/scripts/aggregate_benchmark.py \
  --skill-id <skill-id> --run-id <run-id>
```

baseline / legacy / current の比較と summary delta を集計します。単発ケースでは見えない傾向を、集計で可視化します。

### ステップ 4 — review artifact を作る

```
uv run python plugins/happy-core/skills/skill-eval/_eval/scripts/generate_viewer.py \
  --skill-id <skill-id>
```

`assets/eval_review.html` を使い、人がすばやく結果と履歴を見られる形にします。iteration を回すには、review の速さが重要です。

### ステップ 4.5 — 昇格する artifact を判断する

eval artifact は**セッションワークスペースを既定**とします。

- `evals.json` が複数 iteration で再利用できそうなら、repo の `evals/<skill-id>/evals.json` へ昇格候補
- `benchmark_summary.json` と `benchmark_history.jsonl` が共有価値の高い結果なら、repo の `evals/<skill-id>/` へ昇格候補
- `viewer.html` と raw run artifact は session 側に残す

迷ったら session に残します。昇格は後からできますが、repo に入った transient artifact を整理するほうが高コストです。

### ステップ 5 — 次のアクションを決める

current が legacy より明確に良ければ accept、悪化していれば revise、evidence が薄ければケース追加、回帰が大きければ escalation を選びます。accept した current は、次回 campaign では legacy に昇格させます。

## 昇格ルール

- `baseline` は常に no-skill の固定基準です。
- `legacy` は直前に採用した版です。
- `current` は今回の候補です。
- `current` を accept したら、その snapshot を次回の `legacy` にします。
- 以前の `legacy` は履歴 ledger には残しつつ、active benchmark からは外します。

## 早見表

| 段階 | 見るもの |
|---|---|
| ケース設計 | should-trigger、near-miss、false-positive guard |
| 実行 | baseline / legacy / current の条件一致 |
| 集計 | pass rate、summary delta、傾向 |
| artifact | reviewer が追える形か、repo に昇格する価値があるか |
| 判断 | accept / revise / add cases / escalate |

## 共通リソース

- `../../_eval/agents/runner.md` — baseline / legacy / current 実行
- `../../_eval/scripts/aggregate_benchmark.py` — 集計
- `../../_eval/scripts/generate_viewer.py` — viewer 生成
- `../../_eval/schemas/schemas.md` — artifact スキーマ定義
- `../empirical/` — 指示明瞭性を先に確かめる軽量ルートへの導線

## 注意点

- **happy path だけで評価しない**: near-miss がないと trigger precision を判断できません。
- **variant 間で prompt を変えない**: 条件がずれた時点で比較の意味が壊れます。
- **1 回の好結果を証拠にしない**: anecdotal win より、繰り返し観測される evidence を重視します。
