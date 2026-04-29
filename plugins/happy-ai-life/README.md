# happy-ai-life Copilot CLI plugin

This directory is the curated direct-install package for the reusable Happy AI Life Copilot CLI assets.

Copilot CLI installs plugins from marketplaces, GitHub repositories, Git URLs, or GitHub repository subdirectories. After this package is pushed to GitHub, install from the repository subdirectory:

```powershell
copilot plugin install RyoMurakami1983/happy_ai_life_coding_Environment:plugins/happy-ai-life
```

Local filesystem path installs are not supported by the current Copilot CLI plugin spec. For local development, validate the package structure and smoke test the GitHub subdirectory install after pushing a branch:

```powershell
copilot plugin list
```

## Included assets

- `skills/` — copied from `home-template\.copilot\skills\`
- `agents/` — copied from `home-template\.copilot\agents\`, including `tdd-coder.agent.md`

This first package intentionally does not include MCP server configuration, plugin hooks, plugin commands, or repo-local instructions.

## Maintainer note

`home-template\.copilot\skills\` and `home-template\.copilot\agents\` remain the current authoring sources of truth. Until a generator or sync script is added, keep this plugin package aligned manually whenever those source assets change.
