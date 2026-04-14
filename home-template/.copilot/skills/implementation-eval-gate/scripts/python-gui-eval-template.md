# Python GUI Eval Template

## Purpose

Python ベースの GUI / pygame / desktop tool を対象に、実装 slice の受け入れ条件を確認するための最小テンプレートです。

## When to use

- pygame などの描画ループを含むアプリを確認したい
- Python GUI / automation 周りを軽く触って評価したい
- desktop 画面の状態やイベント反応を evidence にしたい

## Basic loop

1. app を起動する
2. main window / game loop を確認する
3. contract の主要操作を 1 つずつ実行する
4. observed state と expected state を比較する
5. `PASS` / `FAIL` / `REPLAN_REQUIRED` を返す

## Evidence to capture

- 現在の画面状態
- 入力イベントと反応
- frame / state の変化
- 期待値との差分

## Notes

- GUI automation は環境依存が強いので、最初は contract を 1 slice に絞る
- 画面認識が難しい場合は、ログや state dump と併用する
