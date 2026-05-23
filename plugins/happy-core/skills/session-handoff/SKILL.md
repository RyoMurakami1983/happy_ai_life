---
name: session-handoff
description: >
  現在の会話と作業状態を、次の AI が再開できる短い引き継ぎ文書に圧縮する。
  Use when: セッションをまたいで別の AI に作業を引き継ぎたいとき、handoff, 引き継ぎ, 次回再開メモを作りたいとき。
license: MIT-derived
---

# Session Handoff

この skill は、Matt Pocock さんの `handoff` を出発点に、GitHub Copilot CLI、日本語での対話、Happy AI Life の「再現性」「学習資産」「低燃費」へ合わせて再設計したものです。
`furikaeri` が人間向けの作業報告・KPT・Issue 発掘に寄るのに対し、`session-handoff` は **次の AI が迷わず続きを始めるための圧縮引き継ぎ**に絞ります。

## こんなときに使う

- セッションをまたいで、次の AI に作業を続けてもらいたいとき
- context が長くなり、要点だけを別セッションへ渡したいとき
- PR / commit / Issue / plan / ADR など既存 artifact を参照しながら、重複しない再開メモを作りたいとき
- 「引き継ぎ」「handoff」「次回再開メモ」とユーザーが求めたとき

## 判断表

| 状況 | 使うもの |
| --- | --- |
| 次の AI に作業を再開させたい | `session-handoff` |
| 人間向けに日次レビュー、KPT、改善 Issue 候補を残したい | `furikaeri` |
| 公開されうる文書へ経験を抽象化したい | `knowledge-capture` |
| すぐ着手できる後続タスクを GitHub Issue にしたい | `gh-issue-create` |

## ワークフロー: AI 向け引き継ぎを作る

### Step 1 — 次回の焦点を固定する

次のセッションで何を再開するのかを 1 文で固定します。ユーザーが焦点を指定している場合は、それに合わせます。

### Step 2 — 既存 artifact を参照する

既に残っているものは本文に重複させず、path / URL / commit / Issue / PR 番号で参照します。

- commit / branch
- PR / Issue
- 変更済み file path
- docs / ADR / design / implementation handoff
- validation 結果

### Step 3 — secret と固有情報を落とす

API key、password、個人情報、private repo 固有の秘密、公開できない顧客情報は書きません。
公開可能性がある場合は `knowledge-capture` の匿名化観点を使います。

### Step 4 — 次の AI が必要な順で圧縮する

出力は短く、次の AI が最初に読む順で並べます。

```markdown
# Session Handoff: [短いタイトル]

## Goal
- 次回の焦点:

## Current State
- branch:
- commits / PR / Issue:
- validation:

## Important Context
- 決定済み:
- 制約:
- 注意:

## Changed / Relevant Files
- `path` — 何のために重要か

## Next Actions
1. ...
2. ...

## Suggested Skills
- `skill-name` — 使う理由
```

## 保存先

既定は repository に追跡されない session workspace または OS の temporary directory です。ユーザーが明示した場合だけ repo 内に保存します。

## 関連リソース

- `references/origin.md` — 出典、適用範囲、MIT license notice
- `furikaeri` — 人間向けの日次レビュー、KPT、Issue 発掘
- `knowledge-capture` — 公開されうる知識の匿名化
- `gh-issue-create` — handoff ではなく追跡タスクにすべきものを Issue 化

## 注意点

- 既存 artifact の中身を丸ごとコピーしない。参照で済むものは参照する。
- AI 向けなので、感想や学びより「再開に必要な事実」を優先する。
- repo 内に handoff markdown を勝手に作らない。必要なら session workspace を使う。
