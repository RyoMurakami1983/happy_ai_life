# impl-and-ship スキル初版作成

**日時**: 2026-04-18  
**形式**: KPT

## Executive Summary

前回 KPT の SMART 目標（sdd の実装フェーズ切り出し）を今回セッションで完了した。`copilot-authoring` skill 経由で sdd を spec→plan handoff 専用に改善し、新スキル `impl-and-ship` を初版作成。rubber-duck review で設計上の 4 ブロッカーを事前検出・修正してから実装に入り、L1 validation PASS・PR #74 作成まで到達した。

## Session Story

1. 前回 KPT の SMART 目標を受け取り、`copilot-authoring` skill 起動
2. sdd 全 sub-skills（from-scratch / from-spec / from-design / from-plan / resume）と skill 規約を並行調査
3. 変更型を抽象化（sdd 改善型 + impl-and-ship 新規作成型）
4. **rubber-duck review** で設計に 4 ブロッカー検出：
   - fleet 判定が bootstrap 前に来ていた（危険）
   - slice loop と ship flow が混在していた（PASS = 次 slice、ではなく PASS = PR に見えた）
   - furikaeri が PR review 前に来ていた（PR review の学びが入らない）
   - sdd sub-skills 全部（5 ファイル）の更新が計画から漏れていた
5. 全指摘を設計に反映して実装：sdd SKILL.md + 5 sub-skills + impl-and-ship/SKILL.md
6. L1 validation 両 PASS → home-template 更新 → commit → PR #74 作成

**使用スキル**: copilot-authoring, rubber-duck agent  
**出戻り**: 設計段階で 4 ブロッカー検出 → 設計修正後に実装（実装後の出戻りなし）

## Reflection

### Keep

- rubber-duck を実装前に走らせたことで 4 ブロッカーを設計段階で潰せた（実装後修正ゼロ）
- `copilot-authoring` の「抽象化 → review → 具体実装」という型が設計整理に有効に機能した
- sdd の複数 sub-skills を並行 view で調査し、変更漏れを early-detect できた
- L1 validation を commit 前に実行し、構造健全性を確認するフローを踏めた

### Problem

- 最初の設計で fleet 判定を bootstrap の前に置いていた（bootstrap 前の fleet は bootstrap 失敗を量産する）
- slice loop（内側）と ship flow（外側）を最初から分けて設計できなかった
- `impl-and-ship` 実装対象として SKILL.md 本体のみを見ており、sdd sub-skills の全更新が計画から漏れていた

### Try

- **skill の workflow を設計するとき「内側ループ」「外側フロー」を最初の段階で明示的に分けて記述する**（混在は rubber-duck で検出されるが、最初から分けた方が速い）
- **fleet 判定のデフォルト前提チェック**: 「bootstrap + contract 後」を skill 設計時のデフォルトルールとして意識する
- **router 型 skill の更新時は子 sub-skill 全ファイルをデフォルトで変更対象に含める**（SKILL.md だけに目が行きがち）

### 5 つのなぜ（sub-skills 全更新漏れの根因）

1. sdd sub-skills の更新が計画から漏れた
2. 変更の影響範囲を「親 SKILL.md」に限定して考えていた
3. router 型 skill では親と子が同一フロー記述を持つ設計になっており、親だけ変えると子と不整合が起きる
4. router の変更時に「子 sub-skill も必ず確認する」というチェックが手順になかった
5. **改善箇所**: `improve-existing` sub-skill か skill 設計の注意点に「router 更新時は子 sub-skill 全確認」を追加する

### SMART

- **S**: `impl-and-ship` の初回利用時に、workflow の順序（bootstrap → fleet → slice loop → ship flow → furikaeri）が迷わず機能することを検証する
- **M**: 次の `/sdd` or `/impl-and-ship` セッションで、実装サイクルを止まらずに通せること
- **A**: 現在の `impl-and-ship` 初版でそのまま試せる
- **R**: 「fleet タイムアウト後の迷い」と「後半フローの責務不在」を解消できているかの実証
- **T**: 次の実装タスクで使う際に確認する

## skill 改善提案

1. **`copilot-authoring/sub_skills/improve-existing`**: 「router 型 skill の更新時は子 sub-skill を全確認する」を注意点に追加する（今回の漏れを同種の出戻りとして防ぐ）

## Session Notes

- PR #74: `feat/impl-and-ship-skill` → main
- sdd: description、全体フロー、5 sub-skills すべて更新済み
- impl-and-ship: `SKILL.md` + `references/` 2 ファイル作成済み
- L1 validation: `sdd/SKILL.md` / `impl-and-ship/SKILL.md` 両 PASS

## Next Steps

- PR #74 をマージ後に home sync を実行して `$HOME/.copilot/skills/` に反映する
- 次の実装タスクで `impl-and-ship` を実際に使い、SMART の検証を行う
- `improve-existing` の「router 更新時チェック」追加を Issue 化する
