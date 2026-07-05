---
name: gh-pr-create
description: >
  ユーザーが「PR を作って」「プルリク作って」などと言ったら、こんなときに使う。feature branch の変更を PR として出し、レビュー待機へ安全に移す。検証済み変更をレビューに出したい場合に使用します。
---

# GitHub PR 作成

この skill の役割は、レビューに出すための PR を 1 回で作り、必要な情報を残して待機へ移すことです。

## 使い方

次の 4 ステップで進めます。

1. 現在の branch / status / 既存 PR を確認する。
2. 必要なら commit / push する。
3. 日本語本文と `Closes #N` を付けて `gh pr create` する。
4. PR URL を記録したら、レビューシグナル待ちへ移す。新しいレビューが来たら `gh-pr-respond` へ渡す。

## 実行ルール

- main ではなく feature branch から作る。
- まず `git-create-branch` で branch の目的と名前を確認し、必要なら新しい branch を作る。
- 変更が未コミットなら、まず `git-commit` で整理する。
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

## 使わない場面

- 実際のレビューコメント対応
- マージそのもの
- 履歴の書き換え
