---
name: standard
description: >
  単一 repo または通常の機能追加で、要求を構造判断、behavior list、vertical slices、implementation handoff に変える標準設計ワークフロー。
  Use when: 既存 stack で実装できる仕様を、TDD 可能な slice と plan artifact に整理したいとき。
---

# Standard Design Workflow

`interview-with-docs` で固まった要求を、`implement` が TDD で進められる形へ圧縮します。
既存 repo の通常変更では、このルートを既定にします。

## こんなときに使う

- 単一 repo の通常機能追加を設計したいとき
- 既存 stack のまま実装可能な slice に分けたいとき
- behavior list と public interface を整理したいとき
- HITL / AFK と first test 観点を handoff したいとき

## ワークフロー: standard design を implementation handoff に変える

### ステップ 1 — 入力を確認する

読むもの:

- grill result、仕様、issue、会話で合意した要求
- 関連 docs / ADR / `CONTEXT.md`
- 変更対象の既存コードと test
- repo instructions

固定するもの:

- ゴール
- 成功条件
- 対象外
- 確認 command
- blocking unknown の有無

blocking unknown が残る場合は `interview-with-docs` に戻します。

### ステップ 2 — 構造判断をする

実装に必要な構造だけを決めます。

- どの module / component が責務を持つか
- 既存 interface を使うか、新しい public interface が必要か
- 状態、データフロー、外部入力がどこを通るか
- 触らない境界はどこか
- 追加する抽象化は本当に必要か

判断 lens:

- public interface を test surface にできるか
- module は浅い便利関数ではなく、内部複雑性を隠せているか
- 変更が局所化されるか
- 消す・置き換える時の範囲が見えるか

大きな技術選定が必要な場合だけ `_foundation/TECH_SELECTION_HARNESS.md` を読みます。既存 stack で自然に実装できる場合は技術選定 checkpoint を省略します。

### ステップ 3 — behavior list を作る

受け入れ条件を、観測可能な振る舞いに変換します。

各 behavior に含めるもの:

- user-visible behavior または外から観測できる contract
- public interface
- 正常系
- 重要な境界値 / 失敗系
- security boundary が関係する場合の入力検証観点

private method や内部 collaborator の呼び出し回数を仕様化しません。

### ステップ 4 — vertical slices に切る

1 slice は 1 ユーザー行動、または 1 acceptance condition を主語にします。
最初の slice は tracer bullet として、必要な層を薄く縦断します。

各 slice に含めるもの:

- slice 名
- HITL / AFK
- done 条件
- 最初に書く test 観点
- `RED` の期待失敗理由
- `GREEN` / acceptance command
- 対象外

horizontal slice（DB だけ、UI だけ、テストだけ）は避けます。

### ステップ 5 — security と実装適合を確認する

次に該当する場合は、設計内で扱います。

- 認証 / 認可
- 外部入力
- 機密データ
- 外部 API / Webhook
- ファイル I/O
- コマンド実行
- trust boundary をまたぐデータフロー

設計が対象技術で自然に実装できない場合は、構造判断へ戻して小さく直します。

### ステップ 6 — implementation handoff を作る

`docs/design/NNN_TECHNICAL_DESIGN.md` が必要なら保存します。
実装進行の checklist が必要な場合だけ `docs/plan/NNN_PLAN.md` を作ります。
ユーザーが設計書 / 計画書を repo に残すよう明示した場合は、保存を省略しません。
handoff には必ず `artifacts:` フィールドを入れます。`artifacts: conversation-only` とするか、保存した path を `### Artifacts` 配下に列挙します。

handoff の最小形:

```markdown
## Implementation Handoff

### Goal

### Success Criteria

### Out of Scope

### Structure Decisions

### Behavior List

### Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|

### Artifacts

artifacts: conversation-only

または:

artifacts:
  - docs/design/NNN_TECHNICAL_DESIGN.md
  - docs/plan/NNN_PLAN.md

### Risks / Unknowns

### Return Conditions
```

## 注意点

- 実装を始めない。handoff ができたら `implement` に渡す。
- 仕様の穴を設計判断で埋めない。
- 技術選定や詳細テスト仕様を毎回作らない。
- plan は人間向け進捗補助であり、実装契約の本体は handoff と slice contract。

## 関連リソース

- `plugins/happy-coding/skills/interview-with-docs/SKILL.md`
- `plugins/happy-coding/skills/implement/SKILL.md`
- `plugins/happy-coding/skills/design-and-plan/references/WORK_ARTIFACTS.md`
- `plugins/happy-coding/skills/design-and-plan/assets/NNN_PLAN_TEMPLATE.md`
