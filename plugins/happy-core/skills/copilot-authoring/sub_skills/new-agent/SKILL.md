---
name: new-agent
description: >
  新しい custom agent を既存 agent 群と同じ型で立ち上げる。agent の新規追加、役割分離のための専門 agent 作成、既存群の隙間を埋めたいとき。
---

# Agent を新規作成する

この sub-skill は、custom agent を「何を判断する存在か」という責務から設計するための入口です。skill よりも権限と境界の影響が大きいため、まず役割を 1 文で固定してから雛形へ落とし込みます。

## こんなときに使う

- 新しい custom agent を `plugins/happy-coding/agents/` に追加したいとき
- 既存 agent 群の責務境界では吸収しづらい専門領域が出てきたとき
- review / planning / refactor などの専門動作を独立させたいとき
- model や tool 権限を役割に合わせて最小化したいとき

## ワークフロー: agent を作る

### ステップ 1 — 役割境界を 1 文で定義する

「何を判断し、何を返し、何をやらないか」を先に定義します。これを曖昧にすると、既存 agent や skill と責務が重なりやすくなります。

### ステップ 2 — model と tools を決める

必要な推論量と権限に応じて model と tools を最小化します。理由は、過剰な権限や過大な model は便利でも、運用コストと誤用リスクを増やすからです。

### ステップ 3 — template から agent.md を起こす

既存雛形を基準に frontmatter と本文構成を埋めます。`description` の `trigger phrase`（『こんなときに使う』相当）、`役割`、`非責務`、`<領域名>の原則`、`プロセス`、`出力の型`、`注意点`、`完了条件` は `_agent` の正本契約として最低限そろえます。

### ステップ 4 — 近接 agent と比較する

`plugins/happy-coding/agents/` に近い agent がある場合は見比べ、責務境界、語彙、出力の型をそろえます。ここを比較する理由は、新規 agent 単体では気づきにくい overlap を早く見つけるためです。比較対象がない場合は、template と instructions との整合を優先します。

### ステップ 5 — validator で骨格を確認する

作成後は同梱の検証スクリプトで frontmatter と section 構造を確認します。`## 1. 役割` のような番号付き H2 や `## 設計プロセス` / `## レビュープロセス` のような既存 corpus にある見出し、師範 agent の legacy mode 構成も受け入れつつ、雛形由来の agent では `原則` セクションを必須として `_agent` と契約を揃えます。

```powershell
uv run python plugins/happy-core/skills/copilot-authoring/_eval/scripts/validate_agent.py plugins/happy-coding/agents/<agent-name>.agent.md --level L1
```

## 早見表

| 段階 | 決めること |
| --- | --- |
| 役割定義 | 1 文の責務、非責務、隣接 agent との境界 |
| 権限設計 | model、tools、read-only かどうか |
| 草案化 | template に沿った frontmatter、原則、本文構成 |
| 整合性確認 | 近接 agent との比較 |
| 初期検証 | agent validator で骨格確認 |

## 共通リソース

- `../../_agent/` — agent authoring の内部資産
- `../../_agent/references/agent-template.md` — agent.md の雛形
- `../../_eval/scripts/validate_agent.py` — agent validator
- `../validate-authoring/` — 変更後の検証ルート

## 注意点

- **Skill で足りるものを Agent にしない**: 専門 agent は強力ですが、責務の固定コストも大きいです。
- **model を先に固定しない**: 必要な reasoning と権限を見てから決めたほうが、過不足が出にくいです。
- **`原則` セクションを省略しない**: `docs/PHILOSOPHY.md` を agent 固有の判断原則に落とし込む部分が、既存 agent 群との一貫性を支えます。
- **既存 agent の文体を無視しない**: 近い責務の agent と型が揃っているほうが、利用者は学習しやすくなります。
