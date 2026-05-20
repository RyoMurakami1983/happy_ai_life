# Plugin versioning for authoring

`copilot-authoring` で version 判断を行うのは、**対象の skill / agent が `plugins/*` 配下で plugin 配布されている場合だけ**です。

## 基本ルール

- 個別 plugin version の正本は `plugins/<plugin>/plugin.json`
- `.github/plugin/marketplace.json` は配布メタ情報をそろえる mirror
- version を上げるときは両方を一致させる

## いつ version を上げるか

- typo や maintainer-only の補足だけなら通常は上げない
- skill / agent 本文だけの変更でも、**利用者体験が変わる改善**なら上げる
- 後方互換な改善なら `0.1.0 -> 0.1.1` のような patch 更新でよい

## 利用者への案内

利用者が更新を知る手段と取得手段は次です。

```powershell
copilot plugin list
copilot plugin update happy-core@happy-ai-life-marketplace
copilot plugin update happy-coding@happy-ai-life-marketplace
```
