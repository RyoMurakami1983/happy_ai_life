---
name: new-skill
description: >
  新しい custom skill を既存 conventions に沿って立ち上げる。Use when:
  skill の新規追加、router / sub-skill の雛形作成、手作業 workflow の skill 化をしたいとき。
compatibility: "../../../skill/_foundation/CONVENTIONS.md, ../../../skill/scripts/create_skill.py"
---

# Skill を新規作成する

この sub-skill は、新しい workflow を再利用可能な skill package に落とし込むための入口です。先にゴール、trigger、成功条件を固める理由は、topic の説明ではなく実行可能な workflow として設計するためです。

## こんなときに使う

- 新しい workflow を `home-template/.copilot/skills/` に追加したいとき
- 既存の手作業プロンプトを skill として定着させたいとき
- router と sub-skill をまとめて立ち上げたいとき
- 公開 / 内部 / repo 専用の置き場を決めながら草案化したいとき

## ワークフロー: skill を作る

### ステップ 1 — goal / scope / trigger を定義する

skill が何を達成し、どの入力で起動され、どこまで面倒を見るかを 1 段落で定義します。成功条件と確認手段も短く置くと、`description` と workflow が自律実行しやすくなります。

### ステップ 2 — flat / router / suite を選ぶ

一本道なら flat skill、1 つの入口から複数 route に分けるなら router、複数の sibling skill を束ねるなら suite を選びます。理由は、構造選択を後回しにすると後半で大きな移設が発生しやすいからです。

### ステップ 3 — 雛形を起こす

既存の `skill` 資産を再利用して skeleton を作ります。router が必要なら script で生成し、単発 workflow なら template から始めると差分が小さく保てます。

```powershell
uv run python home-template/.copilot/skills/skill/scripts/create_skill.py --name <skill-name> --description "<description>"
uv run python home-template/.copilot/skills/skill/scripts/create_skill.py --name <router-name> --description "<description>" --type router --sub-skills <route-a>,<route-b>
```

### ステップ 4 — hot path を短く保つ

`SKILL.md` には入口判断と主要 workflow を残し、細かい資料は `references/` や bundled asset へ逃がします。なぜなら、入口が長くなるほど利用者が route を見失いやすくなるためです。

### ステップ 5 — 早めに L1 を通す

草案の早い段階で validator を通し、命名、trigger phrase、workflow 構造の欠けを先に直します。細部を磨く前に骨格の不備を消すほうが安全です。

```powershell
uv run python home-template/.copilot/skills/skill/_eval/scripts/validate_skill.py home-template/.copilot/skills/<skill-name>/SKILL.md --level L1
```

## 早見表

| 段階 | 決めること |
| --- | --- |
| 意図定義 | goal、scope、trigger、成功条件、確認手段、配布先 |
| 構造選択 | flat / router / suite |
| 草案化 | template or script で skeleton を起こす |
| 収束 | hot path と references の境界を整える |
| 初期検証 | L1 validation を通す |

## 共通リソース

- `../../../skill/_foundation/TEMPLATE.md` — workflow skill の最小 template
- `../../../skill/_foundation/ROUTER_TEMPLATE.md` — router 親 skill の template
- `../../../skill/_foundation/SUB_SKILL_TEMPLATE.md` — nested sub-skill の template
- `../../../skill/scripts/create_skill.py` — skill / router / sub-skill scaffold
- `../validate-authoring/` — 作成後の検証ルート

## 注意点

- **built-in 名に寄せすぎない**: 独自 skill の名前が platform command と競合すると、使い分けの学習コストが増えます。
- **一本道の workflow に router を使わない**: route が 1 本なら構造だけが増え、保守性を落とします。
- **最初から detail を詰め込みすぎない**: 実行時にしか要らない説明は `references/` に逃がしたほうが再利用しやすいです。
