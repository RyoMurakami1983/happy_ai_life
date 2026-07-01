# Grill with Docs Result

## 対象

Matt Pocock さんの `skills` repo を参考に、`happy_ai_life` の skill / agent / privateEval / docs を、シンプルで保守しやすい skill ecosystem として整理するための前提整理。

## 読んだ source of truth

- `README.md`
- `docs/DEVELOPMENT.md`
- `docs/AUTHORING.md`
- `docs/QUALITY_GATES.md`
- `docs/grill_results/001_GRILL_WITH_DOCS_RESULT.md`
- `plugins/happy-core/skills/skill-eval/SKILL.md`
- `plugins/happy-core/skills/loop-engineering/SKILL.md`
- `plugins/happy-coding/skills/grill-with-docs/SKILL.md`
- `plugins/happy-coding/skills/design-and-plan/SKILL.md`
- `plugins/happy-coding/skills/implement/SKILL.md`
- 参考: <https://github.com/mattpocock/skills/tree/main>

## Fact

- 公開配布の正本は `plugins/happy-core/` と `plugins/happy-coding/`。
- `works/` は常用前の試作、単発寄りの作業物、配布前の実験置き場。
- `grill-with-docs -> design-and-plan -> implement` の流れは README と `docs/DEVELOPMENT.md` に既にある。
- `docs/grill_results/001_GRILL_WITH_DOCS_RESULT.md` では、PrivateEval は `skill-eval` の置き換えではなく、Loop Engineering 内の品質ゲートとして接続するのが自然と整理されている。
- root `CONTEXT.md` は未運用で、現在は `docs/PHILOSOPHY.md` が価値観と背景の正本になっている。

## Inference

- skill 数が増えているため、個別 skill の追加より先に skill map と router / dependency の明示が必要。
- privateEval は `evals/<skill-id>/` に secret なしの評価ケースを置く形にすると、既存 `skill-eval` と接続しやすい。
- `PHILOSOPHY.md` の日常参照負荷を下げるには、ドメイン語彙を `CONTEXT.md` に切り出すのが自然。
- `SKILL.md` の詳細化が進むと起動時・探索時の負荷が増えるため、短い入口と `references/` への段階的参照が必要。

## 解決した用語

- **skill ecosystem**: 基本 skill、専門 skill、agent、docs、eval が互いに孤立せず、入口、連携、評価、昇格基準を持って育つ構造。
- **privateEval**: repo に入れてよい secret なしの評価ケース群。実会話ログや秘密情報は含めない。
- **skill map**: 基本 skill から専門 skill へどう移るかを示す一覧。skill の重複追加と探索コストを下げる。

## 更新した docs

- `docs/SKILL_ECOSYSTEM_ACTION_PLAN.md`
- `docs/grill_results/002_GRILL_WITH_DOCS_RESULT.md`
- `README.md`

## ADR 判断

- 現時点では新規 ADR は不要。今回の成果は設計判断の確定ではなく、整理と実行アクションの洗い出しであるため。
- `CONTEXT.md` の正式運用、`domain-modeling` skill の追加、privateEval 配置を実装する段階で、戻しにくい配布・評価方針が固まるなら ADR を検討する。

## Blocking Unknown

- なし。

## 推奨される次工程

- `design-and-plan` で、`docs/SKILL_ECOSYSTEM_ACTION_PLAN.md` の「最初のPR候補」を実装可能な slice に分ける。
- 最初の PR は `docs/SKILL_MAP.md`、privateEval の禁止事項、`AUTHORING.md` の skill 作成規律に絞る。
