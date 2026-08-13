---
name: gh-pr-create
description: >
  ユーザーが「PR を作って」「プルリク作って」などと言ったら、こんなときに使う。feature branch の変更を PR として出し、レビュー待機へ安全に移す。検証済み変更をレビューに出したい場合に使用します。
---

# GitHub PR 作成

この skill の役割は、レビューに出すための PR を 1 回で作り、必要な情報を残して待機へ移すことです。
既定動作として、PR 作成前に **branch 名候補を確認し、未コミットなら `git-commit` の commit message 候補確認も必ず引き継ぐ** ことを含みます。

## こんなときに使う

- feature branch の変更を PR として安全に出したい
- 未コミット変更を整理してから PR を作りたい
- branch 名候補と commit message 候補の確認を維持したまま PR へ進みたい
- 既存 open PR の重複作成を避けたい

## ワークフロー: PR を作る

次の 4 ステップで進めます。

1. 現在の branch / status / 既存 PR を確認し、**毎回 branch 名候補** を明示する。
2. 必要なら commit / push する。未コミットなら **commit message 候補** を含む `git-commit` の確認ルールを使う。
3. 日本語本文と `Closes #N` を付けて `gh pr create` する。
4. PR URL を記録したら、レビューシグナル待ちへ移す。新しいレビューが来たら `gh-pr-respond` へ渡す。

## 実行ルール

- main ではなく feature branch から作る。
- **毎回 branch 名候補を確認する**。すでに適切な branch 上でも、その branch 名で進めることを候補として明示する。
- まず `git-create-branch` で branch の目的と名前を確認し、必要なら新しい branch を作る。
- 変更が未コミットなら、まず `git-commit` で整理する。このとき **branch 名候補と commit message 候補を提示し、承認後に commit する** 既定を引き継ぐ。
- push していないなら `git push -u origin <branch>` する。
- 既存の open PR があるなら、新しく作らず、既存 URL を報告して止める。
- `gh pr create` では `--body-file` を使う。本文は日本語で、`Closes #N` か `Refs #N` を入れる。
- PR を作ったら、URL を 1 回だけ記録して待機モードに入る。
- amend / rebase は要確認扱いにする。

## 最低限の本文テンプレート

```markdown
## 概要
(何を変えたか)

## 理由
(なぜ必要か)

## テスト
(どう確認したか)

## 関連
Closes #N
```

## 例

```bash
gh auth status
git status
git push -u origin <branch>
gh pr create --title "feat: 変更内容" --body-file <file>
```

未コミット変更がある場合の既定確認:

```text
branch 名候補: feature/123-改善内容
commit message 候補: feat: 改善内容を追加
承認後に commit してから PR を作成する
```

## 注意点

- **branch 名候補の確認を飛ばさない**: push 前後で branch を取り違える事故を避けるため、毎回明示します。
- **未コミット時は commit 確認を弱めない**: `git-commit` に渡すときも branch 名候補と commit message 候補の承認を省略しません。
- **既存 PR を見落とさない**: 同じ branch の open PR がある場合は新規作成より既存 URL の案内を優先します。

## 使わない場面

- 実際のレビューコメント対応
- マージそのもの
- 履歴の書き換え
