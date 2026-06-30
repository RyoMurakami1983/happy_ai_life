# PrivateEval

PrivateEval は、Happy AI Life の skill / prompt / workflow を育てるための評価ケース群です。
目的は AI 評価で機械テストを置き換えることではなく、機械判定では測りにくい handoff、source of truth 参照、指示明瞭性、再利用性を継続的に見ることです。

## 置き場所

repo に昇格する評価ケースは、次の形を正本にします。

```text
evals/<skill-id>/evals.json
evals/<skill-id>/benchmark_summary.json
evals/<skill-id>/benchmark_history.jsonl
```

raw run、viewer、実会話ログは repo に入れません。必要な場合は session workspace や private storage に置きます。

## repo に入れてよいもの

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

## 最小ケース

各 skill の最小セットは3ケースです。

| ケース | 目的 |
| --- | --- |
| happy path | 正しく発火し、期待する handoff まで進めるか |
| near-miss | 似ているが別 skill が適切な依頼を誤発火しないか |
| failure / missing-context | 足りない前提を握りつぶさず、質問や戻り先を示せるか |

## 最初に育てる skill

1. `copilot-authoring`
2. `skill-eval`
3. `grill-with-docs`
4. `design-and-plan`
5. `implementation-eval-gate`

## 評価カタログ

| Catalog | 測るもの |
| --- | --- |
| routing | どの skill が呼ばれるべきか |
| handoff | 次工程が迷わず続けられる成果物か |
| source of truth | README、docs、ADR、plugin manifest へ戻れているか |
| implementation | acceptance check まで到達できるか |
| safety | secret、hook bypass、破壊的操作を誘導しないか |
| docs-reader | 初見読者が目的・手順・判断基準を理解できるか |
| cost | tool 回数、再試行、往復が増えていないか |

## quality gate への接続

- PR 常時 gate にはしない。
- skill / prompt / workflow の挙動を変える PR では、該当 skill の focused eval を検討する。
- raw artifact は `.gitignore` の `evals/**/runs/`、`evals/**/viewer.html`、`evals/**/*transcript*`、`evals/**/*raw*` に従って追跡しない。
- secret / PII 混入は `gitleaks` と evals policy test の両方で防ぐ。
