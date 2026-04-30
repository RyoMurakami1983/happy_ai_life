---
name: sdd
description: >
  仕様駆動開発の前半工程（spec → design → plan handoff）を1つの入口で進める。
  途中の spec / design / planning フェーズからも再開できる。
  複数リポが関連する場合は split_multi_repo_plan で unified architecture を分割し、
  各リポの plan.md を生成します。
  Use when: 仕様駆動で開発を始めたいとき、途中のフェーズから再開したいとき、multirepository 環境で計画を分割したいとき。
---

# SDD — Spec-Driven Development

仕様駆動開発の前半工程（spec → design → plan）を1つの入口から進める router skill です。各フェーズの中身は既存の skill に委譲し、この skill 自身はフローの振り分けと接続だけを担います。plan が完成したら `impl-and-ship` へ引き継ぎます。途中からの再開にも対応し、最も進んだ地点の次から始められます。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

このスキルは次のようなときに使います:
- ゼロから仕様駆動で開発を始めたいとき
- 仕様はあるが設計から進めたいとき
- 設計済みで計画フェーズに入りたいとき
- 中断した spec / design / planning を途中から再開したいとき

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| ゼロから仕様駆動で開発したい | `sub_skills/from-scratch/` | spec-workshop → design-workshop → PLAN mode → impl-and-ship へ handoff |
| 仕様があり設計から始めたい | `sub_skills/from-spec/` | design-workshop → PLAN mode → impl-and-ship へ handoff |
| 設計があり計画から始めたい | `sub_skills/from-design/` | PLAN mode → impl-and-ship へ handoff |
| 計画があり実装から始めたい | `impl-and-ship` を直接使う | bootstrap 確認 → contract checkpoint → 実装 slice → eval gate → review → PR |
| 中断した開発を再開したい | `sub_skills/resume/` | 成果物の状態から中断地点を判定し、該当フェーズから再開 |

## 全体フロー

```
仕様フェーズ        → spec-workshop（対話 + 調査）
  ↓
設計フェーズ        → design-workshop（router: standard / balanced-coupling-design）
  ↓                    standard: 構造判断 + 自己レビュー
  ↓                    balanced-coupling-design: サブドメイン分類 + 3次元結合評価
  ↓                    DDD 戦略パターン（Bounded Context, Context Map）は
  ↓                    design-workshop が構造判断として扱う
  ↓
計画フェーズ        → PLAN mode
  ↓
  ↓                 ＊ multirepository 時（以下オプション）＊
  ↓                 → split_multi_repo_plan（unified architecture → per-repo plans）
  ↓
                    ＊ここで sdd の責務は終わり ＊
                    → impl-and-ship（実装・eval・review・furikaeri・PR の後半サイクル）
```

## PLAN mode について

**PLAN mode** は、design-workshop の完了後に **実装計画を整理・確認する段階** です。以下のいずれかの方法で実行します：

### PLAN mode の起動方法

1. **built-in PLAN mode 機能を使う場合**:
   - Copilot CLI でセッション中に PLAN mode（Shift+Tab で切り替え）に入る
   - 計画の構造化、リスク整理、フェーズ分割を対話的に進める
   - plan.md が session-state フォルダに自動生成される

2. **plan artifact-driven の場合**:
   - 既に存在する plan.md が以下の必須セクションを満たしていれば、from-design をスキップして `impl-and-ship` へ直接進める
   - PLAN mode の新規実行は不要

### 必須 handoff セクション（plan.md に含める）

PLAN mode 完了または既存 plan.md が以下を満たす状態で、`impl-and-ship` へ handoff します：

```markdown
# Implementation Plan

## Project Context
- Related Repositories（単一 repo 場合は省略可）
- Trust Boundaries（設計で確認したもの）
- Key Constraints

## Phase Breakdown
- Phase 1: 〇〇（条件: 〇〇完了）
- Phase 2: 〇〇（条件: Phase 1 完了）

## Acceptance Criteria & Test Strategy
- User story 1: 〇〇テスト
- User story 2: 〇〇テスト

## Risks & Mitigations
- Risk 1: 対策〇〇
- Risk 2: 対策〇〇
```

### PLAN mode スキップ条件

以下の場合、PLAN mode をスキップして `impl-and-ship` へ直接進められます：
- plan.md が既に「Project Context」「Phase Breakdown」「Acceptance Criteria」「Risks」セクションを満たしている
- ただし、multirepository 環境の場合はリポ間依存が明記されていること

### multirepository 時の PLAN mode

複数リポが関連する場合は、PLAN mode で必ず以下を明記してください（後述）。

## For Multi-Repo Project（マルチリポジトリ対応）

複数リポが関連する開発では、PLAN mode で unified architecture を完成させた後、`split_multi_repo_plan` sub-skill を使い、リポごとの独立した plan.md を生成します。

