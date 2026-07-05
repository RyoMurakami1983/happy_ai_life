---
name: beginner-readme-ops
description: >
  コマンドは打てるが運用文脈の補完は弱い読者向けに、README の前提、起動、確認、停止、片付けを迷いにくい順序へ整える。 demo / dry-run / production / systemd を含む運用 README を初心者向けに構成したいとき。
---

# Beginner README Ops

Beginner README Ops は、「コマンドは打てるが、どの順で読めば安全かは自分で補完しづらい」読者向けに README を整える skill です。
API 仕様書や設計書ではなく、**実行前提、起動、確認、停止、片付けを誤解しにくい順で置く運用 README** を対象にします。

## ゴール

- 初見の読者が、README だけで安全に起動・確認・停止できる章立てを作る。

## 成功条件

- demo / dry-run / production / systemd のモード差分が混ざらない。
- 起動だけでなく、確認方法・停止方法・片付けが同じ粒度で書かれる。

## こんなときに使う

- demo / dry-run / production / systemd の違いを README へ整理したい
- 起動コマンドだけでなく、停止方法と確認方法まで書き漏れなくしたい
- `.env.sample` のどこを触るかを、初心者が迷いにくい順で並べたい
- Linux server や service 運用の最短導線を README に落としたい

## 使わない場面

- API reference、CLI option 一覧、設計判断の記録
- maintainer 向けの内部 runbook
- skill / agent 自体の authoring 規約

その場合は `copilot-authoring` や通常の docs 更新フローへ戻します。

## ワークフロー:

```text
reader and mode
  -> 前提を固定
  -> モードごとに章を分離
  -> 起動 / 確認 / 停止 / 片付けを並べる
  -> 失敗時に最初に見る場所を置く
```

## 基本の章立て

1. 読者と前提を固定する
2. どのモードを使うか選ばせる
3. 起動コマンドを書く
4. 起動後の確認方法を書く
5. 停止方法を書く
6. 片付け / 元に戻す手順を書く

## モード分離の型

| モード | 読者が最初に知りたいこと |
| --- | --- |
| demo | 今すぐ試せるか、どこまで本番と違うか |
| dry-run | 何が実行されず、何だけ確認できるか |
| production | 常駐条件、監視、永続化、再起動方針 |
| systemd | unit の配置、反映、status、stop、disable |

## README チェックリスト

- 前提ツール、環境変数、必要権限が先に書かれている
- コマンドの直後に「成功したら何が見えるか」がある
- 停止方法が起動方法と同じ粒度で書かれている
- demo / dry-run / production / systemd が同じ節に混ざっていない
- 失敗時にまずどこを見るかが 1 行で分かる

## 最小テンプレ

```markdown
## 想定読者
- コマンド実行はできるが、運用モードの違いは初見

## 事前準備
- 必要ツール
- 変更する設定ファイル

## パス 1: demo
- 起動
- 確認
- 停止

## パス 2: production
- 起動
- 確認
- 停止
- 片付け
```

## 例

```text
README を更新して。demo と production が混ざって読みにくい。systemd の止め方も足したい。
```

この依頼なら、最初に demo / production / systemd を分離し、各節で **起動 → 確認 → 停止** の順へ並べ替えます。

## 使い分け

| 状況 | 使う skill |
| --- | --- |
| README の運用導線を初心者向けに整えたい | `beginner-readme-ops` |
| skill / instructions の設計や境界を整理したい | `copilot-authoring` |
| 実装前に source of truth と用語を確認したい | `interview-with-docs` |

## 注意点

- 章を増やしすぎず、読者が次に打つコマンドを迷わない順を優先する。
- 「何を実行するか」だけでなく、「どう止めるか」を必ず対にする。
- 本番運用の前提が重い場合は、demo / dry-run を先に置いて誤起動を防ぐ。
