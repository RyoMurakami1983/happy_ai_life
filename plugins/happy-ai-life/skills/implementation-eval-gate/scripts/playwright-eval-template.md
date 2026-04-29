# Playwright Eval Template

## Purpose

Web UI を対象に、実装 slice の受け入れ条件を実際の画面操作で確認するための最小テンプレートです。

## When to use

- ブラウザ上でユーザー操作を再現したい
- UI / navigation / form / API 連携をまとめて確認したい
- Playwright で再現できる失敗を evidence として返したい

## Basic loop

1. generator handoff の runtime launch command で app を起動する
2. Playwright で初期描画と主要 UI 要素を確認する
3. contract の各行動を 1 つずつ再現する
4. 失敗した操作と observed result を記録する
5. `PASS` / `FAIL` / `REPLAN_REQUIRED` を返す

## Minimum operations for interactive slices

- 初期描画が崩れていない
- 主要入力（click / key / navigation）の少なくとも 1 本が live に通る
- contract に含まれる状態変化が画面上で確認できる
- 失敗時に screenshot または trace を残せる

## Evidence to capture

- 操作した画面
- 再現した入力
- 期待値と実測値の差分
- 失敗時のスクリーンショットまたは trace
- 使用した runtime launch command

## Return format

```markdown
## Implementation Eval
- Verdict:
- Evidence:
- Failed criteria:
- Required fixes:
- Next action:
```
