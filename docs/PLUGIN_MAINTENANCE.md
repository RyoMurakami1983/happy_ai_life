# Plugin Maintenance

この文書は `plugins/happy-core/` と `plugins/happy-coding/` に共通する保守ルールです。

## 正本

| 項目 | 正本 |
| --- | --- |
| plugin 内容 | `plugins/happy-core/`, `plugins/happy-coding/` |
| plugin version | `plugins/*/plugin.json` |
| marketplace mirror | `.github/plugin/marketplace.json` |
| local smoke | repository root を local marketplace として追加 |

## pre-merge smoke

PR branch の内容を試す場合は、repository root を local marketplace として追加します。

```powershell
copilot plugin marketplace add ..\..
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
copilot plugin marketplace browse happy-ai-life-marketplace
copilot plugin list
```

cleanup:

```powershell
copilot plugin uninstall happy-core@happy-ai-life-marketplace
copilot plugin uninstall happy-coding@happy-ai-life-marketplace
copilot plugin marketplace remove happy-ai-life-marketplace
```

## version update policy

- typo fix や maintainer-only clarification は version bump を省略してよい。
- skill / agent の改善が利用者体験を変える場合は patch version を上げる。
- version を上げる場合は、`plugins/*/plugin.json` と `.github/plugin/marketplace.json` を同じ PR で更新する。
- 例: `0.2.6 -> 0.2.7` は backward-compatible skill-only improvement に使う。

## 更新を利用者に伝える導線

Copilot CLI plugin の更新取得は `copilot plugin update` を正規導線にします。

```powershell
copilot plugin list
copilot plugin update happy-core@happy-ai-life-marketplace
copilot plugin update happy-coding@happy-ai-life-marketplace
```
