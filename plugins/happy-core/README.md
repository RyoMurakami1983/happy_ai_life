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

- `skills/` — source of truth for reusable Copilot CLI workflows, authoring assets, Git/GitHub operations, Loop Engineering, and the daily `furikaeri` workflow

This package intentionally does not include MCP server configuration, plugin hooks, plugin commands, or repo-local instructions.
Generic safety hooks are managed by the trusted home sync path through `%USERPROFILE%\.copilot\config.json`, not by plugin install. Plugin hooks remain deferred until hook loading, script path resolution, and coexistence with repo-scoped hooks pass smoke validation through the supported marketplace-based install path.

`sessionStart` / `sessionEnd` based repo-local context continuity is sealed as a default workflow. Use `furikaeri` for explicit daily reflection, with `/chronicle standup` when experimental mode is available and `/share file session` only when a raw session export is intentionally needed.

## Maintainer note

This plugin package is the current authoring source of truth for reusable core skills. `home-template\.copilot\` is intentionally limited to trusted local home bootstrap and does not carry `skills\`, `agents\`, or `docs\`.

When plugin metadata changes, update both this package's `plugin.json` and the marketplace entry in `..\..\.github\plugin\marketplace.json`.

### Version update policy

- You can usually skip a version bump for typo fixes or maintainer-only clarifications.
- Even for skill-only changes, bump the plugin version when the improvement changes the user experience.
- When bumping the version, keep this package's `plugin.json` and `..\..\.github\plugin\marketplace.json` in sync.
- For example, `0.1.0 -> 0.1.1` fits backward-compatible skill-only improvements.

### How users notice updates

The official user path for picking up a newer plugin distribution is `copilot plugin update`. Do not assume automatic update notifications; instead, point users to:

```powershell
copilot plugin list
copilot plugin update happy-core@happy-ai-life-marketplace
```
