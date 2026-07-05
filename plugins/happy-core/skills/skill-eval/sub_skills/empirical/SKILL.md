---
name: empirical
description: >
  skill の指示が別の実行者に明瞭に届くかを実証的に確認する。skill を新規作成・大幅改訂した直後、または挙動が期待通りにならない原因を
  指示側の曖昧さに求めたいとき。
---

# 指示明瞭性を実証的に確認する

この sub-skill は、`empirical-prompt-tuning` skill を **skill 評価の文脈** で使う際の入口です。subagent dispatch が必要なため、dispatch 不能環境では適用できません。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


benchmark 比較（`../benchmark/`）とは測る問いが異なります。benchmark は「新版は旧版より良くなったか」、empirical は「この指示は別の実行者にも明瞭か」を問います。両者を同じ iteration で混在させないでください。

## こんなときに使う

- skill の trigger 文・workflow・条件分岐が「自分には明瞭に見えるが他者に伝わるか」を確かめたいとき
- 改善後の指示を出荷前に実行者視点でテストしたいとき
- benchmark 比較の前に、まず指示品質を軽く確認したいとき

## ワークフロー: 指示明瞭性を確認する

### ステップ 1 — `empirical-prompt-tuning` skill を呼ぶ

この sub-skill はルーティング用です。実際の手順は `empirical-prompt-tuning` に定義されています。

対象プロンプト（SKILL.md 全文）とシナリオ 2〜3 種を用意してから、`empirical-prompt-tuning` のワークフローに従って進めます。

### ステップ 2 — 結果を benchmark ルートの判断に接続する

empirical で「指示が明瞭である」ことが確認できたら、次の behavioral 比較が意味を持ちます。empirical でまだ不明瞭点が残るなら、benchmark を先に走らせても曖昧な改善しか得られません。

## 環境制約

subagent dispatch ができない環境（既に subagent として動作しているなど）では、`empirical-prompt-tuning` の環境制約節に従い、評価を skip して上位に「empirical evaluation skipped: dispatch unavailable」と明示報告します。

## 共通リソース

- `empirical-prompt-tuning` skill — 実際の手順はこちらに定義
- `../benchmark/` — behavioral A/B 比較への導線

## 注意点

- **この sub-skill に手順を書き込まない**: 手順の正本は `empirical-prompt-tuning` にあります。ここに複製すると 2 箇所の保守が発生します。
- **任意プロンプトへの適用**: skill 以外（task プロンプト、CLAUDE.md 節など）に empirical 評価を使いたい場合は、`empirical-prompt-tuning` を直接呼んでください。
