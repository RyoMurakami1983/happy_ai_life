---
name: validate-authoring
description: >
  skill と agent の authoring 資産を出荷前に検証する。Use when:
  draft の骨格確認、改善後の回帰確認、共有前の最低品質確認をしたいとき。
compatibility: "../../../skill/_eval/scripts/validate_skill.py, ../../_eval/scripts/validate_agent.py"
---

# Authoring 資産を検証する

この sub-skill は、skill と agent を同じ入口から検証しつつ、実際の check は対象ごとに分けるためのルートです。入口をそろえる理由は、公開前に「どこまで確認したか」を 1 つの会話で揃えられるようにするためです。

## こんなときに使う

- 新しい skill が最低限の構造を満たすか確認したいとき
- 新しい agent が frontmatter と section 構造を満たすか確認したいとき
- 改善後の asset に回帰がないか見直したいとき
- sync や共有の前に最低限の品質ラインを通したいとき

## ワークフロー: authoring 資産を検証する

### ステップ 1 — 対象を skill / agent に分ける

同じ authoring 資産でも、skill は workflow と route、agent は責務と権限を見るため、最初に対象を分けます。ここを混ぜると、check の意図がぶれます。

### ステップ 2 — skill は既存 validator を通す

skill では既存の `validate_skill.py` を使い、まず L1、必要なら L2 まで進めます。最小構造が崩れている skill は、その先の review に進めません。

```powershell
uv run python home-template/.copilot/skills/skill/_eval/scripts/validate_skill.py home-template/.copilot/skills/<skill-name>/SKILL.md --level L1
uv run python home-template/.copilot/skills/skill/_eval/scripts/validate_skill.py home-template/.copilot/skills/<skill-name>/SKILL.md --level L2
```

### ステップ 3 — agent は同梱 validator を通す

agent では `name` / filename 一致、`Use when:`、必須 section、構造の型を確認します。`## 1. 役割` のような番号付き H2、`## 設計プロセス` / `## レビュープロセス`、師範 agent の legacy mode 構成も許容し、既存 agent 群と同じ型を保ちます。template 系 agent では `原則` と step 構造を最低線とします。これは prose の良し悪しではなく、利用者が agent を見つけて安全に使えるかの最低線です。

```powershell
uv run python home-template/.copilot/skills/copilot-authoring-beta/_eval/scripts/validate_agent.py home-template/.copilot/agents/<agent-name>.agent.md --level L1
uv run python home-template/.copilot/skills/copilot-authoring-beta/_eval/scripts/validate_agent.py home-template/.copilot/agents/<agent-name>.agent.md --level L2
```

### ステップ 4 — 境界変更なら周辺も見る

責務や入口の変化がある場合は、README、dispatch 記述、関連 skill / agent との整合性も見ます。validator だけでは boundary drift は拾いきれないためです。

## 早見表

| 対象 | 最低限の check |
| --- | --- |
| Skill | frontmatter、trigger、workflow、関連導線 |
| Agent | frontmatter、原則を含む必須 section、step 構造、関連導線 |
| 境界変更あり | README、dispatch、近接定義との整合性 |

## 共通リソース

- `../../../skill/_eval/scripts/validate_skill.py` — skill validator
- `../../_eval/scripts/validate_agent.py` — agent validator
- `../improve-existing/` — 指摘を反映する改善ルート

## 注意点

- **validator pass を完成と誤認しない**: 自動 check は骨格確認であり、境界の妥当性までは自動で保証しません。
- **L1 だけで満足しない**: 公開前や共有前は、少なくとも L2 相当の読みやすさも見たほうが安全です。
- **境界変更を prose だけで閉じない**: 周辺の導線が古いままだと、利用時の混乱が残ります。
