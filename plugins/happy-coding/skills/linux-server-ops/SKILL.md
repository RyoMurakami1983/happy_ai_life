---
name: linux-server-ops
description: >
  こんなときに使う: Ubuntu / Linux サーバーに SSH で接続し、sudo、systemd サービス、HTTP 監視を一連で安全に進めたいとき。
  接続前に SSH_AUTH_SOCK を含む認証状態を固定し、認証で止まらずに
  サーバー接続・権限確認・サービス起動・停止・再起動・状態確認を一気に行いたいとき。
---

# Linux Server Ops

Linux Server Ops は、Ubuntu / Linux サーバーの運用を「認証固定 → 接続 → 権限確認 → サービス操作 → 監視」へ分けて進める skill です。実務でよく使う手順を、短い再利用可能な flow としてまとめ、skill 本体だけで扱えるようにします。

## こんなときに使う

- Ubuntu / Linux サーバーへ SSH で接続し、認証状態から権限確認・サービス操作まで一気に進めたいとき
- `SSH_AUTH_SOCK` や `ssh-agent` の状態が怪しく、接続前に切り分けたいとき
- systemd サービスの start / stop / restart / status を安全に実行したいとき
- サーバーの HTTP 監視や簡単な健康確認の入口を作りたいとき

## 原理原則

- SSH 認証の成否は「鍵ファイルの有無」ではなく「**今の shell がどの agent socket を見ているか**」で決まる。
- CLI / agent のコマンド実行は毎回 **fresh process**。前回の実行で使えていた `SSH_AUTH_SOCK` は次の実行へ**引き継がれない**。毎回明示的に固定する。
- パスフレーズ入力などの対話プロンプトで止まりうる操作は、先に**非対話モードで検証**して即失敗させ、切り分けに入る。

## ゴール

- 接続前に SSH 認証状態（socket・agent・鍵登録）を固定する。
- SSH で対象サーバーへ接続し、必要な権限確認を行う。
- systemd サービスの起動・停止・再起動・状態確認を安全に実行する。
- HTTP 監視や簡単な健康確認の入口を持つ。

## 成功条件

- 接続先、ユーザー、ポート、鍵、**使用する agent socket** の前提が明確になっている。
- `echo $SSH_AUTH_SOCK` と `ssh-add -l` による接続前チェックを通過している。
- sudo を必要とする操作と通常ユーザー操作が分けて書かれている。
- `start / stop / restart / status` のどの操作をするかが明確である。
- 失敗時にまず見るログ・確認コマンド・失敗パターン表がある。

## ワークフロー: サーバー運用の短い導線

### ステップ 0 — SSH 認証状態を固定する（接続前チェック・省略禁止）

毎回この順で実行する。fresh process 前提のため「前回動いたから省略」は不可。

~~~bash
# 1. 今の shell が見ている socket を確認
echo $SSH_AUTH_SOCK

# 2. その socket に鍵が入っているか確認
ssh-add -l

# 3. 空・失敗なら候補 socket を総当たりで確認
for s in /tmp/ssh-*/agent.* "$XDG_RUNTIME_DIR/keyring/ssh"; do
  [ -S "$s" ] && { echo "== $s"; SSH_AUTH_SOCK=$s ssh-add -l; }
done
~~~

判定と回復:

- **鍵入り socket が見つかった** → その socket を明示して使う
  ~~~bash
  SSH_AUTH_SOCK=<socket> ssh -p 22 user@host
  ~~~
- **どの socket にも鍵が無い** → agent を起こして鍵を登録し、登録確認まで済ませる
  ~~~bash
  eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519
  ssh-add -l
  ~~~
- **注意**: 秘密鍵がパスフレーズ付きの場合、`-i` で鍵ファイルを直接指定するだけでは不十分。agent への登録（`ssh-add -l` で確認）が必要。

接続テストは非対話で行い、プロンプト待ちで止まらないようにする:

~~~bash
SSH_AUTH_SOCK=<socket> ssh -o BatchMode=yes -o ConnectTimeout=5 -p 22 user@host 'echo ok'
~~~

これが失敗したら、接続に進まず下の失敗パターン表で切り分ける。

### ステップ 1 — 接続前提を固定する

接続先、ユーザー、ポート、鍵、**使用する socket**、sudo の必要性を確認し、最初にやる操作を固定する。

### ステップ 2 — 権限と状態を確認する

`whoami` / `id` / `sudo -v` で権限を確認し、`systemctl status` と `journalctl` でサービス状態を把握する。

### ステップ 3 — 変更と確認を分ける

`start / stop / restart / reload` を実行したら、`status` と `curl` / `ss` / `journalctl` で結果を検証する。

## 注意点

- 接続前に `echo $SSH_AUTH_SOCK` と `ssh-add -l` を確認しないと、認証がどこで止まっているか分かりません。
- `BatchMode=yes` の接続テストを通さずに service 操作に進まないでください。
- sudo が必要な操作は、通常ユーザー操作と分けて実行してください。

## 基本の手順

1. SSH 認証状態を固定する（ステップ 0 を必ず実行）
   - `echo $SSH_AUTH_SOCK` → `ssh-add -l` → 必要なら候補 socket 総当たり
   - `BatchMode=yes` の接続テストが `ok` を返すまで先へ進まない
2. 接続先を確認する
   - host, user, port, key, socket, sudo 可能性を確認する
   - 例: `SSH_AUTH_SOCK=<socket> ssh -p 22 user@host`
3. 権限を確認する
   - `whoami`, `id`, `sudo -v`
4. サービス状態を確認する
   - `systemctl status <service>`
   - `journalctl -u <service> -n 100 --no-pager`
5. 必要な操作を実行する
   - `sudo systemctl start|stop|restart|reload <service>`
6. 健康確認を行う
   - `curl -I http://127.0.0.1:<port>`
   - `ss -ltnp | grep <port>`
   - `ps aux | grep <process>`

## SSH 認証の失敗パターン表

| 症状 | 原因 | 切り分け | 回復 |
| --- | --- | --- | --- |
| `Permission denied (publickey)` かつ `ssh-add -l` が空 |