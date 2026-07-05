---
name: new-skill
description: >
  新しい custom skill を既存 conventions に沿って立ち上げる。試作から
  `plugins/*` 配布へ昇格する際の name / description 設計も扱う。skill の新規追加、router / sub-skill の雛形作成、手作業 workflow の skill 化をしたいとき。
---

# Skill を新規作成する

この sub-skill は、新しい workflow を再利用可能な skill package に落とし込むための入口です。先にゴール、trigger、成功条件を固める理由は、topic の説明ではなく実行可能な workflow として設計するためです。

## こんなときに使う

- 新しい workflow を `plugins/happy-core/skills/` または `plugins/happy-coding/skills/` に追加したいとき
- 既存の手作業プロンプトを skill として定着させたいとき
- router と sub-skill をまとめて立ち上げたいとき
- `works/` の草案を `plugins/*` に昇格し、frontmatter の name / description を配布向けに整えたいとき
- 公開 / 内部 / repo 専用の置き場を決めながら草案化したいとき

## ワークフロー: skill を作る

### ステップ 1 — goal / scope / trigger / 配布先を定義する

skill が何を達成し、どの入力で起動され、どこまで面倒を見るかに加えて、配布先（`works/` か `plugins/*` か）を 1 段落で定義します。成功条件と確認手段も短く置くと、`description` と workflow が自律実行しやすくなります。

### ステップ 1.5 — 昇格時の name / description を先に固定する

`plugins/*` 配布へ昇格する前提なら、frontmatter の `name` と `description` に「何を束ねる skill か」「どんなときに使うか（trigger phrase）」を先に反映します。ここを後回しにすると、本文だけ直って metadata が古いまま残り、起動精度と発見性が落ちます。
このとき出力先も `plugins/happy-core/skills/` または `plugins/happy-coding/skills/` に固定し、`works/` は試作専用として切り分けます。
配布先の選択に迷う場合は、横断的な作業基盤（authoring / Git / GitHub / handoff など）は `happy-core`、実装・検証・言語別開発フローは `happy-coding` を優先します。

### ステップ 2 — flat / router / suite を選ぶ

一本道なら flat skill、1 つの入口から複数 route に分けるなら router、複数の sibling skill を束ねるなら suite を選びます。理由は、構造選択を後回しにすると後半で大きな移設が発生しやすいからです。

### ステップ 3 — 雛形を起こす

既存の `_skill` 資産を再利用して雛形を起こします。router が必要なら作成スクリプトで生成し、単発 workflow なら雛形から始めると差分が小さく保てます。

```powershell
uv run python plugins\happy-core\skills\copilot-authoring\_skill\scripts\create_skill.py --name <skill-name> --description "<description>" --output-root plugins/happy-core/skills
uv run python plugins\happy-core\skills\copilot-authoring\_skill\scripts\create_skill.py --name <router-name> --description "<description>" --type router --sub-skills <route-a>,<route-b> --output-root plugins/happy-core/skills
```

### ステップ 4 — hot path を短く保つ

`SKILL.md` には入口判断と主要 workflow を残し、細かい資料は `references/` や bundled asset へ逃がします。なぜなら、入口が長くなるほど利用者が route を見失いやすくなるためです。

### ステップ 5 — 早めに L1 を通す

草案の早い段階で validator を通し、命名、trigger phrase、workflow 構造の欠けを先に直します。細部を磨く前に骨格の不備を消すほうが安全です。
草案の完了条件は「テンプレートのプレースホルダーが残っていない」「`description` と `こんなときに使う` が実文で埋まっている」「L1 が PASS」の 3 点です。

```powershell
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\<skill-name>\SKILL.md --level L1
```

## 早見表

| 段階 | 決めること |
| --- | --- |
| 意図定義 | goal、scope、trigger、成功条件、確認手段、配布先 |
| 昇格準備 | name、description、trigger phrase（Use when / こんなときに使う） |
| 配布先選択 | `happy-core`（横断基盤）/ `happy-coding`（実装フロー） |
| 構造選択 | flat / router / suite |
| 草案化 | template or script で skeleton を起こす |
| 収束 | hot path と references の境界を整え、プレースホルダーを解消する |
| 初期検証 | L1 validation を通す |

## 共通リソース

- `../../_skill/_foundation/TEMPLATE.md` — workflow skill の最小雛形
- `../../_skill/_foundation/ROUTER_TEMPLATE.md` — router 親 skill の雛形
- `../../_skill/_foundation/SUB_SKILL_TEMPLATE.md` — nested sub-skill の雛形
- `../../_skill/scripts/create_skill.py` — skill / router / sub-skill 作成スクリプト
- `../validate-authoring/` — 作成後の検証ルート

## 注意点

- **built-in 名に寄せすぎない**: 独自 skill の名前が platform command と競合すると、使い分けの学習コストが増えます。
- **一本道の workflow に router を使わない**: route が 1 本なら構造だけが増え、保守性を落とします。
- **最初から detail を詰め込みすぎない**: 実行時にしか要らない説明は `references/` に逃がしたほうが再利用しやすいです。
