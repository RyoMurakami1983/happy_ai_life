# happy-core Copilot CLI plugin

This directory is the curated marketplace-install package for Happy AI Life core workflows.

Install through this repository's owner-managed marketplace:

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
```

Local filesystem path installs are not supported by the current Copilot CLI plugin spec, and direct repository installs now emit a deprecation warning. Note that `copilot plugin marketplace add <owner>/<repo>` generally reads the marketplace manifest from the default branch, so it will not reflect a PR branch until after merge. To pre-merge smoke test branch changes, add the repository root as a local marketplace instead:

```powershell
copilot plugin marketplace add ..\..
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin marketplace browse happy-ai-life-marketplace
copilot plugin list
```

Cleanup after a smoke test:

```powershell
copilot plugin uninstall happy-core@happy-ai-life-marketplace
copilot plugin marketplace remove happy-ai-life-marketplace
```

## Included assets

- `skills/` — source of truth for reusable Copilot CLI workflows, authoring assets, Git/GitHub operations, and the daily `furikaeri` workflow

This package intentionally does not include MCP server configuration, plugin hooks, plugin commands, or repo-local instructions.
Generic safety hooks are managed by the trusted home sync path through `%USERPROFILE%\.copilot\config.json`, not by plugin install. Plugin hooks remain deferred until hook loading, script path resolution, and coexistence with repo-scoped hooks pass smoke validation through the supported marketplace-based install path.

`sessionStart` / `sessionEnd` based repo-local context continuity is sealed as a default workflow. Use `furikaeri` for explicit daily reflection, with `/chronicle standup` when experimental mode is available and `/share file session` only when a raw session export is intentionally needed.

## Maintainer note

This plugin package is the current authoring source of truth for reusable core skills. `home-template\.copilot\` is intentionally limited to trusted local home bootstrap and does not carry `skills\`, `agents\`, or `docs\`.

When plugin metadata changes, update both this package's `plugin.json` and the marketplace entry in `..\..\.github\plugin\marketplace.json`.

### Version update policy

- typo や maintainer-only の補足だけなら version を上げなくてもよい
- skill 本文だけの変更でも、**利用者体験が変わる改善**なら plugin version を上げる
- version を上げるときは、この package の `plugin.json` と `..\..\.github\plugin\marketplace.json` の両方をそろえる
- 例: `0.1.0 -> 0.1.1` は、skill-only の後方互換な改善に使う

### How users notice updates

公式 docs 上、利用者が新しい plugin 配布を取り込む正規導線は `copilot plugin update` です。更新通知の自動配信は前提にせず、次を案内します。

```powershell
copilot plugin list
copilot plugin update happy-core@happy-ai-life-marketplace
```
