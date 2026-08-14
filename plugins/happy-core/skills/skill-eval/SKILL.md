---
name: skill-eval
description: >
  こんなときに使う: skill / プロンプト資産の評価方法を選びたいとき。privateEval
  として評価ケースを設計・保管・昇格判断したいとき、skill の behavioral A/B
  比較（baseline / legacy / current）をしたいとき、またはプロンプト指示の明瞭性を
  実証的に検証したいとき。
---

# Skill Eval

「何を評価ケースとして残すか」「この skill は本当に挙動を改善するか」「この指示は別の実行者にも明瞭に届くか」という評価問題を、1 本の入口から適切なルートへ案内します。入口を 1 つにする理由は、評価ケース設計、比較実行、明瞭性検査が近い言葉で語られやすく、境界を明示しないと artifact が混ざるためです。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。

作成・改善・責務整理そのものは `copilot-authoring` から始めます。本 skill は **評価方法を選ぶ窓口**です。明瞭性だけを実動で測りたいことが最初から明らかな場合は、`empirical-prompt-tuning` に直行して構いません。

## こんなときに使う

- skill を改訂し、旧版と比較して behavioral な改善を確認したいとき
- secret なしの評価ケースを privateEval として設計し、repo に昇格するか判断したいとき
- baseline / legacy / current の 3 比較で改善の evidence を作りたいとき
- プロンプトや skill の指示が「別のエージェントに読ませたら曖昧だったのでは」と疑うとき
- 評価ケースを設計し、benchmark summary や history ledger を生成したいとき
- どの評価手法を選ぶか迷うとき

## 判断表

| 問いの種類 | 選ぶルート | 特徴 |
|---|---|---|
| 「何を評価ケースとして残すか？」 | `references/private-eval.md` | secret なし評価ケースの設計・保管・昇格判断を扱う。評価実行そのものではない。 |
| 「新版は旧版より良くなったか？」 | `sub_skills/benchmark/` | privateEval などで設計した `evals.json` を使い、baseline / legacy / current を比較する。 |
| 「この指示は曖昧さなく伝わるか？」 | `empirical-prompt-tuning` | 独立 skill として新規 subagent に実行させ、反復して収束判定する。 |
| 「作成や責務整理から始めたい」 | `copilot-authoring` | authoring の入口へ戻し、構造確認後に必要なら評価へ進む。 |
| どちらか迷う | privateEval でケース設計 → 必要なら empirical → benchmark | 設計、明瞭性、版比較を混在させない。 |

## 共通リソース

- `references/private-eval.md` — privateEval の設計・保管・昇格判断
- `_eval/agents/` — runner / grader / comparator / analyzer の 4 agent
- `_eval/schemas/` — eval artifact のスキーマ定義
- `_eval/scripts/` — aggregate_benchmark.py / generate_viewer.py / materialize_manual_run.py / extract_prompt_corpus.py
- `assets/eval_review.html` — viewer テンプレート

## 注意点

- **privateEval と実行を混在させない**: privateEval は評価ケースの設計・保管・昇格判断です。実行は benchmark や empirical に分けます。
- **benchmark と empirical を混在させない**: 2 つは測る問いが異なります。benchmark は版差、empirical は明瞭性。同じ iteration で両方を走らせると artifact が混在しやすくなります。
- **eval 資産の昇格先**: raw run / viewer は session workspace が既定。`evals.json` と `benchmark_summary / history` は再利用価値が確認できてから repo の `evals/<skill-id>/` へ昇格します。
- **`empirical-prompt-tuning` との役割分担**: `empirical-prompt-tuning` は独立 skill です。`skill-eval` は明瞭性検査が必要だと判断したときの呼び出し元に留まります。
