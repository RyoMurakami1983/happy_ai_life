---
name: repo-onboarding
description: >
  既存リポジトリの構造、主要技術、ビルド方法、テスト方法、重要ファイルを短時間で把握する。
  Use when: 新しいリポジトリを理解したいとき、最初の地図を安全に作りたいとき。
license: Personal
---

# repo-onboarding

この skill は、未知のリポジトリを短時間で安全に理解するための手順です。

## こんなときに使う

- 新しいリポジトリの入口を短時間で把握したいとき
- README と設定ファイルから build / test の根拠を拾いたいとき
- 後続の実装や調査に入る前に「最初の地図」を作りたいとき

## 目的
- 主要言語と技術スタックを把握する
- エントリーポイント、ビルド方法、テスト方法を把握する
- 重要な設定ファイルとドキュメントを特定する
- 後続作業のための「最初の地図」を作る

## ワークフロー:
1. まず README、docs、solution / workspace / manifest 系ファイルを確認する。
2. 次に、ビルド・テスト・依存関係・lint に関わる設定ファイルを確認する。
3. target repo を触る前提作業なら、`repo-secure-check` で repo instructions / Copilot hooks / `.githooks` / `core.hooksPath` の不足を確認する。
4. 主要ディレクトリの役割を要約する。
5. エントリーポイント候補を特定する。
6. テストの場所、実行手段、カバレッジの有無を確認する。
7. 不明点は推測で断定せず、「未確認事項」として分離する。

## 特に見るファイル
- C#: `*.sln`, `*.slnx`, `*.csproj`, `Directory.Build.*`, `global.json`
- Python: `pyproject.toml`, `requirements.txt`, `setup.cfg`, `pytest.ini`
- C: `Makefile`, `CMakeLists.txt`, `meson.build`
- TypeScript: `package.json`, `tsconfig.json`, `eslint.config.*`, `vite.config.*`
- Rust: `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`

## 出力形式
以下の順で短くまとめる。
1. リポジトリの目的
2. 主要言語と主要技術
3. ディレクトリ構造の要点
4. ビルド方法
5. テスト方法
6. 重要な設計上の注意点
7. 未確認事項

## 方針
- まず全体像をつかみ、細部に潜りすぎない
- 見つけたコマンドは、設定ファイルや README に根拠があるものを優先する
- 学習用の説明では「何が入口か」を明確にする
- local safety valve が不足している repo は、その事実を先に明示し、必要なら repo bootstrap を提案してから深掘りする
