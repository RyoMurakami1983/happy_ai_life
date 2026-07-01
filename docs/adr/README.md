# ADR 一覧

このディレクトリには、`happy_ai_life` の設計判断を残します。  
README や運用文書では「何を使うか」を案内し、ここでは「なぜそうしたか」を扱います。

## 使い方

- 方針の理由を確認したいときは、まずこの一覧から近いテーマを開く
- 現在の運用を知りたいときは、新しい日付の ADR を優先して読む
- README / docs と ADR が食い違って見えたら、実装とこの一覧を見比べる
- 新しい ADR には `Status: Accepted / Superseded / Retired` を置く

## Status

| Status | 意味 |
| --- | --- |
| Accepted | 現在も有効な判断 |
| Superseded | 後続 ADR または docs に置き換えられた判断 |
| Retired | 現在の運用では使わない判断 |

## 主な分類

### 配布と同期

- [distribution-strategy.md](distribution-strategy.md) — plugin primary / home sync 最小 bootstrap / repo bootstrap 分離
- [happy-ai-life-plugin-split-and-skill-slug-simplification.md](happy-ai-life-plugin-split-and-skill-slug-simplification.md) — `happy-core` / `happy-coding` への分割
- [home-sync-governance.md](home-sync-governance.md) — home sync の managed / user-owned 境界
- [home-sync-partial-mirror-and-home-bootstrap.md](home-sync-partial-mirror-and-home-bootstrap.md) — diff sync と bootstrap package の経緯
- [home-sync-whitelist.md](home-sync-whitelist.md) — whitelist copy から current state への経緯

### instructions / agent / skill

- [instruction-hierarchy-and-authoritative-source.md](instruction-hierarchy-and-authoritative-source.md) — instruction 階層と正本
- [agent-dispatch-rules.md](agent-dispatch-rules.md) — agent dispatch の基準
- [shihan-agents-operating-model.md](shihan-agents-operating-model.md) — custom agent の運用モデル

### 安全性と Git 運用

- [main-branch-protection-and-githooks.md](main-branch-protection-and-githooks.md) — branch protection と Git hooks

### session continuity

- [session-continuity-hooks-mvp.md](session-continuity-hooks-mvp.md) — continuity hooks の初期方針
- [session-continuity-retirement.md](session-continuity-retirement.md) — 自動継承導線の整理
- [session-share-document.md](session-share-document.md) — session 文書共有

### 個別テーマ

- [dotnet-reproducible-environment-knowledge-distribution.md](dotnet-reproducible-environment-knowledge-distribution.md) — dotnet 環境知識の配布

## 読み始めの目安

1. 配布方針を知りたい → `distribution-strategy.md`
2. home sync の境界を知りたい → `home-sync-governance.md`
3. instructions の正本を知りたい → `instruction-hierarchy-and-authoritative-source.md`
4. plugin 分割の理由を知りたい → `happy-ai-life-plugin-split-and-skill-slug-simplification.md`
