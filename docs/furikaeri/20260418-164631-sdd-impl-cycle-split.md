# sdd-impl-cycle-split

**日時**: 2026-04-18  
**形式**: KPT  

## Executive Summary

`app.py` の home sync 専用 launcher 縮小を `/sdd` フルルートで実装した。spec → design → PLAN → rubber-duck → fleet → 直接実装 → 再レビュー → PR という流れで完了。fleet agent タイムアウトという出戻りを経て「sdd を実装前フェーズ専用に特化させ、実装後フローは別スキルで担う」という設計分割の気づきを得た。

## Session Story

1. `/sdd` 起動 → spec-workshop（from-draft）→ design-workshop（standard）→ PLAN mode でゴール・制約・段階を固めた
2. rubber-duck 事前レビューで docs 更新忘れ・`test_repo_secure_check.py` 削除禁止の 2 ブロッカーを事前検出、計画修正
3. fleet に `happy-env-core` agent を投入 → 240 秒タイムアウト。`import json` / `TypedDict` 2 行のみ削除で未完了終了
4. 直接実装に切り替え。edit ツールで `happy_env.py` を 8 回編集（コンパクション中断あり）
5. テスト・lint・型チェック: 70 passed, ruff/ty 全 pass
6. rubber-duck 再レビュー → 問題なし
7. ブランチ `feat/home-sync-only-launcher` → コミット → PR #73 作成

**使用スキル**: sdd, spec-workshop, design-workshop, furikaeri-practice  
**出戻り**: fleet agent タイムアウト → 直接実装へフォールバック

## Reflection

### Keep

- `sdd` の spec → design → PLAN フローは素直に機能した
- rubber-duck 事前レビューで実装前にブロッカーを 2 件検出できた
- edit ツール直接実装へのフォールバック判断が早く、後続作業への影響を最小化できた

### Problem

- `sdd` が実装後の工程（fleet / review / furikaeri / PR / PR review 対応）まで含んでおり、責務が広すぎた
- fleet agent が 240 秒でタイムアウト。「実装 agent が失敗したときの戻り先」が手順として明文化されていなかった
- 実装 → 再レビュー → furikaeri → PR → PR review 対応という後半フローに対応するスキルが存在しない

### Try

- **sdd を実装前フェーズ専用に特化させる**: spec → design → plan handoff まで。実装トリガーを外す
- **新スキル `impl-and-ship` を作成する**: fleet 前提のマルチエージェント実装 → rubber-duck 再レビュー → furikaeri → PR 作成 → 1 回の PR review 対応までをカバー

### 5 つのなぜ（fleet タイムアウトの根因）

1. fleet agent がタイムアウトした
2. 削除量が多く判断ポイントも多いため、agent が調査ループに入った
3. fleet 適合条件（独立モジュール・削除系・大量行数）の判断基準が曖昧だった
4. 実装フェーズを担うスキルが存在せず、fleet 判断がアドホックになっていた
5. **改善箇所**: 実装フェーズスキルに「fleet 適合判定」と「タイムアウト時の直接実装フォールバック」を明文化する

### SMART

- **S**: `sdd` を spec → plan handoff 専用に絞り、新スキル `impl-and-ship` として実装フェーズを切り出す
- **M**: `sdd` から実装トリガーが消え、`impl-and-ship` が fleet 判定 → 実装 → review → furikaeri → PR → PR review の 1 サイクルをカバーしていること
- **A**: `copilot-authoring` スキル経由で既存 `sdd` の更新と新スキル作成を行う
- **R**: fleet タイムアウト後の迷いと後半フローの責務不在を解消する
- **T**: 次の `/sdd` 利用セッションまでに `impl-and-ship` の初版を作成する

## Session Notes

- `happy_env.py`: 720 行 → 約 90 行（TypedDict / repo 全関数 / confirm 関数 / 定数 / GUI repo ボタン削除）
- PR #73: `feat/home-sync-only-launcher` → main
- `test_repo_secure_check.py` は `happy_env` 依存を外して `json.loads` + `Any` に変更。スクリプトテストは維持

## Next Steps

- `impl-and-ship` スキル初版を `copilot-authoring` 経由で作成する
- `sdd` の実装トリガー部分を削除・更新する（PLAN handoff で終わる形に）
