# Skill の単一責務と薄い orchestration

**日付**: 2026-08-14
**ステータス**: 承認

---

## 背景

skill は再利用しやすい一方で、入口に責務を詰め込み始めると、起動条件、境界、改善先がすぐ曖昧になる。

とくに authoring 系では、`作成`、`改善`、`静的検証`、`実動評価` を 1 本の skill に積み増すと、
「今どの目的で開いた skill なのか」が見えにくくなり、後続の specialized skill との重複も起きやすい。

既存の `interview-with-docs` は、`interview-me` と `domain-modeling` を 1 会話でつなぎつつ、
親自身は薄い orchestration に徹することで、入口の分かりやすさと責務分離を両立している。

## 判断

- **1 skill = 1 primary purpose** を、公開 skill authoring の基本方針とする
- 複数の専門機能を 1 つの skill に直列で詰め込まず、まず sibling skill へ分解する
- それでも 1 入口が必要な場合だけ、`interview-with-docs` 型の **薄い orchestration skill** を置く
- orchestration 親は `disable-model-invocation: true` を既定とし、`役割の境界` と `実行ルール` に徹する
- 親は route / handoff だけを持ち、詳細な workflow、checklist、例外処理は child skill または `references/` へ置く
- `copilot-authoring` は今後、authoring 全体を抱え込む skill ではなく、`new-skill` / `instructions-authoring` / `improve-existing` / `validate-authoring` / `skill-eval` へつなぐ薄い入口として扱う
- `new-agent` は標準 authoring route から外す。custom agent 作成が必要に見える場合も、まず既存 skill では足りない理由を issue / design 判断へ戻す。
- 命名刷新では、plugin slug は維持し、top-level / evaluation / safety / entrypoint skill は説明的なまま保護する。短縮は文脈で一意な child / leaf skill に限る。
- `disable-model-invocation: true` は orchestration 意図を示す印であり、Copilot CLI の可視性制御や manual-only 保証としては依存しない。

## 根拠

- **起動精度**: primary purpose が 1 つに絞られた skill の方が trigger を短く保ちやすい
- **保守性**: 改善対象が 1 つに定まるため、docs と reference の同期がしやすい
- **学習容易性**: 利用者は「どの skill が何を担当するか」を覚えやすくなる
- **拡張性**: 実動評価や構造検証のような後段工程を、親 skill を肥大化させずに追加できる

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| 1 本の大きい skill にまとめる | 入口は少ない | trigger が広がり、責務境界と改善先が曖昧になる |
| すべてを独立 skill にして親を置かない | 責務は明確 | 会話中の handoff が見えにくく、入口が散らばる |
| **単一責務 skill + 薄い orchestration** | 入口の分かりやすさと責務分離を両立できる | parent / child の関係を明示的に保守する必要がある |

## 運用

- 新しい skill を作るときは、まず「これは 1 つの primary purpose に還元できるか」を確認する
- `作成 + 改善 + 検証 + 評価` のような複合要求が出ても、親に全部を書かず、順序だけを orchestration に残す
- orchestration 親を作るときは、`disable-model-invocation: true`、`役割の境界`、`実行ルール`、必要最小限の fallback だけを置く
- `copilot-authoring` のような入口 skill を改善するときは、「親へ詳細手順を戻していないか」を review で確認する
- agent 作成は公開 child route にしない。必要性が出た場合は、個別の設計判断として扱う
- 命名変更は「初見ユーザーが役割を推測できるか」を gate とし、短さだけを理由に省略しない
