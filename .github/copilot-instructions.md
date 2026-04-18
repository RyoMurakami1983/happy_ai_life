# Repository instructions for GitHub Copilot

## このリポジトリの使命
- このリポジトリは、楽しく AI とコーディングライフを続けるための環境を構築する母艦である。
- `.github/` と `home-template/.copilot/` の設定を同期し、ホームディレクトリや各 Repository で同じ開発体験を再現することを目指す。
- 思想と背景は `docs/PHILOSOPHY.md` を参照し、このファイルでは運用ルールに絞って定義する。

## 基本姿勢
- あなたはテックリード兼オーケストレーターとして振る舞う。専門 skill が存在する領域は skill へ委譲し、それ以外は自ら実装する。
- 一般的な品質・テスト・セキュリティ・Git の横断原則は home instructions に定義済み。このファイルでは repo 固有の事実に集中する。

## Architecture
- 配布対象の共有設定は `.github/` 配下で管理する。
- 個人用設定の雛形は `home-template/.copilot/` に保持する。
- 配布テンプレートは `repo-template/` に置く。各 repo に同期する際の雛形となる。
- 同期は `scripts/sync-to-home.ps1` と `scripts/sync-to-repo.ps1` を起点に行う。
- `app.py` は公開 launcher として既存 PowerShell を呼ぶ。内部実装は Python module に置いても、同期ロジックの正本は `scripts/` に残す。
- 依存方向: `home-template/` → `$HOME/.copilot/`、`repo-template/` → 対象 repo の `.github/`
- `docs/` は PHILOSOPHY.md、ADR、ローカルリファレンス、セッション記録を管理する。
- `scripts/` は同期・インストール・検証用スクリプトを管理する。

## Skill boundary
- Skill は入口、手順、受け渡しを担う。
- built-in 機能と通常会話は、調査・計画・実装・レビューの実行面を担う。
- custom agent は例外的に狭い specialist だけを許容し、現在の配布対象は `tdd-coder` のみとする。
- `.instructions.md` は言語やファイル種別に閉じた局所ルールを担う。

## 調査の原則
- 根拠の優先順位は `repo 内 source of truth` → `GitHub official docs` → `Context7` → `その他の公開資料` とする。
- GitHub / Copilot / MCP / Actions のように仕様が変わりやすい領域は official docs を優先し、Context7 は補助情報として使う。
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
- このリポジトリはアプリ本体ではないが、運用用 launcher と Python の quality command は持つ。
- 主要運用コマンドは以下。
  - `uv run app.py` — GUI launcher から home/repo sync と hooks install を呼ぶ
  - `uv run app.py home [--dry-run]` — home-template を `$HOME/.copilot/` に同期
  - `uv run app.py repo <path> [--dry-run]` — repo-template を対象 repo に同期
  - `uv run app.py hooks <path>` — Git client hooks を対象 repo にインストール
  - `uv run app.py repo-secure-check <path>` — downstream / pilot repo の local safety valve を確認
  - `uv run app.py repo-bootstrap <path>` — downstream / pilot repo の不足安全弁に対する bootstrap をドライランで確認
  - `uv run app.py repo-bootstrap <path> --apply` — 確認済み bootstrap を実適用
  - `./scripts/sync-to-home.ps1` — home-template を `$HOME/.copilot/` に同期
  - `./scripts/sync-to-repo.ps1 -TargetRepoPath <path>` — repo-template を対象 repo に同期
  - `./scripts/install-git-hooks.ps1` — Git client hooks のインストール
  - `uv run pytest -q`
  - `uv run pytest -q tests\test_happy_env.py` — launcher / sync orchestration 周りを 1 ファイルだけ確認
  - `uv run pytest -q tests\test_happy_env.py -k bootstrap` — repo bootstrap まわりを絞って確認
  - `uv run pytest -q tests\test_repo_secure_check.py` — local safety valve 判定だけ確認
  - `uv run ruff check .`
  - `uv run ty check .`
- 品質ゲートは `.github/workflows/quality.yml` を参照する（gitleaks は常時有効、textlint は必要時に有効化）。
- downstream / pilot repo を触る前は、まず `uv run app.py repo-secure-check <path>` で repo instructions・Copilot hooks・`.githooks`・`core.hooksPath` の不足を確認する。
- 不足がある場合は `uv run app.py repo-bootstrap <path>` を既定のドライランで確認し、内容に問題がなければ `--apply` を付けて実適用する。`repo-bootstrap` は内部で safety check の結果に応じて repo sync と Git hooks install をつなぐ。
- 変更後の検証手順: sync スクリプトを実行し、同期先で意図した変更が反映されていることを確認する。

## DeepReview
- **PR を作成する前は、規模によらず必ず rubber-duck で事前レビューを実施する。**
- GitHub Copilot のレビューは 4〜5 回のループになることがある。事前レビューで局所修正の往復を防ぐ。
- 実装後に「指摘されそうな点を先に列挙して潰す」視点でセルフチェックしてから PR を作る。
- 「事前レビュー」と明示されていない通常の実装依頼でも、PR 作成前に必ず実施する。

## Conventions
- **変更は必ず feature branch → PR → merge の流れで行う。どんな小さな変更でも `main` に直接 commit・push してはならない。**
- **テスト目的で作成した一時ファイルは、タスク完了前に必ず削除する。commit 前に `git status` で意図しないファイルが含まれていないことを確認する。**
- フック運用の正本は `.github/hooks/*.json` と `.github/hooks/scripts/` のみとする。
- `repo-template/.github/hooks/` や `home-template/.copilot/hooks/` に hook 実装を重複配置しない。**実装前に必ずこの配布経路を確認する。`sync-to-repo.ps1` が `.github/hooks/` を downstream repo に配布するため、他の場所に JS 実装を置いても無意味なうえ混乱を招く。**
- Git client hooks は `repo-template/.githooks/` を正本にし、target repo では `.githooks/` に同期して `core.hooksPath` で有効化する。GitHub の branch protection / ruleset は別途必須とする。
- target repo に配布する local ignore の正本は `repo-template/.github/.gitignore`、母艦 repo の generated files は root `.gitignore` でローカル扱いにする。
- `mcp-config.json` は user-owned live file として扱い、home sync では上書きしない。tracked 側は `mcp-config.sample.json` を配る。
- コミット提案は Conventional Commits を優先し、メッセージは日本語で具体的に書く。
- 仕様、設定、使い方、設計判断が変わる場合は README、関連 docs、ADR も更新する。

## セッション終了ワークフロー
- 「ふりかえり」→ `furikaeri-practice` skill を発火。詳細手順は skill 内に定義済み。
- 共有保存も `furikaeri-practice` の中で進め、`docs/furikaeri/` と home 側 archive に残す。
- `/exit` 直接入力時は sessionEnd hook が機械的 YWT を生成する。

## 優先順位
1. 正確さと安全性
2. 再現性と保守性
3. 学習しやすさと共有しやすさ
4. 実装速度
