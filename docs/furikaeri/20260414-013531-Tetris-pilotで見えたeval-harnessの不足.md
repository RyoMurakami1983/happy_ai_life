# Tetris pilotで見えたeval harnessの不足

## Executive Summary

- 3-stack Tetris pilot を通して、`spec -> design -> plan -> implement -> eval` の前段は概ね機能した一方、interactive app を `PASS` 判定へ押し上げる runtime evidence 導線が不足していることが明確になった。
- TypeScript / Python / WPF はそれぞれ別の小さな詰まりを見せたが、共通の根本要因は「target repo への instructions 未配布」「runtime evidence 基準の弱さ」「generator handoff の粒度不足」だった。
- 改善点は Issue #47〜#50 として分離し、次回は backlog を 1 件ずつ潰しながら harness 側へ還元できる状態にした。

## Session Story

- planner / generator / evaluator 型ハーネスをこの repo に持ち込む前提で、`implementation-eval-gate` と `/sdd` の導線を先に整えた。
- その後、3-stack Tetris pilot を別 repo で実施し、TypeScript、Python、WPF の順に baseline 実装と eval を通した。
- TypeScript は web runtime evidence 不足、Python は test discovery/import 契約、WPF は persisted test artifact 不足が目立ち、最後に cross-stack の改善点を整理して Issue 化した。
- 利用した主な要素は `sdd`、`spec-workshop`、`implementation-eval-gate`、`tdd-coder`、手動の検証コマンド、および issue/furikaeri 導線だった。

## Reflection

### Keep

- 共通 `SPEC.md` / `DESIGN.md` / `EVAL-RUBRIC.md` を先に固定したことで、3 stack の比較軸をぶらさずに進められた。
- generator と evaluator を分けたことで、build/test が通っても `FAIL` を返す批判的な判定ができた。
- pilot の詰まりをその場で `HARNESS-FINDINGS.md` と Issue に落とし、学びを backlog に変換できた。

### Problem

- pilot repo に `.github/instructions/` が配られておらず、母艦の言語 instructions が効く前提で見てはいけない状態だった。
- interactive app 向けの runtime evidence 要件が弱く、TypeScript / Python / WPF のどれも `PASS` に進める次の条件が曖昧だった。
- generator handoff に test artifact path や runtime launch command が不足し、WPF では evaluator 側で証拠を再構成する手戻りが発生した。
- fresh scaffold の contract が弱く、TypeScript では test runner 不在、Python では `unittest discover` の import 契約不足で小さく詰まった。

### Try

- `/sdd` の pilot 開始時に、target repo へ `.github/instructions/` が配布済みか確認する checkpoint を追加する。
- `implementation-eval-gate` に web / pygame / WPF 向けの runtime evidence 要件を追加し、template と判定基準を接続する。
- generator handoff の必須項目に test artifact path、test command、runtime launch command を追加する。
- interactive app pilot の bootstrap checklist を作り、TypeScript の TDD-ready 条件と Python の import-safe 条件を明文化する。

### 5つのなぜ

1. なぜ interactive app が `PASS` にならなかったか: build/test 証拠だけでは live behavior を証明できなかったため。
2. なぜ live behavior を証明できなかったか: runtime evidence の最小要件と観測手順が stack 別に十分定義されていなかったため。
3. なぜ手順が弱かったか: `implementation-eval-gate` は方向性を持っていたが、web / pygame / WPF の具体的な確認条件まで落ちていなかったため。
4. なぜそれが pilot 中まで露見しなかったか: 前段の spec/design/plan は整っており、実装の詰まりより evaluator 側の不足が後半で顕在化したため。
5. なぜ改善先が明確になったか: 3 stack を同じ rubric で比較したことで、言語差より harness 差のほうが支配的だと見えたため。

### SMART

- **Specific**: Issue #47〜#50 の 4 本を入口に、instructions 配布チェック、runtime evidence、generator handoff、bootstrap contract を順に改善する。
- **Measurable**: 次回の pilot で、instructions 未配布を開始時に検出でき、interactive app の `PASS/FAIL` 判定に必要な evidence と起動入口が handoff から辿れる状態にする。
- **Achievable**: 4 本とも docs / skill / template / handoff contract の改善として分離済みで、1 件ずつ小さく実装できる。
- **Relevant**: 今回の主要な手戻りと判定の曖昧さに直接対応している。
- **Time-bound**: 次の改善セッションから Issue #47 を起点に着手する。

### skill 改善提案

- `sdd` に pilot / downstream repo 開始前の instructions 配布チェックを追加する。
- `implementation-eval-gate` に interactive app 向け runtime evidence の stack 別 rubric を追加する。
- generator handoff の型を強め、evaluator が test 実体と起動入口を再探索しなくてよい形にする。

## Session Notes

- pilot repo は最終的に source / docs / handoff のみを tracked に整理し、生成物は `.gitignore` 修正で除外した。
- Issue は公開 repo 向けにローカル絶対パスや個人環境依存の記述を避けて起票した。
- 今回の学びは「言語 rules が弱い」よりも、「rules を target repo に配れていない」「interactive runtime 評価の標準が弱い」に寄っていた。

## Next Steps

- Issue #47 `/sdd: target repo の .github/instructions 配布確認を必須 checkpoint 化する` から着手する。
- Issue #48 `implementation-eval-gate: interactive app 向け runtime evidence 要件を stack別に明文化する` を続ける。
- Issue #49 `generator handoff: test artifact path と runtime launch command を必須項目にする` を反映する。
- Issue #50 `pilot bootstrap: interactive app の scaffold contract を TDD-ready / import-safe に明文化する` を整理する。
