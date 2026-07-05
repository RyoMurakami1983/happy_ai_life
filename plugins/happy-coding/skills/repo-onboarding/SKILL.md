---
name: repo-onboarding
description: >
  既存リポジトリの構造、主要技術、ビルド方法、テスト方法、重要ファイルを短時間で把握する。
  新しいリポジトリを理解したいとき、最初の地図を安全に作りたいとき、
  または作業開始前に repo bootstrap まで完了したいとき。
license: Personal
---

# repo-onboarding

この skill は、未知のリポジトリを短時間で安全に理解するための手順です。
repo を読むだけでなく、共同作業の場として触り始める依頼では
bootstrap 完了までを onboarding の一部として扱います。

## こんなときに使う

- 新しいリポジトリの入口を短時間で把握したいとき
- README と設定ファイルから build / test の根拠を拾いたいとき
- 後続の実装や調査に入る前に「最初の地図」を作りたいとき

## 目的
- 主要言語と技術スタックを把握する
- エントリーポイント、ビルド方法、テスト方法を把握する
- 重要な設定ファイルとドキュメントを特定する
- 後続作業のための「最初の地図」を作る
- 必要なら repo bootstrap を実行し、共同作業に必要な safety valve をそろえる

## 作業モード

- **Read-only onboarding**: repo の構造や build / test 方法を把握する依頼。調査を主に進める。
- **Bootstrap onboarding**: 「ここを作業場所にしたい」「repo として整えたい」「共同開発の場にしたい」のように、
  repo を今後触る前提の依頼。`repo-secure-check` で不足が出たら、提案で止めず script 実行まで進める。

## ワークフロー

### ステップ 1 — 入口ファイルを確認する

まず README、docs、solution / workspace / manifest 系ファイルを確認します。
ここで全体像をつかんでから詳細へ入ると、後段の build / test 調査がぶれにくくなります。

### ステップ 2 — build / test / dependency の根拠を拾う

ビルド・テスト・依存関係・lint に関わる設定ファイルを確認します。
コマンドは推測で作らず、README や設定ファイルに根拠があるものを優先します。

### ステップ 3 — bootstrap が必要かを判定する

target repo を今後触る依頼なら、`repo-secure-check` で
`repo instructions / Copilot hooks / .githooks / core.hooksPath / GitHub Actions workflows` の不足を確認します。
この判定を先に置く理由は、安全弁が欠けたまま onboarding を完了扱いにしないためです。

### ステップ 4 — 不足があれば bootstrap を実行する

不足がある場合は onboarding を続ける前に bootstrap task として次を**実行**します。
以下は **home sync 済みの `%USERPROFILE%\.copilot\scripts\`** から実行する前提とし、
script の既定値で `%USERPROFILE%\.copilot` を `SourceRoot` として扱います。

- git repo でなければ `git init`
- `%USERPROFILE%\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath <repo>`
- `%USERPROFILE%\.copilot\scripts\install-git-hooks.ps1 -TargetRepoPath <repo>`
- `%USERPROFILE%\.copilot\scripts\repo-secure-check.ps1 -TargetRepoPath <repo>`

ここでは **「提案した」で止めず、script 実行結果まで確認する** のが重要です。
`repo-secure-check` の各項目がすべて `OK` になるまでを bootstrap 完了条件として扱います。
`.github/workflows/*.yml|*.yaml` が不足している場合は、repo の技術スタックに合う workflow template を明示的に選び、
必要な skill または `sync-to-repo.ps1` の導線で導入します。CI workflow は組織・言語ごとに差が出るため、
ユーザーに黙って汎用 workflow を追加せず、意図と対象 runtime を確認してから実行します。

### ステップ 5 — ディレクトリと入口を要約する

`repoInstructions / Copilot hooks / .githooks / core.hooksPath / GitHub Actions workflows` がすべて `OK` になったら、
主要ディレクトリの役割を要約し、エントリーポイント候補を特定します。

### ステップ 6 — テスト導線を確認する

テストの場所、実行手段、カバレッジの有無を確認します。
未確認のものは推測で埋めず、「未確認事項」として分離します。

## 特に見るファイル
- C#: `*.sln`, `*.slnx`, `*.csproj`, `Directory.Build.*`, `global.json`
- Python: `pyproject.toml`, `requirements.txt`, `setup.cfg`, `pytest.ini`
- C: `Makefile`, `CMakeLists.txt`, `meson.build`
- TypeScript: `package.json`, `tsconfig.json`, `eslint.config.*`, `vite.config.*`
- Rust: `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`

## 出力形式
以下の順で短くまとめる。
1. Bootstrap 状態（Read-only か Bootstrap 実行済みか。実行した場合は `repo-secure-check` の結果）
2. リポジトリの目的
3. 主要言語と主要技術
4. ディレクトリ構造の要点
5. ビルド方法
6. テスト方法
7. 重要な設計上の注意点
8. 未確認事項

## 方針
- まず全体像をつかみ、細部に潜りすぎない
- 見つけたコマンドは、設定ファイルや README に根拠があるものを優先する
- 学習用の説明では「何が入口か」を明確にする
- local safety valve や GitHub Actions workflow が不足している repo は、その事実を先に明示し、必要なら repo bootstrap を提案してから深掘りする
- ただし downstream repo を触る flow では、**提案で止めず** `.github/` と `.githooks/` の同期、`core.hooksPath` 設定、再チェック完了までを bootstrap の一部として扱う
- `.github` がない repo を「onboarding 完了」とは扱わない。最低でも `repo-secure-check` の各項目が `OK` になってから本調査へ進む
- `%USERPROFILE%\.copilot\scripts\` が存在しない、または script 実行に失敗した場合だけ、その事実を block として明示して止まる
