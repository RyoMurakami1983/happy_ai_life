---
name: ask-happy
disable-model-invocation: true
description: >
  Happy AI Life の skill 選択に迷ったときの user-invoked router。
---

# Ask Happy

Ask Happy は、どの Happy AI Life skill を使うか迷ったときの入口です。
実作業は担当 skill へ渡し、この skill 自体には詳細手順を増やしません。

## 判断表

| したいこと | 使う skill |
| --- | --- |
| 要求、用語、既存 docs と照合したい | `grill-with-docs` |
| 実装前に構造判断と plan を作りたい | `design-and-plan` |
| 実装契約からローカル実装へ進めたい | `implement` |
| PR 前に事前レビューしたい | `deep-review-preflight` |
| skill / agent / instructions を作りたい | `copilot-authoring` |
| skill / prompt を評価したい | `skill-eval` |
| repo 固有語彙を整理したい | `domain-modeling` |
| session を引き継ぎたい | `session-handoff` |
| ふりかえりたい | `furikaeri` |
| Git commit を作りたい | `git-commit` |
| PR を作りたい | `gh-pr-create` |
| PR review に対応したい | `gh-pr-respond` |
| 作業中に見つけた別件を軽く Issue 化したい | `happy-add-issue` |
| ラベルや受け入れ条件まで含めて Issue を丁寧に作りたい | `gh-issue-create` |
| 初心者向けの README / 運用手順を書きたい | `beginner-readme-ops` |
| .NET 関連の skill を選びたい | `dotnet` |
| Tauri / TypeScript 環境を整えたい | `typescript-tauri-setup` |

## 使い方

1. ユーザーの目的を1文に圧縮する。
2. 判断表から最も近い skill を1つ選ぶ。
3. 選んだ理由と、次に読む source of truth を短く添えて handoff する。

## 注意点

- 複数 skill を同時に実行しない。まず入口を1つに絞る。
- 実装やレビューをこの skill 内で始めない。
- 判断表にない作業は `repo-onboarding` または `grill-with-docs` へ戻す。
