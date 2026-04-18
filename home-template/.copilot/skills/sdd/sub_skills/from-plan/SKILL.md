---
name: from-plan
description: >
  計画がある状態から実装サイクルを開始する。
  Use when: 計画が揃っていて実装フェーズに入りたいとき。
compatibility: "impl-and-ship"
---

# From Plan — impl-and-ship へ引き継ぐ

このルートは `impl-and-ship` skill に移管されました。

計画（plan.md / todos / PLAN summary）が手元にある場合は、**`impl-and-ship`** を直接使ってください。`impl-and-ship` が bootstrap 確認、contract checkpoint、実装（TDD）、eval gate、review、furikaeri、PR サイクルを担います。

## 移行

```
以前: sdd → from-plan → 実装
現在: sdd → impl-and-ship（計画受け取り → 実装 → 後半サイクル全体）
```

`impl-and-ship` を呼び出すときは、plan artifact のパスまたは内容を渡してください。
