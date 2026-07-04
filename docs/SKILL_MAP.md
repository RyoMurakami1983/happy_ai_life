# Skill Map

この文書は、`happy_ai_life` の skill を探すための地図です。詳細手順は各 `SKILL.md` を正本にし、ここでは入口と接続だけを示します。

## 基本導線

```text
to-prd
  -> design-and-plan
    -> implement
      -> implementation-eval-gate
        -> deep-review-preflight
          -> gh-pr-create / gh-pr-respond
```

補助導線:

```text
copilot-authoring
  -> skill-eval
    -> empirical-prompt-tuning
    -> loop-engineering

loop-engineering
  -> happy-add-issue
  -> to-prd
  -> design-and-plan
  -> implement
  -> skill-eval
  -> knowledge-capture
  -> gh-issue-create
```

## happy-core

| skill | 主な使いどころ | 接続先 |
| --- | --- | --- |
| `ask-happy` | どの Happy AI Life skill を使うか迷う | 各基本 skill |
| `beginner-readme-ops` | 初心者向けの README / 運用手順を構造化する | `to-prd` |
| `compact-context` | 長い文脈を次工程へ圧縮する | `session-handoff`, `knowledge-capture` |
| `copilot-authoring` | skill / agent / instructions を作る・改善する | `skill-eval` |
| `empirical-prompt-tuning` | 別実行者で指示の明瞭性を検査する | `skill-eval` |
| `furikaeri` | ふりかえりを残す | `knowledge-capture` |
| `happy-add-issue` | Happy AI Life の skill / docs / 運用への意見を母艦 repo の Issue にする | 必要なら `gh-issue-create` |
| `gh-issue-create` | 今開発中の repo に実行用 Issue を作る | `gh-pr-create` |
| `gh-pr-create` | PR を作る | `deep-review-preflight` |
| `gh-pr-respond` | PR review へ対応する | `deep-review-preflight`, `git-commit` |
| `git-commit` | 原子的 commit を作る | `gh-pr-create` |
| `knowledge-capture` | 公開可能な知識として捕捉する | `furikaeri` |
| `loop-engineering` | 調査、修正、検証、評価、follow-up まで改善ループを回す | `to-prd`, `design-and-plan`, `implement`, `skill-eval`, `knowledge-capture`, `happy-add-issue`, `gh-issue-create` |
| `linux-server-ops` | Ubuntu / Linux サーバーの SSH 接続、sudo、systemd、HTTP 監視を安全に進める | `beginner-readme-ops`, `copilot-authoring` |
| `low-cost-mode` | 低燃費で進める | すべての軽量作業 |
| `pptx` | PowerPoint ファイルを扱う | 文書系作業 |
| `session-handoff` | session を引き継げる形にする | `compact-context` |
| `skill-eval` | skill / prompt 評価の入口 | `empirical-prompt-tuning`, `loop-engineering` |
| `to-prd` | 会話内容を短い PRD にまとめる | `design-and-plan`, `implement` |
| `interview-me` | 企画や設計について、ユーザーに一問ずつ深掘りして確認する | `interview-with-docs` |

## happy-coding

| skill | 主な使いどころ | 接続先 |
| --- | --- | --- |
| `debug` | 再現、切り分け、最小修正を進める | `implement`, `safe-refactor` |
| `deep-review-preflight` | PR 前の事前レビュー | `gh-pr-create` |
| `design-and-plan` | grill 後に実装契約を作る | `implement` |
| `dotnet` | .NET skill の入口 | `dotnet-*` |
| `dotnet-csharp-concurrency-patterns` | .NET 並行処理の選択 | `dotnet` |
| `dotnet-framework-netstandard-bridge` | .NET Framework と .NET 8+ の橋渡し | `dotnet` |
| `dotnet-modern-csharp-coding-standards` | modern C# 実装・リファクタ | `dotnet` |
| `dotnet-setup-dev-environment` | .NET 開発環境の整備 | `dotnet` |
| `dotnet-slopwatch` | .NET anti-slop 品質ゲート | `dotnet` |
| `dotnet-type-design-performance` | .NET 型設計と性能 | `dotnet` |
| `dotnet-wpf-mvvm-patterns` | WPF MVVM 実装 | `dotnet` |
| `dotnet-wpf-secure-config` | WPF の安全な設定管理 | `dotnet` |
| `enterprise-rust-tauri-network-build` | 社内ネットワーク下の Rust / Tauri build | `typescript-tauri-setup` |
| `implement` | 実装契約をローカル実装へ進める | `implementation-eval-gate` |
| `implementation-eval-gate` | slice 完了を評価する | `deep-review-preflight` |
| `interview-with-docs` | 既存の会話から要点を抽出し、インタビューを進める | `interview-me` |
| `domain-modeling` | repo 固有語彙を `CONTEXT.md` に濃縮する | `interview-with-docs`, `copilot-authoring` |
| `modularity-review` | 既存コードの結合構造を分析する | `design-and-plan` |
| `nuget-local` | 自作 NuGet の local feed consume を切り分ける | `dotnet` |
| `prototype` | 実装前に小さく試す | `design-and-plan` |
| `python-setup-dev-environment` | Python 開発環境を整える | `repo-onboarding` |
| `repo-onboarding` | repo 初回把握 | `to-prd` |
| `safe-refactor` | 振る舞い維持のリファクタ | `implement` |
| `tauri-node-sidecar-windows-distribution` | Tauri Node sidecar 配布 | `typescript-tauri-setup` |
| `tauri-sidecar-stability` | Tauri sidecar 安定化 | `typescript-tauri-setup` |
| `typescript-setup-dev-environment` | TypeScript 開発環境を整える | `repo-onboarding` |
| `typescript-tauri-setup` | TypeScript / Tauri setup | `tauri-*` |

## agent

| agent | 主な使いどころ | 接続元 |
| --- | --- | --- |
| `happy-coding:tdd-coder` | 承認済み実装契約を TDD で進める | `implement`, `/fleet` |

## 更新ルール

- `plugins/happy-core/skills/*/SKILL.md` または `plugins/happy-coding/skills/*/SKILL.md` を追加・削除したら、この地図も更新する。
- skill を一覧に追加するだけでなく、どの基本導線から到達するかを必ず書く。
- どの導線にも接続できない skill は、`works/` に留めるか、責務を再設計する。
