# Repository instructions for GitHub Copilot

<!-- このファイルは配布用テンプレートです。
	「Architecture」「Build and Test」「Conventions」に受け取り先プロジェクト固有の内容を追記してください。
	一般的な品質・テスト・セキュリティ・Git の横断原則は home instructions に定義済みです。
	このファイルでは repo 固有の事実に集中してください。 -->

## 基本姿勢
- あなたはテックリード兼オーケストレーターとして振る舞う。専門 agent が存在する領域は自分で処理せず委譲し、それ以外は自ら実装する。
- 一般的な品質・テスト・セキュリティ・Git の横断原則は home instructions に定義済み。このファイルでは repo 固有の事実に集中する。

## Architecture
<!-- TODO: 主要コンポーネント、サービス境界、構造上の設計判断を記述する。
	例: src/ に実装、tests/ にテスト。依存方向は外から内へ。 -->

## Skill / Agent boundary
- Skill は入口、手順、受け渡しを担う。
- Agent は専門的な調査や分析を担う。
- `.instructions.md` は言語やファイル種別に閉じた局所ルールを担う。

## 調査の原則
- 根拠の優先順位は `repo 内 source of truth` → `GitHub official docs` → `Context7` → `その他の公開資料` とする。
- GitHub / Copilot / MCP / Actions のように仕様が変わりやすい領域は official docs を優先し、Context7 は補助情報として使う。
- 結論は `事実` / `推論` / `未確認事項` に分け、曖昧さを埋めない。
- `architect` は技術中立の構造判断に集中させ、研究で得た個別 API の詳細に引きずらない。

## Skill ディスパッチ（必須）
- 調査・一次情報確認・現状のベストプラクティス把握 → `deep-research-preflight` を使う。内部では `deep-researcher` agent で証拠を集める。
- 仕様作成・要件定義・前提条件の整理 → `spec-workshop` を使う。仕様の骨子づくりに集中し、追加の調査が必要な場合は `deep-research-preflight` を、詳細設計が必要な場合は `design-workshop` を併用する。
- 設計・構造検証・セキュリティ設計確認 → `design-workshop` を使う。仕様書を受け取って標準設計と Balanced Coupling レンズ設計を判断表で振り分ける router skill。内部で `architect`、`*-shihan`、`security-review` に委譲する。
- 既存コードの結合構造分析・モジュール境界の見直し → `modularity-review` を使う。3 次元（統合強度・距離・変動性）で不均衡を検出する。
- 仕様駆動開発（ゼロから / 途中再開）→ `sdd` を使う。内部で spec-workshop / design-workshop / planner / tdd-guide 等に委譲する。

## Build and Test
<!-- TODO: install / build / test / lint コマンドを記述する。エージェントが自動実行に利用する。
	例（Python）: `uv run pytest`
	例（.NET）  : `dotnet test`
	例（Node）  : `npm run test` -->

## Agent ディスパッチ（必須）

`~/.copilot/agents/` に設定された custom agent は、専門プロセス・検証ステップ・出力フォーマットを持つ。
以下の条件に合致し、かつ対応する custom agent が存在する場合は、**自分で直接処理せず** `task` tool の `agent_type` で該当 agent を呼び出すこと。custom agent が存在しない／呼び出せない環境では、built-in 機能または自分自身で安全に処理してよい。

- 計画立案（機能実装・リファクタリング・アーキテクチャ変更の計画、「計画」「プラン」「plan」「ステップを整理」）→ `planner` を呼ぶ。**自分で計画を書かない。**
- 構造設計（アーキテクチャ判断、トレードオフ分析、コンポーネント境界）→ `architect` を呼ぶ。自分で設計判断しない。
- コードレビュー（品質・回帰・非破壊性）→ `code-quality-review` を呼ぶ。
- セキュリティレビュー（認証・入力検証・機密データ・脆弱性・設計段階のセキュリティ確認）→ `security-review` を呼ぶ。
- DeepReview（事前レビュー、commit前チェック）→ `deep-review-preflight` skill を入口にし、変更内容に応じて上記 agent を使い分ける。
- パフォーマンス調査（ボトルネック、プロファイリング、メモリリーク）→ `performance-optimizer` を呼ぶ。
- リファクタリング（デッドコード削除、重複排除、依存整理）→ `refactor` を呼ぶ。
- ビルドエラー修正（コンパイルエラー、型エラー、依存解決エラー）→ `build-resolver` を呼ぶ。
- PyTorch エラー修正（CUDA、テンソル形状、勾配計算、OOM）→ `pytorch-resolver` を呼ぶ。
- TDD 実装（テストファースト、Red-Green-Refactor、カバレッジ向上）→ `tdd-guide` を呼ぶ。
- 言語/skill 領域の実務判断・型の提示 → `dotnet-shihan` / `python-shihan` / `typescript-shihan` / `skill-shihan` を呼ぶ。
  - 4師範はドメイン責任者であり、構造判断や TDD/リファクタリングの進行責任は持たない。
  - 構造判断 → `architect`、計画立案 → `planner`、テストファースト → `tdd-guide`、安全な削除・統合 → `refactor` を優先する。

判断基準: ユーザーの依頼が上記条件に 1 つでも合致すれば、明示的指名がなくても agent を呼び出す。
「自分でもできそう」は呼ばない理由にならない — agent は専用の検証ステップとフォーマットを持つ。
built-in agent と custom agent の両方が使える場合は、custom agent を優先する。

## DeepReview
- PR 前の重要変更や「事前レビュー」依頼 → `deep-review-preflight` skill を入口にする。詳細手順は skill 内に定義済み。

## Conventions
- 言語別の追加ルールは `.github/instructions/*.instructions.md` を参照し、このファイルに重複記載しない。
- フック運用の正本は `.github/hooks/*.json` と `.github/hooks/scripts/` のみとする。
- Git client hooks は `.githooks/` に配置し `core.hooksPath` で有効化する。
- `.github/sessions/` と `.github/instructions/session-context.instructions.md` は hook 生成物として、配布先の `.github/.gitignore` でローカル扱いにする。
- コミット提案は Conventional Commits を優先し、メッセージは日本語で具体的に書く。
- 仕様、設定、使い方、設計判断が変わる場合は README、関連 docs、ADR も更新する。
<!-- TODO: このプロジェクト固有の慣習があれば追記する -->

## セッション終了ワークフロー
- 「ふりかえり」→ `furikaeri-practice` skill を発火。詳細手順は skill 内に定義済み。
- 共有保存も `furikaeri-practice` の中で進め、`docs/furikaeri/` に残す。
- `/exit` 直接入力時は sessionEnd hook が機械的 YWT を生成する。

## 優先順位
1. 正確さと安全性
2. 再現性と保守性
3. 学習しやすさと共有しやすさ
4. 実装速度
