# Grill with Docs Result

## 対象

Loop Engineering と PrivateEval を、貼付された新規 plugin 一式案ではなく、`happy-core` 配布の新規 top-level skill として入れる前提の整理。

## 読んだ source of truth

- `README.md`
- `docs/DEVELOPMENT.md`
- `docs/AUTHORING.md`
- `docs/PHILOSOPHY.md`
- `docs/adr/distribution-strategy.md`
- `docs/adr/happy-ai-life-plugin-split-and-skill-slug-simplification.md`
- `plugins/happy-core/README.md`
- `plugins/happy-core/plugin.json`
- `plugins/happy-core/skills/copilot-authoring/SKILL.md`
- `plugins/happy-core/skills/skill-eval/SKILL.md`
- `plugins/happy-core/skills/empirical-prompt-tuning/SKILL.md`
- 貼付文書 `paste-1782852015672.txt`

## Fact

- 公開配布の正本は `plugins/happy-core/` と `plugins/happy-coding/` であり、新しい第三 plugin を増やす案は既存の配布境界と衝突する。
- `happy-core` は汎用 workflow、知識化、GitHub 運用、Copilot asset authoring、評価系 skill を持つ。
- `skill-eval` は skill / prompt 資産の評価入口であり、`empirical-prompt-tuning` は別実行者による明瞭性評価を担当する。
- 貼付文書の中心概念は `Observe -> Plan -> Act -> Verify -> Evaluate -> Reflect -> Patch -> Stop or Loop` と、PrivateEval 5軸による品質ゲートである。

## Inference

- Loop Engineering は coding 専用ではなく、authoring、PR、振り返り、評価、知識化にもまたがるため `happy-core` が自然な配置先である。
- 初回差分は `loop-engineering` skill 本体と必要最小限の references / 導線に絞り、テンプレート一式はレビュー後の後続 PR に分ける方が既存方針の「外科的対応」に合う。
- PrivateEval は `skill-eval` の置き換えではなく、Loop Engineering 内の品質ゲートとして既存 skill へ接続するのが重複を避けやすい。

## 解決した用語

- **Loop Engineering**: Observe、Plan、Act、Verify、Evaluate、Reflect、Patch、Stop or Loop を明示的に回し、検証と評価で止めどきを決める開発・改善の型。
- **PrivateEval**: Loop Engineering の Evaluate で使う、Happy AI Life 向けの自己評価ゲート。
- **組織視点**: 旧案の「会社視点」を置き換える PrivateEval 軸。個人の速さだけでなく、チームの保守性、安全性、自走、レビューしやすさに効いているかを見る。

## 更新した docs

- `docs/grill_results/001_GRILL_WITH_DOCS_RESULT.md`
- `CONTEXT.md` はこの repo で未運用のため新設しない。用語定義は初回 `loop-engineering` skill の本文に置く。

## ADR 判断

- 新規 ADR は現時点では不要。第三 plugin を作らず `happy-core` に入れる判断は、既存 ADR `distribution-strategy.md` と `happy-ai-life-plugin-split-and-skill-slug-simplification.md` に従うだけであり、新しい配布方針ではない。

## Blocking Unknown

- なし。

## 推奨される次工程

- `design-and-plan` で `loop-engineering` skill の責務、既存 skill との接続、初回 PR と後続テンプレート追加 PR の切り分けを作る。
