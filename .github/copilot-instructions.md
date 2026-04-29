# Repository instructions for GitHub Copilot

## このリポジトリの使命
- このリポジトリは、楽しく AI とコーディングライフを続けるための環境を構築する母艦である。
- reusable skills / agents は Copilot CLI plugin を primary distribution とし、home sync は trusted local author bootstrap として残す。
- 思想と背景は `docs/PHILOSOPHY.md` を参照し、このファイルでは運用ルールに絞って定義する。

## 基本姿勢
- あなたはテックリード兼オーケストレーターとして振る舞う。専門 skill が存在する領域は skill へ委譲し、それ以外は自ら実装する。
- 一般的な品質・テスト・セキュリティ・Git の横断原則は home instructions に定義済み。このファイルでは repo 固有の事実に集中する。

## Architecture
- 公開・共有向けの primary distribution は `plugins/happy-ai-life/` の Copilot CLI plugin とする。
- 個人用設定の雛形は `home-template/.copilot/` に保持し、trusted local author bootstrap としてだけ home sync する。`skills/`、`agents/`、`docs/` は持たせず、開発者自身も plugin install を使う。
- 配布テンプレートは `repo-template/` に置く。各 repo に同期する際の雛形となる。
- 同期は `scripts/sync-to-home.ps1` と `scripts/sync-to-repo.ps1` を起点に行う。
- `app.py` は公開 launcher として既存 PowerShell を呼ぶ。内部実装は Python module に置いても、同期ロジックの正本は `scripts/` に残す。
- 配布方向: `plugins/happy-ai-life/` → Copilot CLI installed plugin、`home-template/` → `$HOME/.copilot/` の最小 bootstrap、`repo-template/` → 対象 repo の `.github/`
- `docs/` は PHILOSOPHY.md、ADR、ローカルリファレンス、セッション記録を管理する。
- `scripts/` は同期・インストール・検証用スクリプトを管理する。

## Skill boundary
- Skill は入口、手順、受け渡しを担う。
- built-in 機能と通常会話は、調査・計画・実装・レビューの実行面を担う。
- custom agent は例外的に狭い specialist だけを許容し、現在の配布対象は `tdd-coder` のみとする。
- `.instructions.md` は言語やファイル種別に閉じた局所ルールを担う。

## 調査の原則
- 根拠の優先順位は `repo 内 source of truth` → `GitHub official docs` → `installed plugins` → `その他の公開資料` とする。
- GitHub / Copilot / Actions / plugin のように仕様が変わりやすい領域は official docs を優先し、外部 plugin や公開資料は補助情報として使う。
- 結論は `事実` / `推論` / `未確認事項` に分け、曖昧さを埋めない。
- 構造判断と実行順序は分け、調査結果をそのまま実装へ流し込まない。

## Skill ディスパッチ（必須）
- 調査・一次情報確認・現状のベストプラクティス把握 → built-in 機能または自分で実施する。
- 仕様作成・要件定義・前提条件の整理 → `spec-workshop` を使う。仕様の骨子づくりに集中する。
- 設計・構造検証 → `design-workshop` を使う。仕様書を受け取り、標準設計と Balanced Coupling レンズ設計を振り分け、planning handoff を作る。
- 実装計画・フェーズ分割・段取り整理 → PLAN mode を使う。目的、制約、段階、Why、検証、リスク、今決めなくてよいことを残す。
- TDD 実装を小さく進める specialist が必要で、前提成果物がそろっている → `tdd-coder` を `/fleet` または明示指名で使う。仕様・設計・計画の入口としては使わない。
- custom skill / agent / repository instructions の作成・改善・検証 → `copilot-authoring` を使う。内部で `skill` と `create-agents`、instructions authoring に分岐するため、直接そちらを起点にしない。
- 既存コードの結合構造分析・モジュール境界の見直し → `modularity-review` を使う。3 次元（統合強度・距離・変動性）で不均衡を検出する。
- 仕様駆動開発（ゼロから / 途中再開）→ `sdd` を使う。内部で spec-workshop / design-workshop / PLAN mode 等につなぐ。

## Build and Test
- このリポジトリはアプリ本体ではないが、Copilot CLI plugin package、運用用 launcher、Python の quality command は持つ。
- 主要運用コマンドは以下。
  - `copilot plugin marketplace add RyoMurakami1983/happy_ai_life_coding_Environment` — owner-managed marketplace を登録する
  - `copilot plugin install happy-ai-life@happy-ai-life-marketplace` — public/shared primary install path（branch push 後に marketplace install を検証）
  - `uv run app.py` — GUI launcher から trusted local home sync を呼ぶ
  - `uv run app.py home [--dry-run]` — home-template を `$HOME/.copilot/` に同期
  - `./scripts/sync-to-home.ps1` — home-template を `$HOME/.copilot/` に同期
  - `./scripts/sync-to-repo.ps1 -TargetRepoPath <path>` — repo-template を対象 repo に同期
  - `./scripts/install-git-hooks.ps1` — Git client hooks のインストール
  - `uv run pytest -q`
  - `uv run pytest -q tests/test_happy_env.py` — launcher / sync orchestration 周りを 1 ファイルだけ確認
  - `uv run pytest -q tests/test_repo_secure_check.py` — Windows では local safety valve 判定を確認、非 Windows 環境では `os.name != 'nt'` により skip される
  - `uv run ruff check .`
  - `uv run ty check .`
