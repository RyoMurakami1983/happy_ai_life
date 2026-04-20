---
name: evaluate
description: >
  スキルの行動変化を測定する。Use when: trigger 精度、出力品質、回帰リスクを
  実証的に確認したいとき。
---

# スキルを評価する（委譲ポインター）

このルートは `skill-eval` skill に移管されました。

behavioral eval の全手順（ケース設計、benchmark 比較、artifact 昇格、次アクション判断）は `skill-eval` の `sub_skills/benchmark/` に定義されています。指示の明瞭性確認には `sub_skills/empirical/` を使います。

## 移行先

- **benchmark 比較**: `skill-eval` → `sub_skills/benchmark/`
- **指示明瞭性の確認**: `skill-eval` → `sub_skills/empirical/`

## このルートに残っているもの

`../validate/` の L4 段階（「behavior が焦点のときだけ L4 へ回す」）からの参照は引き続き機能します。回された先として `skill-eval` を呼んでください。
