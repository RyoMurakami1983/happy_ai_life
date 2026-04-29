---
name: skill-eval
description: >
  skill / プロンプト資産の評価を 1 つの入口にまとめる。Use when:
  skill の behavioral A/B 比較（baseline / legacy / current）をしたいとき、または
  プロンプト指示の明瞭性を実証的に検証したいとき。
---

# Skill Eval

「この skill は本当に挙動を改善するか」「この指示は別の実行者にも明瞭に届くか」という 2 つの評価問題を、1 本の入口から適切なルートへ案内します。入口を 1 つにする理由は、どちらの評価も「変更前に測る」「iteration を回す」という共通の構造を持ち、用語が紛れやすいためです。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

- skill を改訂し、旧版と比較して behavioral な改善を確認したいとき
- baseline / legacy / current の 3 比較で改善の evidence を作りたいとき
- プロンプトや skill の指示が「別のエージェントに読ませたら曖昧だったのでは」と疑うとき
- 評価ケースを設計し、benchmark summary や history ledger を生成したいとき
- どの評価手法を選ぶか迷うとき

## 判断表

| 問いの種類 | 選ぶルート | 特徴 |
|---|---|---|
| 「新版は旧版より良くなったか？」 | `sub_skills/benchmark/` | evals.json を用意して baseline / legacy / current を比較。定量的 verdict を出す。 |
| 「この指示は曖昧さなく伝わるか？」 | `sub_skills/empirical/` | 新規 subagent に実行させて両面評価。反復して収束判定。 |
| どちらか迷う | まず empirical で明瞭性を確認 → 改善後に benchmark で版比較 | empirical は軽量で先に回しやすい。 |

## 共通リソース

- `_eval/agents/` — runner / grader / comparator / analyzer の 4 agent
- `_eval/schemas/` — eval artifact のスキーマ定義
- `_eval/scripts/` — aggregate_benchmark.py / generate_viewer.py / materialize_manual_run.py / extract_prompt_corpus.py
- `assets/eval_review.html` — viewer テンプレート

## 注意点

- **benchmark と empirical を混在させない**: 2 つは測る問いが異なります。benchmark は版差、empirical は明瞭性。同じ iteration で両方を走らせると artifact が混在しやすくなります。
- **eval 資産の昇格先**: raw run / viewer は session workspace が既定。`evals.json` と `benchmark_summary / history` は再利用価値が確認できてから repo の `evals/<skill-id>/` へ昇格します。
- **`empirical-prompt-tuning` との役割分担**: `sub_skills/empirical/` は skill 評価文脈の thin pointer です。任意プロンプトに単独で使いたい場合は `empirical-prompt-tuning` skill を直接呼びます。
