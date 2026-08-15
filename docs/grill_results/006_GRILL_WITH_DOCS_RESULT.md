# 006 PRD: skill 命名体系の全面刷新

## Goal

Happy AI Life の skill 命名を、**誤解しにくさを最優先しつつ短くする** 方針へ刷新する。plugin slug は維持し、skill slug はトップレベル / 評価 / 安全 / 入口を説明的に保ちながら、文脈で一意な child / leaf だけを短縮する。

## Fact

- 最優先は「短さ」より「誤解しにくさ」。
- plugin 名（`happy-core` / `happy-coding`）は維持する。
- 短縮対象は skill 名側に限定する。
- 略称は **文脈で一意な leaf / 子 skill だけ** に許す。
- **評価・安全・入口 skill は略称禁止**。
- 失敗条件は **初見ユーザーが役割を推測できない名前になること**。
- `disable-model-invocation: true` は orchestration 親が route / handoff に徹する意図を示す frontmatter としては使うが、Copilot CLI では可視性制御や manual-only 保証には使わない。

## Inference

- rename は一律短縮ではなく、**保護対象** と **短縮許可対象** を分ける必要がある。
- 最初の実装対象は、既に親文脈が強く、かつ slug が長い child / leaf から着手するのが安全。
- `typescript` -> `ts` や `python` -> `py` のような略称は developer 文脈で一般的だが、`eval` や `authoring` 系は衝突しやすく危険。
- `disable-model-invocation` は命名刷新と同じく「意味の明文化」が必要であり、frontmatter 運用規約に落とす価値がある。

## Success Criteria

- 命名ポリシーが docs / ADR / conventions に明文化される。
- 保護対象（トップレベル / 評価 / 安全 / 入口）と短縮許可対象（文脈で一意な child / leaf）が区別される。
- 少なくとも明確に短縮しても誤解しにくい skill slug 群が rename される。
- `disable-model-invocation` の扱いが docs / CONTEXT に整合して記載される。
- skill map / tests / plugin manifest checks が新命名へ追随する。

## Out of Scope

- plugin slug の変更。
- slash command 表示名と内部 slug の分離機構の実装。
- すべての skill を同一 PR で rename し切ること。
- Copilot CLI の `disable-model-invocation` 挙動そのものを変更すること。

## Next

`docs/design/006_TECHNICAL_DESIGN.md` と `docs/plan/006_PLAN.md` に落とし、命名ポリシー確立 → child / leaf rename → docs / test 追随の順で実装する。
