---
name: session-share-document
description: >
  セッション記録を共有用の docs/sessions/ 文書に整形して保存する。Use when:
  セッションを共有したいとき、ふりかえり後に公開用の要約を作りたいとき、docs/sessions に履歴を残したいとき。
compatibility: GitHub Copilot Agent, Claude Code, Codex
---

# session-share-document

`.github/sessions/` にある作業用セッションを、タイトル確認と公開配慮を通して `docs/sessions/` に保存する共有ワークフローです。  
`furikaeri-practice` の成果を「読まれる文書」に変えるときに使います。
対話でタイトルと要約を固めてから保存するので、あとから直しづらい公開用の事故を減らせます。
なぜなら、共有文書は公開前にタイトル確認と匿名化を済ませないと、内部情報をそのまま残しやすいからです。

## こんなときに使う

- セッションの内容を共有用の文書にしたいとき
- ふりかえりの結果を履歴として残したいとき
- `docs/sessions/` に最新の共有版を作りたいとき

## 関連スキル

- **`furikaeri-practice`** — ふりかえりから共有へつなぐ入口
- **`knowledge-capture`** — 公開前の匿名化観点

## ワークフロー: 共有文書の作成

### ステップ 1 — 対象セッションを選ぶ

既定では最新の `.github/sessions/*-session.md` を対象にします。`docs/sessions/` の共有文書は append-only にして、既存版を上書きせず新しい `YYYYMMDD-HHmmss_(Session名).md` を追加します。

### ステップ 2 — タイトル候補を出して確認する

共有文書のファイル名と見出しに使うセッションタイトルを、まず候補として提示します。  
そのあとで、必ずユーザーに最終タイトルを確認してください。

### ステップ 3 — Executive Summary と公開用本文を作る

セッション全体を 2〜4 文の Executive Summary に圧縮し、公開可能な表現に整えます。  
必要なら `knowledge-capture` の匿名化観点（AC-1〜AC-4）を使って、固有名詞や内部情報を置き換えます。

### ステップ 4 — `docs/sessions/` に保存する

保存先は `docs/sessions/YYYYMMDD-HHmmss_(Session名).md` です。  
ファイル名の禁止文字は置換し、長すぎるタイトルは読みやすさを優先して短くしてください。
既存の共有文書は更新せず、新しい共有文書を追加してください。`pre-commit` hook が既存ファイルの変更・削除・rename を拒否します。

### ステップ 5 — 次の導線を残す

`furikaeri-practice` の後続として案内しやすいように、必要なら次回のセッション向けメモも短く残します。

## 注意点

- **hook からの自動起動はしない**: `sessionEnd` から skill を直接呼び出す前提ではありません。
- **作業用と共有用を混ぜない**: `.github/sessions/` は作業領域、`docs/sessions/` は共有領域です。
- **公開配慮を省かない**: 共有文書は外部に読まれる前提で書きます。

## 早見表

| やりたいこと | 次の動き |
| --- | --- |
| 直近のセッションを共有したい | 最新の `.github/sessions/` を読む |
| 共有文書の名前を決めたい | タイトル候補を出してユーザー確認する |
| 公開用の本文を整えたい | Executive Summary と匿名化を入れる |
| 保存したい | `docs/sessions/YYYYMMDD-HHmmss_(Session名).md` に書く |
