# privateEval の設計・保管・昇格判断

privateEval は、secret を含まない評価ケースを設計し、repo に残す価値があるものだけを `evals/<skill-id>/` へ昇格するための評価資産レイヤーです。評価の実行そのものではなく、何を測るか、何を保存してよいか、いつ昇格するかを扱います。

## 境界

| 入口 | 責務 | privateEval との関係 |
| --- | --- | --- |
| `privateEval` | 評価ケースの設計・保管・昇格判断 | この reference が扱う |
| `skill-eval` | 評価方法の選択と実行導線 | privateEval で設計したケースを benchmark などで使う |
| `empirical-prompt-tuning` | 別実行者で指示明瞭性を反復改善 | privateEval へ昇格するケース候補を見つけることがある |
| `loop-engineering` | Verify -> Evaluate -> Reflect -> Patch の改善ループ | privateEval の資産を使う consumer。評価資産の owner ではない |

## 最小ケース

| ケース | 目的 |
| --- | --- |
| happy path | 正しく発火し、期待する handoff まで進めるか |
| near-miss | 似ているが別 skill が適切な依頼を誤発火しないか |
| failure / missing-context | 足りない前提を握りつぶさず、質問や戻り先を示せるか |

## repo に昇格してよいもの

- secret を含まない `evals.json`
- 匿名化済みの期待結果
- 集計済み `benchmark_summary.json`
- append-only の `benchmark_history.jsonl`

## repo に入れないもの

- 実会話ログ
- API key、token、cookie、認証情報
- 個人情報
- private repo のコード片
- 顧客・職場・未公開情報を推測できる内容
- `runs/`、`viewer.html`、raw transcript、tool output dump

## 昇格判断

1. 同じ失敗が複数回起きる、または再発コストが高い。
2. secret / PII / private code を含まず、匿名化しても意味が残る。
3. happy path / near-miss / failure のどれを測るかが明確である。
4. `skill-eval` の benchmark で再利用できる形にできる。

迷った場合は repo に昇格せず、session workspace や private storage に残します。
