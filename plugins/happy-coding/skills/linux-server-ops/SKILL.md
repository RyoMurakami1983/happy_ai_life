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

## systemd レベルの選択指針

systemd サービスには **system-level** と **user-level** の 2 種類がある。production 環境では原則として **system-level** を使う。

### 選択表（3S 観点）

| 観点 | system-level（`/etc/systemd/system/`） | user-level（`~/.config/systemd/user/`） |
|---|---|---|
| **Security** | `User=` / `Group=` で最小権限ユーザーを指定できる | 起動ユーザーの権限をそのまま引き継ぐ |
| **Stability** | OS 起動時から動作・ログアウト非依存 | `Linger=no` ではログアウト時に停止。`Linger=yes` でも session 依存リスクが残る |
| **Simplicity** | `sudo systemctl` 1 コマンドで全サービスを管理できる | `systemctl --user` が必要で、`sudo journalctl` と混在しやすい |

**結論**: `Linger=yes` を設定しても user-level は session 依存のリスクが残る。production サービスには推奨しない。

### user-level で動いているサービスを発見した場合の是正手順

既存の user-level service を system-level へ移行する手順。

> **前提**: `systemctl --user` は**当該ユーザーの shell で実行する**必要がある。root から実行すると D-Bus に接続できず失敗する。root で SSH 接続している場合は `sudo -iu <user>` でユーザーに切り替えてから実行すること。

~~~bash
# 当該ユーザーで実行する（root なら: sudo -iu <user>）

# 1. 現状確認
systemctl --user status <service>
systemctl --user cat <service>          # ExecStart や EnvironmentFile を確認する

# 2. system-level の unit ファイルを作成する
#    User= / Group= に実行ユーザーを明示し、/etc/systemd/system/<service>.service へ配置する
sudo vi /etc/systemd/system/<service>.service

# 3. user-level を無効化・停止する
systemctl --user stop <service>
systemctl --user disable <service>

# 4. system-level を有効化・起動する
sudo systemctl daemon-reload
sudo systemctl enable --now <service>

# 5. 結果を確認する
sudo systemctl status <service> --no-pager -l
sudo journalctl -u <service> -n 50 --no-pager
~~~

> 移行後は `loginctl show-user <user>` で `Linger=no` のままにしておいてよい（system-level は影響しない）。

## 注意点

- 接続前に `echo $SSH_AUTH_SOCK` と `ssh-add -l` を確認しないと、認証がどこで止まっているか分かりません。
- `BatchMode=yes` の接続テストを通さずに service 操作に進まないでください。
- sudo が必要な操作は、通常ユーザー操作と分けて実行してください。
- **production では system-level systemd を使う**。user-level の service を発見したら、上記の是正手順で移行してください。

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
| `Permission denied (publickey)` かつ `ssh-add -l` が空 | 鍵未登録または agent socket が違う | `echo $SSH_AUTH_SOCK` と `ssh-add -l` を確認する | `ssh-agent` を起動し、鍵を登録して再試行する |
| `Connection timed out` | 接続先・ポート・ネットワーク経路の問題 | `ssh -o BatchMode=yes -o ConnectTimeout=5` で再確認する | 接続先、ポート、ユーザー名、ネットワーク経路を確認する |
| `sudo: a password is required` | sudo 権限が必要だがパスワード未設定 | `whoami` / `id` / `sudo -v` を確認する | sudo が必要な操作はパスワード付き前提で実行する |