# FlaUI Eval Template

## Purpose

WPF / desktop app を対象に、実装 slice の受け入れ条件を実際の UI 操作で確認するための最小テンプレートです。

## When to use

- .NET WPF 画面を実際に操作して評価したい
- Playwright では見えない desktop UI を確認したい
- コントロールの存在、状態遷移、主要操作を evidence にしたい

## Basic loop

1. generator handoff の runtime launch command で app を起動する
2. desktop window を捕捉する
3. contract の主要操作を実行する
4. UI state と期待値を比較する
5. `PASS` / `FAIL` / `REPLAN_REQUIRED` を返す

## Minimum operations for interactive slices

- window title と main window 捕捉を確認する
- keyboard または主要 control の操作を 1 本以上再現する
- status text / score / restart のような user-visible state を確認する
- 失敗時は screenshot を残す

## Evidence to capture

- window title
- control tree の主要ノード
- 実行した操作
- 期待値と実測値の差分
- 失敗時のスクリーンショット
- 使用した runtime launch command

## Notes

- automation 対象が WPF 以外なら、UIA / WinAppDriver / pywinauto への差し替えを検討する
- 操作が不安定な場合は、contract を小さく切り直す