### split_multi_repo_plan の役割

- **入力**: PLAN mode または design-workshop の unified architecture
  - リポ一覧（name, modules）
  - リポ間の provide/require artifacts（コンポーネント間の依存関係）
- **処理**: DAG 構築 → サイクル検出 → contract 検証 → per-repo plan.md 生成
- **出力**: 各リポの plan.md
  - リポの project context（依存リポ、提供 artifact）
  - 当該リポ内の phase breakdown
  - 実装順序の明示

### split_multi_repo_plan を使うとき

- リポ数が 2 つ以上
- リポ間に明確な依存関係（provide/require）がある
- 各リポの実装フェーズを並列または順序付きで管理したい場合

### split_multi_repo_plan の後

各リポの plan.md が生成されたら、各リポに対して `impl-and-ship` を起動し、並列実装を開始します（dependencies の順序に従う）。

## セキュリティ checkpoint（設計時）

設計フェーズでは design-workshop 内で trust boundary と設計方針を確認します。実装中のセキュリティ checkpoint は `impl-and-ship` が担います。

## 共通リソース

- `plugins/happy-coding/skills/spec-workshop/SKILL.md` — 仕様作成
- `plugins/happy-coding/skills/design-workshop/SKILL.md` — 技術設計（router: standard / balanced-coupling-design）
- `plugins/happy-coding/skills/modularity-review/SKILL.md` — 既存コードの結合構造分析
- `plugins/happy-coding/skills/impl-and-ship/SKILL.md` — 実装・eval・review・PR の後半サイクル
- `references/interactive-app-bootstrap-checklist.md` — interactive app pilot の実装前前提
- `references/interactive-app-comparable-harness-contract.md` — interactive app pilot の比較前提

## ルーティングメモ

- ユーザーの現在地点に最も合う sub-skill へ直接案内する。
- 実行ロジックは router ではなく sub-skill と既存 skill に置く。
- 各フェーズの中身を sdd 内に再実装しない。委譲先の skill や PLAN mode が正本。
- 計画の正本は PLAN mode の出力または明示的な plan artifact に置く。
- sdd 自体はモデル選定を持たず、入口と接続だけを担う。
- plan handoff が完成したら、実装の入口は `impl-and-ship` に委譲する。

## multirepository 環境での handoff

複数リポが関連する場合、plan handoff は以下の形式で作成してください：

### Handoff フォーマット

**メタデータ** （plan.md の冒頭に記載）:
```markdown
# Implementation Plan

## Project Context
- **Multirepository Structure**: Yes
- **Related Repositories**: 
  - Frontend (TypeScript/React) → `frontend/`
  - Backend (Python/FastAPI) → `backend/`
  - Mobile (Dart/Flutter) → `mobile/`

## Dependency Order
1. Backend API (core interface)
2. Frontend & Mobile (in parallel)
```

### 各フェーズでの処理

- **複数リポ構成の確認**: from-scratch ステップ 0.5 または from-spec ステップ 0 で multirepository 判定が行われ、関連リポを列挙します
- **設計フェーズでの分割**: design-workshop で balanced-coupling-design ルート（context map + bounded context 分類）を選択し、リポごとに分割された設計書を作成します。各リポの設計書に「この bounded context が他のリポのどの context に依存するか」を記述
- **PLAN mode への受け渡し**: 
  - **オプション A（分割 plan）**: 各リポに対応する独立した plan artifact を作成（`plan-backend.md`, `plan-frontend.md`, `plan-mobile.md`）し、各 plan に `## Dependency Order` セクションで実装順序を指定
    - **推奨対象**: 3 リポ以上の規模 / リポの進捗管理が独立している場合
  - **オプション B（統合 plan）**: 統合 plan 上で「## リポ別実装フェーズ」セクションを作成し、各リポの実装タスクと依存関係を一元管理
    - **推奨対象**: 小規模（2 リポ）/ リポ間依存が密結合 / 全体を 1 つの計画で管理したい場合

### impl-and-ship への引き継ぎ

`impl-and-ship` は以下の情報を受け取ります：
- Multirepository フラグ（構造識別）
- 各リポの plan artifact または統合 plan
- リポ間の依存関係と並列実装可能な箇所

`impl-and-ship` がリポごとの bootstrap 確認、contract checkpoint、実装、eval gate を並列・順序付きで実行します。

## 注意点

- **各段の中身を再実装しない**: sdd はフローを繋ぐだけです。仕様は spec-workshop、設計は design-workshop、計画は PLAN mode または plan artifact が正本です。
- **実装フェーズは sdd に持ち込まない**: plan handoff 完了後は `impl-and-ship` が正本です。
- **全フェーズを必ず通す必要はない**: 途中から始めてよいし、特定フェーズを飛ばす判断もユーザーに委ねます。
