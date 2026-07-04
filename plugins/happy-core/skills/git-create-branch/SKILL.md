---
name: git-create-branch
description: >
  ユーザーが「ブランチを作って」「新しいブランチを作って」などと言ったら、こんなときに使う。目的に合う日本語主体の命名と安全な作成手順を提案して branch を作る。main/master から分岐しやすい形に整えたいときに使用します。
user-invocable: false
---

# Git create branch

この skill の役割は、ユーザーが新しい作業ブランチを作るときに、名前の迷いを減らし、main/master から分岐しやすい形に整えることです。

## こんなときに使う

- 新しい feature / fix / docs 用の branch を作りたい
- issue や ticket 番号に合わせた branch 名を決めたい
- main / master 上で作業したくないときに、作業用 branch を切りたい
- どの prefix を使うべきか迷う

## ワークフロー: ブランチを作る

### ステップ 1 — 目的とベースを確認する
作る branch の用途、対象 issue / ticket、ベース branch を短く確認します。迷っている間に branch を作らないようにします。

### ステップ 2 — 命名ルールを決める
branch 名は短く、説明的に、kebab-case で書きます。日本語の目的名を主軸にし、必要に応じて英数字に変換した短い表現を使います。基本は次の順です。

- prefix: `feature/`, `fix/`, `docs/`, `refactor/`, `chore/`
- issue 番号があるなら `123-` のように入れる
- その後に、目的を表す日本語主体の 2〜4 語の短い説明を入れる

例:
- `feature/123-ログイン改善`
- `fix/456-api-timeout`
- `docs/789-readme-setup`
- `refactor/101-ブランチ命名整理`

### ステップ 3 — 実際に branch を作る
ベース branch を確認したら、次の形で作ります。

```bash
git switch <base-branch>
git pull --ff-only
git switch -c <branch-name>
```

必要なら `git push -u origin <branch-name>` まで案内します。

## ベストプラクティス

- 1 つの branch につき 1 つの目的にする
- 名前は英小文字・kebab-case・短めにする
- 日本語の目的名を主軸にし、必要なら英数字に変換して短くする
- 既存の issue / ticket があれば番号を入れる
- `main` / `master` で直接作業しない
- すでに似た名前があれば再利用せず、説明を少し変える

## 注意点

- **名前が長すぎる**: 30 文字前後に収め、説明は 2〜4 語に絞ると見通しが良いです。
- **prefix を付けない**: `feature/` や `fix/` のような種別を付けると、後から並べやすくなります。
- **base branch を確認しない**: どの branch から切るかを決めないと、後で差分が崩れやすくなります。

## 例

- 仕様追加: `feature/214-ログイン改善`
- バグ修正: `fix/315-ログインタイムアウト`
- ドキュメント更新: `docs/410-セットアップ手順`
- 内部整理: `refactor/512-ブランチ命名整理`
