---
name: copilot-authoring
disable-model-invocation: true
description: >
  こんなときに使う: Copilot の custom skill / repository instructions authoring で、
  新規作成、既存改善、静的検証、実動評価のどれをしたいかを仕分け、適切な専門
  skill へつなぎたいとき。複数責務を 1 つの skill に詰めず、必要なら薄い
  orchestration skill として束ねたいときに使う。
---

# Copilot authoring

この skill は、authoring 作業を 1 つの大きな workflow に詰め込まず、対象ごとに分けた専門 skill へつなぐためのオーケストレーションです。`interview-with-docs` と同じく、親は薄く保ち、詳細な手順は子 skill や reference に置きます。ゴールは、authoring の入口を 1 本に保ちながら、成功条件と確認手段を各専門 skill 側へ正しく渡すことです。

## こんなときに使う

- 新しい skill を作るのか、既存 skill を改善するのかを先に切り分けたいとき
- skill と instructions のどこを直すべきか迷っているとき
- 静的な構造確認で十分か、実動評価まで進むべきかを分けたいとき
- 複数の authoring 機能を 1 つに混ぜず、薄い親から専門 skill へ handoff したいとき

## 役割の境界

- `sub_skills/new-skill/` は、新しい skill の作成と昇格準備を担当します。
- `sub_skills/instructions-authoring/` は、repo-wide / path-specific instructions の作成と整理を担当します。
- `sub_skills/improve-existing/` は、既存資産の wording、境界、handoff の改善を担当します。
- `sub_skills/validate-authoring/` は、authoring 資産の静的な構造確認を担当します。
- `happy-core@skill-eval` は、別実行者でも通じるかの評価窓口です。
- `happy-core@empirical-prompt-tuning` は、指示の曖昧さや裁量補完を実動で詰める窓口です。

## 実行ルール

1. 新規作成なら、対象に応じて `sub_skills/new-skill/` または `sub_skills/instructions-authoring/` へ進みます。
2. 既存資産の責務整理や wording 修正なら、まず `sub_skills/improve-existing/` へ進みます。
3. 構造や静的品質の確認が主目的なら、`sub_skills/validate-authoring/` へ進みます。
4. 別実行者にも同じように通じるか、または明瞭性を実動で測りたいなら、`happy-core@skill-eval` または `happy-core@empirical-prompt-tuning` へ進みます。
5. `plugins/*` 配下の配布中 asset で利用者体験が変わる場合は、`references/plugin-versioning.md` で version 更新要否を確認します。

> 実装上の明示参照としては `happy-core@skill-eval` のような plugin-qualified 名を使い、実行時の会話では `/skill-eval` のような短い呼び出し名で扱うのが自然です。

## 迷ったときの判断

- 1 つの primary purpose に還元できるなら、新しい親 skill を増やさず、既存の専門 skill を使います。
- 複数の skill をまたぐ必要があるなら、親に詳細手順を詰め込まず、`interview-with-docs` 型の薄い orchestration にします。
- 改善と評価が同時に必要でも、まず authoring 資産を直し、その後で評価ルートへ送ります。
- 新しい custom agent は標準 authoring route では作りません。必要性が出た場合は、まず `improve-existing` で既存 skill では足りない理由を明文化し、別 issue / design 判断へ戻します。

## 注意点

- 親 skill に child skill の詳細手順を複製しないでください。
- authoring の静的確認と、別実行者による実動評価を 1 つの手順として混ぜないでください。
