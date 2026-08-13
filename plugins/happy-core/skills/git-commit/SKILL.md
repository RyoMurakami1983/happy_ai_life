---
name: git-commit
description: >
  ユーザーが「コミットして」「コミットを作って」などと言ったら、こんなときに使う。文脈がある場合は diff なしで判断し、分からない場合だけ diff を確認して atomic commit を提案・実行する。
user-invocable: false
---

# Git commit

この skill の役割は、ユーザーがコミットを依頼したときに、最小の手順で atomic commit を作れるように案内することです。
既定動作として、**毎回 branch 名候補と commit message 候補を明示し、承認後に commit する** ところまでを含みます。

## こんなときに使う

- 変更内容ごとに atomic commit を作りたい
- `main` / `master` 直コミットを避けつつ安全に進めたい
- branch 名候補と commit message 候補を毎回確認してから commit したい
- 未コミット変更を PR 作成前に整理したい

## ワークフロー: コミットを作る

ユーザーが「コミットして」「コミットを作って」などと言ったら、次の 4 ステップで進めます。

1. 現在の branch と対象 issue を確認し、**毎回 branch 名候補** を出す。必要なら `git-create-branch` を先に通す。
2. 文脈が十分に分かっているなら `git diff` なしで判断する。分からない場合だけ `git diff` を確認する。
3. 変更意図ごとに分割候補を決め、**毎回 commit message 候補** を出す。1 commit = 1 変更意図を基本とする。
4. branch 名候補と commit message 候補の両方について確認を取り、承認後に commit する。

## 実行ルール

- まず「何をコミットしたいか」を短く確認する。
- **毎回 branch 名候補を明示する**。すでに適切な branch にいる場合も、「この branch 名で進める」ことを候補として確認する。
- まず `git-create-branch` で branch の目的と名前を確認し、必要なら新しい branch を作る。
- 現在の branch が `main` / `master` なら、そのまま commit 既定にせず、feature branch 候補を先に提示する。
- 変更内容が明確なら、diff を見ずに候補を出す。
- 変更内容が曖昧なら、必要最小限だけ `git diff` を確認する。
- **毎回 commit message 候補を明示する**。曖昧な仮メッセージのまま commit しない。
- branch 名候補と commit message 候補は、できれば 1 回で並べて提示し、承認後に実行する。
- 1 つのコミットに複数の責務を混ぜない。
- amend / rebase は要確認扱いにする。共有済み履歴を書き換える場合は、まずユーザーに確認する。

## コミットメッセージの基本

- 形式は `type: subject` を基本とする。
- subject は変更意図が明確な日本語を基本とする。type は英語で良い。
- 理由が必要なら本文に `Why:` を入れる。

例:

- `feat: エラー表示を改善`
- `fix: API timeout を延長`
- `docs: README の手順を追記`

## 既定の確認フォーマット

最低限、次の 2 点をセットで出します。

- `branch 名候補: <branch-name>`
- `commit message 候補: <type: subject>`

どちらかが未確定でも、「今回はこの branch で進める」または「この message 候補で commit する」を明示し、承認後に実行します。

## 例

- 「この変更は機能追加とテスト追加が混ざっている」なら、分けて提案する。
- 「このコミットは docs のみ」なら、docs 単位でまとめる。
- 「履歴を直す必要がある」なら、amend / rebase ではなくユーザー確認を入れる。

## 注意点

- **branch 名候補を省略しない**: すでに適切な branch でも、「この branch で進める」と明示した方が事故を防ぎやすいです。
- **commit message を仮のまま走らせない**: `fix stuff` のような曖昧な候補をそのまま使わず、意図が分かる subject に整えます。
- **確認を曖昧時だけにしない**: issue #249 の方針として、branch 名候補と commit message 候補の確認は毎回の既定です。

## 使わない場面

- すでにコミット済み内容の再解釈が必要な場合
- 共有ブランチに対して履歴を書き換える場合
- 依頼内容が「コミット」ではなく「PR作成」や「レビュー対応」そのものの場合
