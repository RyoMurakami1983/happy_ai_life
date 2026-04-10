---
name: session-share-document
description: >
  セッション記録を共有用の docs/sessions/ 文書に整形して保存する。Use when:
  セッションを共有したいとき、ふりかえり後に公開用の要約を作りたいとき、docs/sessions に履歴を残したいとき。
compatibility: GitHub Copilot Agent, Claude Code, Codex
---

# session-share-document

`.github/sessions/` の作業記録を、公開配慮とタイトル確認を通して `docs/sessions/` の共有文書に変える router skill です。
`furikaeri-practice` の出力をそのまま使わず、読まれる文書として整える入口にします。

## こんなときに使う

- セッションの内容を共有用の文書にしたいとき
- ふりかえりの結果を履歴として残したいとき
- `docs/sessions/` に最新の共有版を追加したいとき

## 選び方

| 状況 | 使うもの | 目的 |
| --- | --- | --- |
| 共有版を作る | session-share-document | 公開用の文書に整える |
| ふりかえりから繋ぐ | furikaeri-practice | YWT / KPT を作る |

## ワークフロー

### Step 1 — 対象セッションを選ぶ

既定では最新の `.github/sessions/*-session.md` を対象にします。

### Step 2 — タイトル候補を確認する

共有文書のタイトルと見出し候補を提示し、最終決定を確認します。

### Step 3 — 公開用本文に整える

Executive Summary を先頭に置き、必要なら匿名化して読みやすくします。

### Step 4 — `docs/sessions/` に保存する

新しい共有文書として追加し、既存の共有文書は上書きしません。

### Step 5 — 次の導線を残す

必要なら次回向けメモを短く残し、`furikaeri-practice` とつなぎます。

## 共通リソース

- `references/naming.md`
- `references/output-shape.md`
- `../furikaeri-practice/`
- `../knowledge-capture/`

## 注意点

- hook から自動起動しない
- 作業用と共有用を混ぜない
- 公開配慮を省かない
- 共有 docs commit は実装 commit と分ける
