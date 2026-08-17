---
name: happy-add-issue
description: >
  Happy AI Life 関連の skill、agent、docs、運用への意見や改善要望を、
  `RyoMurakami1983/happy_ai_life` の Issue にすばやく起票する入口。こんなときに使う:
  「この skill が分かりづらい」「この導線を直してほしい」のような雑なフィードバックを、母艦 repo の Issue に残したいとき。
---

# Happy Add Issue

Happy Add Issue は、**Happy AI Life への意見窓口**です。
対象は今開発している repo の backlog ではなく、基本的に
`https://github.com/RyoMurakami1983/happy_ai_life/` の Issue です。

短い感想、違和感、改善要望を失わずに残し、必要なら後で母艦 repo 側で具体化できる状態にします。

## ゴール

- Happy AI Life 関連のフィードバックを、母艦 repo の Issue としてすぐ残す。

## 成功条件

- 投稿先が `RyoMurakami1983/happy_ai_life` だと明確に分かる。
- skill / agent / docs / hooks / plugin 導線への意見が、最小限の背景つきで残る。
- gist は個人用の cheat sheet や小さな snippet 共有に限定し、Issue の詳細メモや長い失敗ログの標準置き場にはしないと分かる。
- 今開発中の repo に起票したい場合は `gh-issue-create` へ迷わず切り替えられる。

## こんなときに使う

- 「この skill の説明が分かりづらい」を Happy AI Life に伝えたい
- plugin、README、docs、hook、router の導線改善を提案したい
- 他 repo で使っていて見つけた違和感を、母艦 repo に返したい
- 実装中ではなく、配布物や運用体験への意見をまず 1 件残したい
- 長い detail を Issue 分割や docs / ADR / follow-up Issue に切り出したい

## 使わない場面

- 今開発している repo のバグや改善を、その repo 自体に起票したい
- ラベル、Acceptance Criteria、DoD まで丁寧に整えた実行用 Issue を作りたい
- 既存 Issue の本文を大きく再設計したい

その場合は `gh-issue-create` を使います。

## 使い分け

| 状況 | 使う skill |
| --- | --- |
| Happy AI Life の skill / docs / 運用への意見を母艦 repo に返したい | `happy-add-issue` |
| 今開発中の repo に、その repo の作業 Issue を起票したい | `gh-issue-create` |
| PR review 中の指摘から現 repo の follow-up を切り出したい | `gh-pr-respond` -> `gh-issue-create` |
| 改善ループの最後に Happy AI Life 側への要望を残したい | `loop-engineering` -> `happy-add-issue` |

## 関連 skill

- `gh-issue-create` — 今開発している repo に、その repo の作業 Issue を起票する
- `knowledge-capture` — 公開されうる内容を匿名化観点つきで整理する

## ワークフロー:

```text
rough feedback
 -> 何が困ったかを1文にする
 -> Happy AI Life 向けの改善要望に言い換える
 -> 公開 Issue に何を書くか / follow-up に分けるかを決める
 -> 必要なら文脈補填を 3-6 行で足す
 -> 最小テンプレへ整形
 -> RyoMurakami1983/happy_ai_life に起票
```

## 軽量フロー

1. 入力を 1 文で圧縮し、「どこで困ったか」と「どう変わってほしいか」を分ける。
2. 投稿先が `RyoMurakami1983/happy_ai_life` であることを明示する。
3. 読み手が対象 repo を知らないと困りそうなら、`文脈補填` を 3-6 行で足す。
4. 長い再現ログ、切り分け経緯、証拠メモが必要なら、Issue を分割するか、`docs / ADR / follow-up Issue` のどれに切り出すかを決める。
5. 公開 Issue には固有名詞・private repo 名・顧客名・内部 URL をそのまま書かない。
6. 次の最小テンプレに落とす。
7. 必要なら `gh issue create -R RyoMurakami1983/happy_ai_life` で起票する。
8. 現 repo の実装 Issue にすべきだと分かったら `gh-issue-create` に切り替える。

## 詳細を分ける判断

gist は個人用の cheat sheet や小さな snippet 共有には使えますが、**Happy Add Issue の detail escape hatch には使いません**。
Issue からこぼれる durable detail は、Issue 分割、`docs / ADR / follow-up Issue` のいずれかへ回します。

| 状況 | 既定の置き場 |
| --- | --- |
| 軽い感想 1 件 | そのまま Issue に書く |
| 3-6 行で済む前提説明が必要 | `文脈補填` を足す |
| 長い経緯や別論点が増える | follow-up Issue に分ける |
| 戻しにくい判断理由が出る | ADR または docs へ切り出す |

## 最小テンプレ

```markdown
Title: 🟢 skill 名または導線名: 何を改善してほしいか

投稿先: RyoMurakami1983/happy_ai_life

## 背景
- どの skill / docs / 導線を使っていて気になったか

## 文脈補填
- 対象 repo を知らない読み手に必要な前提を 3-6 行で補う（任意）

## 困りごと
- 何が分かりづらいか / 何が使いにくいか

## こう変わってほしい
- 期待する改善

## 詳細メモ
- 関連 Issue / docs / ADR の path や URL（任意）

## 補足
- 例、再現場面、関連 skill など（任意）
```

## 入力例

```text
domain-modeling は grill-with-docs とのつながりが見えづらい。Happy AI Life 側に Issue として残したい。
```

## 出力イメージ

```markdown
Title: 🟢 domain-modeling: grill-with-docs との接続を分かりやすくする

投稿先: RyoMurakami1983/happy_ai_life

## 背景
- `domain-modeling` の説明を読み、関連 skill とのつながりを確認していた

## 困りごと
- `grill-with-docs` からどう渡るのかが本文だけでは読み取りづらい

## こう変わってほしい
- 接続元と接続先を判断表か導線図で明示してほしい

## 補足
- Happy AI Life の skill 間の関係を初見でも追えるようにしたい
```

## CLI 例

```powershell
gh issue create `
  -R RyoMurakami1983/happy_ai_life `
  --title "🟢 domain-modeling: grill-with-docs との接続を分かりやすくする" `
  --body-file issue.md
```

## 注意点

- この skill の既定の投稿先は **今の作業 repo ではなく** `RyoMurakami1983/happy_ai_life`。
- 現 repo の backlog を切る用途に流用しない。現 repo の Issue は `gh-issue-create` を使う。
- 最初から重い仕様化をしない。まず意見を失わず残し、必要ならこの repo 側で具体化する。
- 公開 Issue なので、他 repo の private 情報や固有名詞はそのまま書かない。
- gist は個人用の cheat sheet や小さな snippet 共有に限定し、Issue の詳細メモや長い失敗ログの標準置き場にはしない。
- detail が長くなる場合は、Issue を分割するか、`docs / ADR / follow-up Issue` へ切り出す。
