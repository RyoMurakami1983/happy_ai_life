---
name: happy-add-issue
description: >
  短い自然文や雑なメモから、最低限行動可能な GitHub Issue に整えてすばやく起票する軽量入口。 Use when: 作業中に見つけた別件をその場で backlog 化したいとき、PR や debug 中の follow-up を低摩擦で切り出したいとき。
---

# Happy Add Issue

Happy Add Issue は、作業の途中で見つけた改善点を「あとで書こう」で失わないための軽量入口です。
詳細な整形や公開向け匿名化の本体は `gh-issue-create` を正本にし、この skill は**短い入力から最小の Issue 骨格を作ってすぐ起票する**ところに絞ります。

## ゴール

- 短い入力を、見失わない最小の GitHub Issue 骨格へ変える。

## 成功条件

- タイトル、背景、問題、提案、Acceptance Criteria が 1 回で埋まる。
- 詳細化が必要な場合に `gh-issue-create` へ迷わず handoff できる。

## こんなときに使う

- PR、debug、loop-engineering の途中で別件をすぐ backlog 化したい
- 「この改善を Issue にして」の 1 文から最小限の本文を作りたい
- ラベルや受け入れ条件をゼロから考える前に、まず追跡可能な形へ残したい
- 後続担当へ「何を直すべきか」だけ先に渡したい

## 使わない場面

- 公開 repo 向け匿名化、ラベル設計、受け入れ条件の厳密化まで丁寧にやりたい
- 既存 Issue の本文を大きく再設計したい
- 1 本の大きい epic を vertical slice に分割したい

その場合は `gh-issue-create` を使います。

## ワークフロー:

```text
rough note
  -> 1文に圧縮
  -> 最小テンプレへ整形
  -> Acceptance Criteria を 1〜3 個置く
  -> そのまま起票 or gh-issue-create へ handoff
```

## 軽量フロー

1. 入力を 1 文で圧縮し、「何を困っているか」と「何を変えたいか」を分ける。
2. 次の最小テンプレに落とす。
3. Acceptance Criteria を 1〜3 個だけ置く。
4. 必要なら `gh issue create` で起票し、重い整形が必要なら `gh-issue-create` に handoff する。

## 最小テンプレ

```markdown
## 背景
- どの作業中に見つかったか

## 問題
- 何が足りないか / どこで迷うか

## 提案
- 最小でどう変えたいか

## Acceptance Criteria
- [ ] 変更後に観測できる結果
```

## 使い分け

| 状況 | 使う skill |
| --- | --- |
| まず忘れないように軽く backlog 化したい | `happy-add-issue` |
| ラベル、匿名化、vertical slice、DoD まで丁寧に整えたい | `gh-issue-create` |
| PR review 中の指摘から follow-up を切り出したい | `gh-pr-respond` -> `happy-add-issue` |
| 改善ループの最後に次の課題を残したい | `loop-engineering` -> `happy-add-issue` |

## 入力例

```text
この skill、導入方法は分かるけど update 手順が見つけづらい。Issue にして。
```

## 出力イメージ

```markdown
Title: 🟢 plugin update 導線: 利用者が更新手順を見つけやすくする

## 背景
- plugin 導入後の運用確認中に見つかった

## 問題
- update 手順が入口 docs から見つけづらい

## 提案
- README または Getting Started に update 導線を追加する

## Acceptance Criteria
- [ ] 利用者が plugin update 手順へ 2 クリック以内で到達できる
```

## 注意点

- タイトル、背景、Acceptance Criteria を盛りすぎない。最初は薄く残し、必要なら `gh-issue-create` で育てる。
- 公開 repo に出す内容は、固有名詞や内部事情をそのまま書かない。
- 今の作業を止めない。Issue 化は「切り出して続ける」ための動作として使う。
