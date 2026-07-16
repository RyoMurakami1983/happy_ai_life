---
name: linux-update-systemd-deploy
description: >
  こんなときに使う: 既に systemd で動いているサーバー上のアプリを、
  バックアップ・上書き配置・環境変数更新・手動 1 回実行・journal 確認まで
  安全に更新したいとき。
compatibility: "ssh, scp, tar, sudo, systemd, python3"
---

# Systemd 配備更新

このスキルは、すでに systemd 運用に載っているサーバー上のアプリを、停止時間を最小にしながら安全に更新するための手順をまとめたものです。新規構築ではなく、**既存 service / timer を壊さずに中身だけ更新する**流れに寄せます。

## こんなときに使う

このスキルは次のようなときに使います:
- 更新済みの binary や補助ファイルだけを既存 `systemd service + timer` 配備へ反映したい
- `git pull` ではなく `tar` / `scp` ベースで安全に上書きしたい
- バックアップを取ってから本番ディレクトリを更新したい
- 手動で 1 回だけ service を動かして結果を確認したい

## 判断表

| やりたいこと | 判断 | 次にやること |
| --- | --- | --- |
| 鍵 agent で接続できる | そのまま鍵接続を使う | `BatchMode=yes` の疎通確認後に更新へ進む |
| 鍵接続できず、password の一度だけ使用が明示されている | password fallback を使う | 接続確認と sudo 昇格確認を先に通す |
| 本番配置先が git repo ではない | `git pull` を使わない | archive を作って `scp -> backup -> extract` へ切り替える |
| `Type=oneshot` service を手動実行する | `inactive (dead)` を正常候補として扱う | `status=0/SUCCESS` と journal を確認する |

## 関連リソース

- `linux-server-ops` — 認証固定、sudo、systemd 状態確認の共通入口
- `systemctl cat <service>` — 実際の `ExecStart`、`EnvironmentFile`、override を確認する正本
- `journalctl -u <service> -n 50 --no-pager` — 反映結果を最短で確認する入口

## ワークフロー: 既存 systemd 配備の更新

### ステップ 1 — ゴールと成功条件を固定する

先に次を固定します。

- 対象 host / user / port
- 認証方式: 鍵 agent か、**明示的に一度だけ許可された** password 認証か
- sudo が必要か
- service 名 / timer 名
- 配置先ディレクトリ
- env file の配置先
- 今回の目的が「更新後に手動で 1 回実行する」ことか

成功条件は、**既存 timer を維持したまま新しい成果物へ更新され、手動実行 1 回が成功し、journal に成功ログが残ること**です。

### ステップ 2 — 接続方法を固定し、非対話で先に失敗させる

まず `linux-server-ops` と同じく、鍵 agent が使えるかを確認します。`BatchMode=yes` で通らないのに先へ進まないでください。

鍵で通らない場合でも、ユーザーが明示的に一度だけ password 使用を許可したなら、`python3` の疑似端末や `expect` で **接続確認だけ** 先に通します。ここで大事なのは:

- skill や repo に秘密情報を保存しない
- password / passphrase を文書へ埋め込まない
- 通常ユーザー接続と sudo 昇格を分ける

### ステップ 3 — 既存 service の実体を確認する

更新前に、少なくとも次を確認します。

- `systemctl status <service> --no-pager -l`
- `systemctl status <timer> --no-pager -l`（timer がある場合）
- `systemctl cat <service> --no-pager`
- `journalctl -u <service> -n 50 --no-pager`
- 配置先ディレクトリの所有者・書き込み可否
- 配置先が git repo か、単なる展開ディレクトリか
- env file に今回追加が必要な変数があるか

`Type=oneshot` の service では、成功後の `inactive (dead)` は正常です。`failed` と取り違えないでください。

### ステップ 4 — 配布物を最小で固める

ローカルでは既存の build 入口を使って成果物を作り、更新に必要な最小ファイルだけをまとめます。原則は次です。

- 実行に必要な binary / dll / runtime files
- 更新した source や config template
- 必要なら `sql/` や `systemd/` など実行に参照される付帯ファイル
- `.git/` や不要な作業ファイルは含めない

git pull 前提にしないことが重要です。既存サーバー側が git 管理されていない場合、この方が壊れにくいです。

### ステップ 5 — バックアップしてから上書きする

反映時は次の順に進めます。

1. `scp` でアーカイブを一時領域へ送る
2. 配置先ディレクトリ全体を `tar` でバックアップする
3. 配置先へ展開する
4. env file に必要な新規キーを追記、既存キーは必要時だけ置換する

env 更新では、既存の運用値を壊さず **今回必要な差分だけ** 触ります。毎回 `.env.sample` を丸ごと上書きしないでください。

### ステップ 6 — 手動で 1 回実行し、journal まで確認する

更新後は `systemctl start <service>` で手動実行し、次を確認します。

- `systemctl status <service> --no-pager -l`
- `journalctl -u <service> -n 50 --no-pager`
- 必要なら env file の該当キー
- 一時アップロードしたアーカイブの削除
- 退避したバックアップの保存先

成功ログには、送信件数や skipped 件数のような**今回の更新で意味のある差分**が出ているのが望ましいです。

## 注意点

- **認証方式を途中で混ぜない**: 鍵失敗と password fallback を曖昧にすると、どこで詰まったか分からなくなります。接続確認を先に 1 本通してください。
- **oneshot service を failed と誤認しない**: `inactive (dead)` は正常終了後にも出ます。必ず `status=0/SUCCESS` と journal を見ます。
- **git 配備前提で進めない**: 本番配置先が単純展開ディレクトリなら、`git pull` より `backup -> extract` の方が安全です。
- **env を丸ごと置換しない**: 本番値が消える事故を避けるため、必要なキーだけ追加・変更します。
- **秘密情報を skill に入れない**: password、passphrase、token、接続文字列を skill 本文や補助ファイルへ保存しません。

## 失敗パターン表

| 症状 | 原因 | 切り分け | 回復 |
| --- | --- | --- | --- |
| `Permission denied (publickey,password)` | 鍵 agent 不一致、または password 未確認 | `BatchMode=yes` と password 単独接続を分けて試す | 使う認証方式を 1 つに固定してから進む |
| `fatal: not a git repository` | 本番配置先が git 管理されていない | 配置先で `.git` と `git status` を確認する | `git pull` をやめて archive 展開に切り替える |
| service が `failed` になる | env 不足、binary 不整合、権限問題 | `systemctl status` と `journalctl` を直後に確認する | env 追記、成果物再配置、権限修正のどれかへ切り分ける |
| 期待より全件更新される | 差分ロジックや env が未反映 | 直近の journal と env file の追加キーを確認する | 新しい binary / env が本当に展開されたか見直す |
