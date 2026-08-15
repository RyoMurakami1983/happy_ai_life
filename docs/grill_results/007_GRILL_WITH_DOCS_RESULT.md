# 007 PRD: dotnet family を internal sub-skill 化する

## Goal

dotnet 関連 skill を top-level の独立公開 skill として並べるのをやめ、`dotnet` を唯一の公開入口にした family router へ再編する。内部では `sub_skills/` に分解し、親文脈で一意な短い leaf 名を許す。

## Fact

- 現在の plugin / test 前提では、独立公開 skill は `plugins/<plugin>/skills/<slug>/SKILL.md` の 1 階層で列挙される。
- `dotnet` はすでに薄い router として存在し、複数の .NET skill へ振り分けている。
- ユーザー方針は「短さより誤解しにくさ」「plugin 名は維持」「文脈で一意な leaf だけ略称可」。
- dotnet family は **hard cutover now** で `dotnet` 配下へ寄せる。
- dotnet family は **公開入口を `dotnet` に一本化** する。
- dotnet 配下の leaf は **`dotnet-` prefix を落とす**。

## Inference

- 今の top-level dotnet leaf は、一覧を長くしつつ、親文脈がないため略称も使いにくい。
- `dotnet/sub_skills/*` に移すと、公開 surface を減らしながら `cs-concurrency` / `modern-cs` / `type-perf` のような短い leaf 名が自然になる。
- plugin / skill map / tests は top-level 列挙前提なので、移設と同時に期待値更新が必要。
- 既存の直接 invocation は breaking change になるため、PR と docs に互換性注意が必要。

## Success Criteria

- `dotnet` が唯一の公開入口として残る。
- dotnet family の leaf skill が `plugins/happy-coding/skills/dotnet/sub_skills/*/SKILL.md` に移る。
- leaf 名が親文脈前提の短い名前に変わる。
- `docs/SKILL_MAP.md` と関連 docs が `dotnet` family router 構造を説明する。
- targeted tests / validator / review が通る。

## Out of Scope

- 他の family (`ts-tauri`, `linux-server-ops` など) まで同時に internal sub-skill 化すること。
- plugin 名変更。
- alias / shim による旧 slug 互換を残すこと。

## Next

`docs/design/007_TECHNICAL_DESIGN.md` と `docs/plan/007_PLAN.md` に落とし、dotnet router 再設計 -> sub-skill 移設 -> docs / tests 追随 -> gate の順で実装する。
