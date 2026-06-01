---
name: compact-context
description: >
  Agent作業前に cheap signals から最小スコープを切り、Context Pack を作る文脈圧縮プロトコル。
  対象は code / docs / skills。
  Use when: compact context, context pack, 文脈圧縮, コンテキスト圧縮, 読む範囲を絞る, low-cost investigation.
license: MIT
---

# Compact Context

Agentが作業に入る前に、読む範囲を最小化し、必要な文脈だけを `Context Pack` に圧縮する。

## Mission

全文読解・全repo探索・不要な質問を避ける。
cheap signals から対象を絞り、最大5 artifactsで作業前文脈を固定する。

## Applies To

コード専用ではない。次のいずれも対象にする。

- code: ソース、設定、テスト
- docs: 文書、PDF束、議事録、Wiki
- skills: SKILL.md、prompt、protocol定義

非コード対象では、cheap signals を git/tree から README・索引・ファイル名・日付・frontmatter に読み替える。

## Hard Rules

1. Do not read full files first.
2. Start with cheap signals.
3. Limit initial scope to 5 artifacts.
4. Rank and cut overflow candidates.
5. Justify every file or slice you read.
6. Do not ask what available artifacts can answer.
7. Stop after emitting the Context Pack.

## Protocol

1. Pin the task in one line.
2. Inspect cheap signals.
3. Narrow scope to the smallest useful set.
4. Read only justified files.
5. Emit the Context Pack and stop.

## Cheap Signals

安い情報から高い情報へ進む。順序は固定する。

1. task: ユーザー依頼、現在の目的、明示された制約
2. diff: `git status`, `git diff --stat`, 必要時だけ対象fileのdiff
3. tree: `tree -L 3`, `find . -maxdepth 3`, `Get-ChildItem -Depth 3`
4. metadata: README, package metadata, config names, skill frontmatter
5. search: `rg`, fallback to `grep` or `Select-String`

docs / skills 対象では 2〜3 を「索引・ファイル名・日付・配置・既存index・周辺README」に置き換える。

Prefer:
~~~ text
git status

git diff --stat

rg "keyword" .
~~~

PowerShell fallback:
~~~ text
git status

git diff --stat

Select-String -Path .* -Pattern "keyword" -Recurse
~~~

## Scope Limit

初期対象は最大5 artifacts。5件を超えたら順位付けで5件に切る。

順位付け基準:

1. Task近接度
2. Diff有無
3. Import / 参照中心性
4. Test / Config近接度
5. 最近触った形跡

## Reading Rules

Read slices, not whole files, when files are large.

Relevant slices are limited to:

1. diff hunk周辺
2. errorが指す行・関数
3. search hit周辺
4. public API / entry point周辺

Default window: 前後40行。
近い関数・class境界があれば、そこまで広げてよい。
巨大な関数・class全体を無条件に読まない。

## Exclusions

標準除外:

- `node_modules/`, `vendor/`
- `.venv/`, `venv/`, `__pycache__/`
- `dist/`, `build/`, `out/`, `target/`, `.next/`
- generated files
- `*.log`, `coverage/`, `reports/`
- binary / media / models / datasets

lock file は通常読まない。依存問題・install failure・バージョン差分の時だけ読む。
大容量assetは中身を読まず、メタ情報のみを見る。
PDF / 文書束は索引優先。本文の前に、ファイル名・日付・番号・配置・既存index・周辺READMEを見る。

## Context Pack Format

Use English headings and Japanese body.
全体を80行以内に収める。セクション別の上限を守る。

~~~ text
全体: 80行以内
Task: 1行
Scope: 3行以内
Relevant Artifacts: 5行以内
Key Contracts: 5行以内
Constraints: 5行以内
Excluded: 5行以内
Open Questions: 3行以内
Next Actions: 3行以内
~~~

## Task

- 1行で目的を書く

## Scope

- dir: `対象directory`
- feature: 対象機能・文書・skill
- checked: `command/target` — 確認済みcheap signalsの要約

## Relevant Artifacts

- `path` — 読む理由を1行で書く

## Key Contracts

- API、entry point、主要関数、skill rule、文書契約を書く

## Constraints

- 作業制約、安全制約、変更禁止事項を書く

## Excluded

- 読まない範囲を書く
- 標準除外＋task別除外を書く

## Open Questions

- 探索では解けない設計判断だけを書く
- 最大3件

## Next Actions

1. 次にやること
2. 必要なら検証コマンド候補を最大1件
3. 必要なら次skill

## Minimal Example
## Task

- `compact-context` skillを作るための作業前文脈を固定する。

## Scope

- dir: `plugins/happy-core/skills/compact-context`
- feature: Agent作業前の文脈圧縮protocol
- checked: `tree/find`, `low-cost-mode`, `session-handoff` — 既存skill構造と責務境界を確認

## Relevant Artifacts

- `plugins/happy-core/skills/low-cost-mode/SKILL.md` — 出力token削減の既存skill
- `plugins/happy-core/skills/session-handoff/SKILL.md` — 次AIへの圧縮引き継ぎ
- `plugins/happy-core/skills/compact-context/SKILL.md` — 新規作成対象

## Key Contracts

- `compact-context`: 作業前にContext Packを出して停止する。
- `low-cost-mode`: Context Pack出力を短く保つ原則として参照する。
- `session-handoff`: 中断・別AIへ渡す時だけ使う。

## Constraints

- 既存 `low-cost-mode` に統合しない。
- Context Packは80行以内。
- 初期scopeは最大5 artifacts。

## Excluded

- repo全体探索
- full README読み
- generated files / dependencies / logs
- 実装作業

## Open Questions

- なし。

## Next Actions

1. `SKILL.md` draftをレビューする。
2. 必要なら `references/origin.md` を追加する。

## Acceptance Criteria

1. Context Pack is within 80 lines.
2. Initial scope is limited to 5 artifacts.
3. Every read file or slice is justified.
4. Applies-to target (code / docs / skills) is identified.
5. Standard exclusions and Open Questions are present.
6. The agent stops after emitting the Context Pack.

## Anti-patterns

- リポジトリ全体を読む。
- READMEや設定を全文で読み始める。
- 候補artifactを絞らずに列挙する。
- 検索で解けることをユーザーに質問する。
- Context Pack後にそのまま実装へ進む。

## Related Skills

- `low-cost-mode` — Context Packの出力を短く正確に保つ。
- `session-handoff` — 中断時や別AIへ渡す時に使う。
- `knowledge-capture` — 再利用可能な知見へ抽象化する時に使う。