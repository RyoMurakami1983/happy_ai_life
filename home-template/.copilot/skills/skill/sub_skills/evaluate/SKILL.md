---
name: evaluate
description: >
  スキルの行動変化を測定する。Use when: trigger 精度、出力品質、回帰リスクを
  実証的に確認したいとき。
---

# スキルを評価する（委譲ポインター）

このルートは `skill-eval` skill に移管されました。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


behavioral eval の全手順（ケース設計、benchmark 比較、artifact 昇格、次アクション判断）は `skill-eval` の `sub_skills/benchmark/` に定義されています。指示の明瞭性確認には `sub_skills/empirical/` を使います。

## こんなときに使う

- baseline / legacy / current を比較して skill の効果を測りたいとき
- 改善候補が本当に良くなったかを実証したいとき
- prompt の指示が別の実行者にも明瞭かを確認したいとき

## ワークフロー: 委譲ルート

このページは router です。以下のように使い分けてください：

### スキル行動を比較したいとき
→ `skill-eval/sub_skills/benchmark/` へ進む
- ケース設計、baseline / legacy / current 実行、集計、次アクション判定

### プロンプト明瞭性を確認したいとき
→ `skill-eval/sub_skills/empirical/` へ進む
- バイアス排除の実行者に動かしてもらい、両面評価

## 移行先

- **benchmark 比較**: `skill-eval` → `sub_skills/benchmark/`
- **指示明瞭性の確認**: `skill-eval` → `sub_skills/empirical/`

## このルートに残っているもの

`../validate/` の L4 段階（「behavior が焦点のときだけ L4 へ回す」）からの参照は引き続き機能します。回された先として `skill-eval` を呼んでください。
