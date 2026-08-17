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

PR branch の内容を試す場合は、**repository root で** local marketplace を追加します。

```powershell
copilot plugin marketplace add .
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

Windows で `Access denied` / `アクセスが拒否されました` が出ても、public docs 上の primary path は update のまま維持します。  
ただし maintainer がこの repo を clone 済みなら、**先に VS Code を完全に閉じて同じ update を再試行**してください。まだ失敗する場合だけ、safe fallback として次を使えます。

```powershell
uv run app.py plugin-repair --dry-run --no-interactive
uv run app.py plugin-repair --yes --no-interactive
```

この command は `happy-core` / `happy-coding` の backup を取ってから reinstall し、install 失敗時は backup から restore を試みます。
