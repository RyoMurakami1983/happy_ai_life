---
name: happy-add-issue
description: >
  Happy AI Life 関連の skill、agent、docs、運用への意見や改善要望を、
  `RyoMurakami1983/happy_ai_life` の Issue にすばやく起票する入口。 Use when:
  「この skill が分かりづらい」「この導線を直してほしい」のような雑なフィードバックを、
  母艦 repo の Issue に残したいとき。
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
- 長い再現メモや失敗ログがある場合に、公開 Issue と分離して **secret gist** を併用できる。
- 公開 Issue と gist の両方で、固有名詞や private 情報を匿名化する既定が分かる。
- 今開発中の repo に起票したい場合は `gh-issue-create` へ迷わず切り替えられる。

## こんなときに使う

- 「この skill の説明が分かりづらい」を Happy AI Life に伝えたい
- plugin、README、docs、hook、router の導線改善を提案したい
- 他 repo で使っていて見つけた違和感を、母艦 repo に返したい
- 実装中ではなく、配布物や運用体験への意見をまず 1 件残したい
- 公開 Issue は軽く保ちつつ、長い再現ログや切り分けメモは gist に逃がしたい

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

## ワークフロー

```text
rough feedback
 -> 何が困ったかを1文にする
 -> Happy AI Life 向けの改善要望に言い換える
 -> 公開 Issue に何を書くか / gist に逃がすかを分ける
 -> 必要なら文脈補填を 3-6 行で足す
 -> 最小テンプレへ整形
 -> RyoMurakami1983/happy_ai_life に起票
```

## 軽量フロー

1. 入力を 1 文で圧縮し、「どこで困ったか」と「どう変わってほしいか」を分ける。
2. 投稿先が `RyoMurakami1983/happy_ai_life` であることを明示する。
3. 読み手が対象 repo を知らないと困りそうなら、`文脈補填` を 3-6 行で足す。
4. 長い再現ログ、切り分け経緯、証拠メモは公開 Issue に詰め込まず、必要なら **secret gist** に分離する。
5. 公開 Issue と gist の両方で、固有名詞・private repo 名・顧客名・内部 URL を一般化する。
6. 次の最小テンプレに落とす。
7. 必要なら `gh issue create -R RyoMurakami1983/happy_ai_life` で起票する。
8. 現 repo の実装 Issue にすべきだと分かったら `gh-issue-create` に切り替える。

## gist を併用する判断

gist は **補助資料** です。Issue 本文を長文化しすぎず、必要な根拠だけを分離したいときに使います。

| 状況 | Issue 本文 | gist |
| --- | --- | --- |
| 軽い感想 1 件 | そのまま書く | 使わない |
| 3-6 行で済む前提説明が必要 | `文脈補填` を足す | 基本使わない |
| 長い失敗ログ、再現メモ、切り分け経緯がある | 要点だけ書く | 使う |
| private repo 名や顧客固有語が多い | 公開 Issue では抽象化する | gist 側も匿名化して使う |

## gist 利用時の既定

- gist を使う場合の既定は **secret gist**。`gh gist create` では `--public` を付けない。
- secret gist でも URL を知る人は読めるため、**機密情報は載せない**。
- gist の本文でも、repo 名、顧客名、サーバー名、内部 URL、内部 ID はそのまま書かない。
- 匿名化は `knowledge-capture` の AC-1〜AC-4 を使う。
- lightweight gist guard がある環境では、gist 作成時に「公開可否」と「匿名化」を人間が再確認する想定で進める。

### 匿名化の最小チェック

1. AC-1: プロジェクト名・会社名・顧客名を消すか汎用名へ置換する
2. AC-2: 実 ID・実フォーマットは、同じ形を保つダミー値へ置換する
3. AC-3: 業界や社内固有の用語を中立語へ一般化する
4. AC-4: 実測値や閾値は代表的なダミー値へ置換する

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
- secret gist の URL や「詳細は gist 参照」の一文（任意）

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

## gist 併用の出力イメージ

```markdown
Title: 🟢 linux-server-ops: 失敗ログを gist で補える導線を足す

投稿先: RyoMurakami1983/happy_ai_life

## 背景
- `linux-server-ops` を使って実サーバー導線を試していた

## 文脈補填
- 対象は Linux サーバーへの SSH 接続、sudo、systemd、HTTP 確認を扱う skill
- 読み手が元 repo や実環境を知らなくても、どの段階で詰まったか分かるよう最小限の前提だけ書く

## 困りごと
- 公開 Issue に長い失敗ログを全部入れると重い
- ただし、再現の根拠は残したい

## こう変わってほしい
- 要点は Issue に、長い証拠は secret gist に分ける導線を本文で案内してほしい

## 詳細メモ
- 詳細な再現ログ: secret gist を参照

## 補足
- gist 本文でも固有名詞は匿名化する
```

## CLI 例

```powershell
gh issue create `
  -R RyoMurakami1983/happy_ai_life `
  --title "🟢 domain-modeling: grill-with-docs との接続を分かりやすくする" `
  --body-file issue.md
```

```powershell
# secret gist が既定。--public は付けない
gh gist create `
  issue_evidence.md `
  --desc "happy-add-issue 用の補助メモ"
```

## 注意点

- この skill の既定の投稿先は **今の作業 repo ではなく** `RyoMurakami1983/happy_ai_life`。
- 現 repo の backlog を切る用途に流用しない。現 repo の Issue は `gh-issue-create` を使う。
- 最初から重い仕様化をしない。まず意見を失わず残し、必要ならこの repo 側で具体化する。
- 公開 Issue なので、他 repo の private 情報や固有名詞はそのまま書かない。
- gist を使う場合も既定は **secret gist**。public gist は「本当に公開してよいか」を再確認する。
- secret gist でも機密情報は載せない。URL を知る人は閲覧できる。
- 匿名化に迷ったら `knowledge-capture` の AC-1〜AC-4 を適用する。