- 品質ゲートは `.github/workflows/quality.yml` を参照する（gitleaks は常時有効、textlint は必要時に有効化）。
- downstream / pilot repo を触る前は、`$HOME\.copilot\scripts\repo-secure-check.ps1` で repo instructions・Copilot safety hooks・`.githooks/pre-commit`・`.githooks/pre-push`・`.githooks/lib/*.sh`・`core.hooksPath`・`.github/workflows/*.yml|*.yaml` の不足を確認する。不足がある場合は `$HOME\.copilot\scripts\sync-to-repo.ps1` と `$HOME\.copilot\scripts\install-git-hooks.ps1`、または対象技術の workflow setup skill で補う。secret guard は `gitleaks` 必須で、`.gitleaks.toml` が無い repo でも default rules で fail-closed scan する。`sessionStart` / `sessionEnd` の repo-local continuity hooks は標準運用から封印済みで、必要な legacy repo だけ `sync-to-repo.ps1 -HooksMode All` で明示 opt-in する。
- plugin 変更後の検証手順: remote の marketplace add / browse / install / list / uninstall / remove は merge 後の default branch 状態を確認する手順として扱う。feature branch を push しただけでは `<owner>/<repo>` 指定の marketplace 経由で PR ブランチの manifest 変更は通常確認できないため、merge 前の smoke test が必要な場合はローカル checkout の repo root を marketplace として add して確認する。direct repository / URL / local path install は deprecated fallback とし、primary path にはしない。sync 変更時は sync スクリプトを実行し、同期先で意図した変更が反映されていることを確認する。

## DeepReview
- **PR を作成する前は、規模によらず必ず built-in レビュー機能または自分で段階的にセルフチェックする形で事前レビューを実施する。**
- 事前レビューでは、変更点を説明しながら「意図」「想定リスク」「壊れうる箇所」を順に洗い出し、指摘されそうな点を先に列挙して潰す。
- GitHub Copilot のレビューは 4〜5 回のループになることがある。事前レビューで局所修正の往復を防ぐ。
- 「事前レビュー」と明示されていない通常の実装依頼でも、PR 作成前に必ず実施する。

## Conventions
- **変更は必ず feature branch → PR → merge の流れで行う。どんな小さな変更でも `main` に直接 commit・push してはならない。**
- **テスト目的で作成した一時ファイルは、タスク完了前に必ず削除する。commit 前に `git status` で意図しないファイルが含まれていないことを確認する。**
- repo-scoped Copilot hooks の正本は `.github/hooks/*.json` と `.github/hooks/scripts/` のみとする。ただし標準配布は safety guard に限定し、session continuity hooks は封印済み legacy opt-in として扱う。
- generic safety behavior は `%USERPROFILE%\.copilot\config.json` の user-level hook を正本とし、home sync が managed entry だけを upsert する。repo 固有の hook は `repo-template/.github/hooks/` を正本にする。plugin hook は path resolution / ordering を spike で検証できるまで primary safety とせず、repo-scoped `safety-guard.json` を fallback として維持する。
- Git client hooks は `repo-template/.githooks/` を正本にし、target repo では `.githooks/` に同期して `core.hooksPath` で有効化する。`pre-commit` は staged content、`pre-push` は push range を gitleaks で検査する。GitHub の branch protection / ruleset は別途必須とする。
- target repo に配布する local ignore の正本は `repo-template/.github/.gitignore`、母艦 repo の generated files は root `.gitignore` でローカル扱いにする。
- `mcp-config.json` は user-owned live file として扱い、home sync では上書きしない。この母艦 repo は MCP config sample を primary path として配布しない。Context7 が必要な場合は外部 Copilot CLI plugin として案内する。
- コミット提案は Conventional Commits を優先し、メッセージは日本語で具体的に書く。
- 仕様、設定、使い方、設計判断が変わる場合は README、関連 docs、ADR も更新する。

## セッション終了ワークフロー
- 「ふりかえり」→ `furikaeri-practice` skill を発火。詳細手順は skill 内に定義済み。
- 共有保存も `furikaeri-practice` の中で進め、`docs/furikaeri/` と home 側 archive に残す。
- `/exit` 直接入力時の sessionEnd 自動 YWT 生成は標準運用から封印済み。文脈継承は公式 session data と `furikaeri-practice` による日次保存を主導線にする。

## 優先順位
1. 正確さと安全性
2. 再現性と保守性
3. 学習しやすさと共有しやすさ
4. 実装速度
