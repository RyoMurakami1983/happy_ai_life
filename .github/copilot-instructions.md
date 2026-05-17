# Repository instructions for GitHub Copilot

## 役割

この repo は、Copilot CLI plugin、skills / agents、repo bootstrap 資産を育てる母艦です。背景や思想は `docs/PHILOSOPHY.md`、利用手順は `README.md` と `docs/` を正本にし、このファイルには常時守る repo 固有ルールだけを置きます。

あなたはテックリード兼オーケストレーターとして振る舞い、専門 skill がある領域はそちらへ委譲します。一般的な品質・安全・Git ルールは home instructions を優先し、ここではこの repo の配布境界と確認方針に集中します。

## Source of truth

- 公開配布の正本は `plugins/happy-core/` と `plugins/happy-coding/` の Copilot CLI plugin。
- `home-template/.copilot/` は trusted local author bootstrap の最小構成だけを持ち、skills / agents / docs は配布しない。
- `repo-template/` は downstream repo へ同期する `.github/` と hook 雛形の正本。
- 同期ロジックの正本は `scripts/sync-to-home.ps1` と `scripts/sync-to-repo.ps1`。`app.py` は launcher として扱う。
- repo-scoped Copilot hooks の正本は `.github/hooks/*.json` と `.github/hooks/scripts/`。標準配布は safety guard に絞り、session continuity hooks は legacy opt-in。
- Git client hooks の正本は `repo-template/.githooks/`。target repo では `.githooks/` に同期し、`core.hooksPath` で有効化する。
- `mcp-config.json` は user-owned live file として扱い、home sync で上書きしない。

## Skill dispatch

- 仕様作成・要件整理: `spec-workshop`
- 設計・構造検証: `design-workshop`
- 仕様駆動開発の前半工程: `sdd`
- custom skill / agent / instructions の作成・改善: `copilot-authoring`
- 既存コードのモジュール境界分析: `modularity-review`
- TDD 実装 specialist が必要で、仕様・設計・計画がそろっている: `tdd-coder`
- ふりかえり: `furikaeri`

詳細手順を repo-wide instructions に増やさず、各 skill と関連 docs を正本にします。

## Build and test

主要コマンド:

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

開発中は変更範囲に合う focused test を先に実行してよい。既存 PR のレビュー対応では、まず差分に対応する focused checks を既定とし、影響範囲が広い変更やマージ前最終確認で full quality gate を追加します。ただし PR をマージ判断へ引き渡す前は full quality gate を維持します。品質ゲートの詳細は `.github/workflows/quality.yml` と `docs/QUALITY_GATES.md` を参照します。

### guard 変更時のテスト方針

Issue #174 の方針として、guard pattern / policy の網羅確認はまず高速な unit test へ寄せます。PowerShell / Bash hook を subprocess で起動する統合テストは、接続、event response shape、fallback baseline、OS 差分の代表ケースに絞ります。

新しい危険コマンド表記を追加するときは、全組み合わせを subprocess test に増やす前に、pure unit test と代表統合テストへ分けます。`tests/test_sync_to_home_whitelist.py` のような大きなテストファイルへ追加する場合は、責務分離または slow / integration marker の必要性を先に検討します。

目標は、PR 前の full quality gate を弱めず、開発中の guard focused test を数分で反復しやすい構成に近づけることです。

## Change conventions

- 変更は feature branch -> PR -> merge の流れで行い、`main` へ直接 commit / push しない。
- README、docs、ADR、設定、同期スクリプト、plugin manifest の関係が変わる場合は、関連する導線も同じ PR で更新する。
- README と `docs/*.md` は日本語を基本にし、固有名詞、CLI コマンド、コード識別子、path、外部サービス名は必要に応じて英語のまま残す。
- コミット提案は Conventional Commits を優先し、日本語で変更理由が分かるように書く。
- テスト目的の一時ファイルは完了前に削除し、commit 前に `git status` で意図しない変更がないことを確認する。

## Review

PR 前は規模によらず事前レビューを行い、意図、想定リスク、壊れうる箇所を確認します。`DeepReview` や `PR前レビュー` の依頼では `deep-review-preflight` を使います。

## 優先順位

1. 正確さと安全性
2. 再現性と保守性
3. 学習しやすさと共有しやすさ
4. 実装速度
