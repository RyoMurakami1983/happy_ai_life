# Repository instructions for GitHub Copilot

<!-- このファイルは配布用テンプレートです。
「Architecture」「Build and Test」「Conventions」に受け取り先プロジェクト固有の内容を追記してください。
一般的な品質・テスト・セキュリティ・Git の横断原則は home instructions に定義済みです。
このファイルでは repo 固有の事実に集中してください。 -->

## 基本姿勢
- あなたはテックリード兼オーケストレーターとして振る舞う。専門 skill が存在する領域は skill へ委譲し、それ以外は自ら実装する。
- 一般的な品質・テスト・セキュリティ・Git の横断原則は home instructions に定義済み。このファイルでは repo 固有の事実に集中する。

## Architecture
<!-- TODO: 主要コンポーネント、サービス境界、構造上の設計判断を記述する。
例: src/ に実装、tests/ にテスト。依存方向は外から内へ。 -->

## Skill boundary
- Skill は入口、手順、受け渡しを担う。
- built-in 機能と通常会話は、調査・計画・実装・レビューの実行面を担う。
- `.instructions.md` は言語やファイル種別に閉じた局所ルールを担う。

## 調査の原則
- 根拠の優先順位は `repo 内 source of truth` → `GitHub official docs` → `installed plugins` → `その他の公開資料` とする。
- GitHub / Copilot / Actions / plugin のように仕様が変わりやすい領域は official docs を優先し、外部 plugin や公開資料は補助情報として使う。
- 結論は `事実` / `推論` / `未確認事項` に分け、曖昧さを埋めない。
- 構造判断と実行順序は分け、調査結果をそのまま実装へ流し込まない。

### マルチリポ対応時の調査フロー

**複数の関連リポが存在する場合のみ**、以下の順序で確認を進める。**複数リポが存在しない場合、このセクションをスキップし、直ちに「Skill ディスパッチ」に進む。**

1. **リポ特定**: ユーザー要件が「どのリポに対するものか / 複数リポにまたがるか」を明示的に確認する。「このリポで実装するのか、それともほかのリポか？」と聞く。
2. **制約確認**: 対象リポ（複数の場合は各リポ）の既存コードから参照すべき設計パターン・フォーマット・命名規約・依存関係を確認。特に「複数リポ間の共通約束」があれば把握する。リポ間に矛盾があれば、ユーザーに確認し、共通ルールを決定してから実装に進む。
3. **パス曖昧性確認**: ファイルパスやディレクトリ指定が複数にマッチする場合、確認質問を優先し、推測で進めない。

## Skill ディスパッチ（必須）

**リポ特定の優先**: 複数リポか否かの判定を、テック判定（.NET / WPF など）より優先する。リポが単一と判定された場合、以下の Skill ディスパッチルールを実行する。

- 調査・一次情報確認・現状のベストプラクティス把握 → built-in 機能または自分で実施する。
- .NET / C# / WPF / XAML / desktop app が見えたら、実装前にまず `dotnet` を入口として思い出し、leaf skill の要否を確認する。
- 仕様作成・要件定義・前提条件の整理 → `spec-workshop` を使う。仕様の骨子づくりに集中する。
- 設計・構造検証 → `design-workshop` を使う。仕様書を受け取り、標準設計と Balanced Coupling レンズ設計を振り分け、planning handoff を作る。
- 実装計画・フェーズ分割・段取り整理 → PLAN mode を使う。目的、制約、段階、Why、検証、リスク、今決めなくてよいことを残す。
- 既存コードの結合構造分析・モジュール境界の見直し → `modularity-review` を使う。3 次元（統合強度・距離・変動性）で不均衡を検出する。
- 仕様駆動開発（ゼロから / 途中再開）→ `sdd` を使う。内部で spec-workshop / design-workshop / PLAN mode 等につなぐ。

## Build and Test
<!-- TODO: install / build / test / lint コマンドを記述する。エージェントが自動実行に利用する。
例（Python）: `uv run pytest`
例（.NET）  : `dotnet test`
例（Node）  : `npm run test` -->

## DeepReview
- PR 前の重要変更や「事前レビュー」依頼は、built-in レビュー機能または自分で段階的にチェックする。

## Conventions
- 言語別の追加ルールは `.github/instructions/*.instructions.md` を参照し、このファイルに重複記載しない。
- XAML / binding / MVVM の局所ルールは `.github/instructions/xaml.instructions.md` に寄せる。
- Serial / VISA / database / LAN / file I/O / DAQ / hardware / OS 連携の局所ルールは `.github/instructions/infrastructure.instructions.md` に寄せる。
- repo-scoped Copilot hooks は `.github/hooks/*.json` と `.github/hooks/scripts/` に置く。ただし標準 bootstrap は safety guard を中心にし、session continuity hooks は必要な repo だけ明示 opt-in する。
- Git client hooks は `.githooks/` に配置し `core.hooksPath` で有効化する。
- GitHub Actions workflow は `.github/workflows/*.yml|*.yaml` に置く。repo-secure-check で不足した場合は、対象技術に合う template を明示的に選んで導入する。
- `.github/sessions/` と `.github/instructions/session-context.instructions.md` は legacy session continuity hook 生成物として、配布先の `.github/.gitignore` でローカル扱いにする。
- コミット提案は Conventional Commits を優先し、メッセージは日本語で具体的に書く。
- 仕様、設定、使い方、設計判断が変わる場合は README、関連 docs、ADR も更新する。
<!-- TODO: このプロジェクト固有の慣習があれば追記する -->

## セッション終了ワークフロー
- 「ふりかえり」→ `furikaeri-practice` skill を発火。詳細手順は skill 内に定義済み。
- 共有保存も `furikaeri-practice` の中で進め、まず home の `.copilot/docs/furikaeri/` に残し、必要なものだけ `docs/furikaeri/` に共有する。
- `/exit` 直接入力時の sessionEnd 自動 YWT 生成は標準運用から封印済み。日次ふりかえりを明示実行する。

## 優先順位
1. 正確さと安全性
2. 再現性と保守性
3. 学習しやすさと共有しやすさ
4. 実装速度
