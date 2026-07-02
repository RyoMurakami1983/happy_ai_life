---
name: linux-server-ops
description: >
  Ubuntu / Linux サーバーに SSH で接続し、sudo、systemd サービス、HTTP 監視を一連で安全に進める。 Use when: サーバー接続・権限確認・サービス起動・停止・再起動・状態確認を一気に行いたいとき。
---

# Linux Server Ops

Linux Server Ops は、Ubuntu / Linux サーバーの運用を「接続 → 権限確認 → サービス操作 → 監視」へ分けて進める skill です。
実務でよく使う手順を、短い再利用可能な flow としてまとめ、skill 本体だけで扱えるようにします。

## ゴール

- SSH で対象サーバーへ接続し、必要な権限確認を行う。
- systemd サービスの起動・停止・再起動・状態確認を安全に実行する。
- HTTP 監視や簡単な健康確認の入口を持つ。

## 成功条件

- 接続先、ユーザー、ポート、鍵の前提が明確になっている。
- sudo を必要とする操作と通常ユーザー操作が分けて書かれている。
- `start / stop / restart / status` のどの操作をするかが明確である。
- 失敗時にまず見るログや確認コマンドがある。

## こんなときに使う

- Ubuntu / Linux サーバーへの SSH 接続手順を整理したい
- systemd の service を起動・停止・再起動したい
- サーバーの状態確認や HTTP 監視を一発で進めたい
- 運用手順を短く skill として再利用したい

## 使わない場面

- Windows サーバーの運用
- Kubernetes / Docker Compose などのコンテナオーケストレーション
- 既存の長い runbook をそのまま skill に押し込むこと

その場合は `beginner-readme-ops` や適切なドキュメント / infra skill へ戻します。

## ワークフロー: サーバー運用の短い導線

### ステップ 1 — 接続前提を固定する

接続先、ユーザー、ポート、鍵、sudo の必要性を確認し、最初にやる操作を固定する。

### ステップ 2 — 権限と状態を確認する

`whoami` / `id` / `sudo -v` で権限を確認し、`systemctl status` と `journalctl` でサービス状態を把握する。

### ステップ 3 — 変更と確認を分ける

`start / stop / restart / reload` を実行したら、`status` と `curl` / `ss` / `journalctl` で結果を検証する。

## 基本の手順

1. 接続先を確認する
   - host, user, port, key, sudo 可能性を確認する
   - 例: `ssh -i ~/.ssh/id_ed25519 user@host -p 22`
2. 権限を確認する
   - `whoami`, `id`, `sudo -v`
3. サービス状態を確認する
   - `systemctl status <service>`
   - `journalctl -u <service> -n 100 --no-pager`
4. 必要な操作を実行する
   - `sudo systemctl start <service>`
   - `sudo systemctl stop <service>`
   - `sudo systemctl restart <service>`
   - `sudo systemctl reload <service>`
5. 健康確認を行う
   - `curl -I http://127.0.0.1:<port>`
   - `ss -ltnp | grep <port>`
   - `ps aux | grep <process>`

## チェックリスト

- 接続先、ユーザー、ポート、鍵が明確か
- `sudo` が必要な操作を明示しているか
- 変更前後に `status` を確認しているか
- ログ確認コマンドを持っているか
- 失敗時の切り分け先が明確か

## 例

```text
Ubuntu サーバーに接続して、nginx を再起動して、HTTP が返るか確認したい。
```

この依頼なら、まず接続先と権限を確認し、`systemctl status nginx` で状態を見て、必要なら `restart` し、`curl` で確認します。

## 使い分け

| 状況 | 使う skill |
| --- | --- |
| README / 運用手順の文書化 | `beginner-readme-ops` |
| skill / agent / instructions の authoring | `copilot-authoring` |
| サーバー接続・systemd・HTTP 監視を一気に進めたい | `linux-server-ops` |
