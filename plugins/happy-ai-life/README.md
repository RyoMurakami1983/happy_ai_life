# happy-ai-life Copilot CLI plugin

This directory is the curated marketplace-install package for the reusable Happy AI Life Copilot CLI assets.

Install through this repository's owner-managed marketplace:

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life_coding_Environment
copilot plugin install happy-ai-life@happy-ai-life-marketplace
```

Local filesystem path installs are not supported by the current Copilot CLI plugin spec, and direct repository installs now emit a deprecation warning. For local development, validate the package structure and smoke test the marketplace install after pushing a branch:

```powershell
copilot plugin marketplace browse happy-ai-life-marketplace
copilot plugin list
```

Cleanup after a smoke test:

```powershell
copilot plugin uninstall happy-ai-life@happy-ai-life-marketplace
copilot plugin marketplace remove happy-ai-life-marketplace
```

## Included assets

- `skills/` — copied from `home-template\.copilot\skills\`
- `agents/` — copied from `home-template\.copilot\agents\`, including `tdd-coder.agent.md`

This first package intentionally does not include MCP server configuration, plugin hooks, plugin commands, or repo-local instructions.

## Maintainer note

`home-template\.copilot\skills\` and `home-template\.copilot\agents\` remain the current authoring sources of truth. Until a generator or sync script is added, keep this plugin package aligned manually whenever those source assets change.

When plugin metadata changes, update both this package's `plugin.json` and the marketplace entry in `..\..\.github\plugin\marketplace.json`.
