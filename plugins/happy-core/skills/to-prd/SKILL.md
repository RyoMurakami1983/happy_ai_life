---
name: to-prd
description: >
  こんなときに使う: 現在の会話内容をもとに、短く実用的な PRD を作りたいとき。追加のインタビューはせず、すでに分かっている内容だけから要約する。
---

## こんなときに使う

- 仕様を整理したい
- 実装前に、問題・解決策・受け入れ条件を固めたい
- そのまま issue / plan / design に渡せる形にしたい

## ルール

- 追加のインタビューはしない
- 既に会話に出ている内容だけで構成する
- 未確定の点は「未確定」として明示する
- 文章は短く、実装に直結する形にする

## ワークフロー

### Step 1 — 会話内容を要約する

- 既に出ている要件、制約、受け入れ条件を箇条書きにする
- 重要な背景や未確定点を残す

### Step 2 — PRD の骨組みを埋める

- Problem Statement、Solution、User Stories、Acceptance Criteria、Out of Scope、Notes を埋める
- 実装に直結する短い文章に整える

### Step 3 — そのまま次工程へ渡す

- issue / plan / design へ受け渡せる形で残す
- 未確定の点は「未確定」として明示する

## 生成テンプレート

### Problem Statement

ユーザーが直面している問題を、ユーザー視点で 1-2 文で書く。

### Solution

その問題に対する解決策を、ユーザー視点で 1-2 文で書く。

### User Stories

1. As a <actor>, I want a <feature>, so that <benefit>

### Acceptance Criteria

- 受け入れ条件を箇条書きで書く
- 実装の観点で曖昧さがないようにする

### Out of Scope

- 今回の PRD では扱わないものを箇条書きで書く

### Notes

- 追加で残すべき前提、制約、未確定事項を箇条書きで書く
