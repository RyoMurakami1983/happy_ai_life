# Copilot CLI plugin distribution follow-up scope

## Background

The first plugin-distribution implementation intentionally used the smallest safe distribution path:

```powershell
copilot plugin install RyoMurakami1983/happy_ai_life_coding_Environment:plugins/happy-ai-life
```

This is the current Option A: a direct Copilot CLI plugin install from `plugins/happy-ai-life`.
It moves reusable skills and the narrow `tdd-coder` agent into an isolated plugin package without treating marketplace publication, repo bootstrap automation, plugin hooks, or MCP server work as part of the first change.

Phase 2 promotes that same plugin package through this repository's owner-managed marketplace because Copilot CLI warns that direct repository, URL, and local path installs are deprecated:

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life_coding_Environment
copilot plugin install happy-ai-life@happy-ai-life-marketplace
```

The excluded items are not rejected. They are deferred because each one changes a different boundary:

- **Marketplace publication** changes discovery, metadata, release, and user install paths.
- **MCP server / MCP Registry work** changes the repo from prompt/workflow distribution into tool integration.
- **Plugin hooks** can affect Copilot CLI behavior beyond one target repository.
- **Plugin commands / bootstrap automation** can write into target repositories and must be dry-run-first and reviewable.
- **Generator-based packaging** changes the source-of-truth model between `home-template/.copilot/` and `plugins/happy-ai-life/`.

Keeping these out protects non-destructive behavior and lets reviewers validate the marketplace install path before broader distribution surfaces are added.

## Relationship to current repo-owned marketplace work

Current work should only prove that `plugins/happy-ai-life` is installable and useful through this repository's marketplace manifest.

It may document future paths, but it must not implement them. In particular:

- `plugins/happy-ai-life` remains the curated first distribution surface.
- `home-template/.copilot/` remains the author/trusted-environment bootstrap source.
- repo-local instructions and hooks remain delivered through existing repo bootstrap scripts, not plugin install side effects.
- live `%USERPROFILE%\.copilot\mcp-config.json` remains user-owned and must not be deleted or rewritten.
- Context7 is treated as an external Copilot CLI plugin marketplace path, not as this repository's MCP config sample.

## Future work goal

Future work should make the plugin distribution model easier to discover, install, update, uninstall, and apply to target repositories without weakening the current ownership boundaries.

The desired end state is:

1. reusable personal assets are installed as a plugin;
2. repo-local assets are applied to target repositories with explicit dry-run / apply steps;
3. any MCP work is limited to tool-like integrations, not prompt asset distribution;
4. publication metadata and generated package content are traceable to a clear source of truth.

## Non-goals

The follow-up work should still exclude:

- silently modifying personal Copilot instructions;
- silently modifying or deleting live `%USERPROFILE%\.copilot\mcp-config.json`;
- using MCP Registry as the primary distribution path for skills, agents, instructions, or hooks;
- making plugin install write directly into arbitrary target repositories;
- enabling Git client hooks without explicit user consent;
- treating `.github/instructions/*.instructions.md` as automatically loaded plugin components;
- adding broad tool permissions or secrets requirements to any future MCP server;
- replacing the existing trusted home sync path until an explicit migration decision exists.

## Future items and acceptance criteria

### 1. Public/default marketplace publication

**Purpose**: make `happy-ai-life` discoverable through a public/default Copilot CLI plugin marketplace instead of requiring users to add this repository as an owner-managed marketplace.

The repo-owned marketplace path is the preferred intermediate step:

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life_coding_Environment
copilot plugin install happy-ai-life@happy-ai-life-marketplace
```

**Acceptance criteria / conditions**:

- A repo-owned marketplace manifest exists and is stable before any public/default marketplace submission.
- The marketplace entry points to the same reviewed plugin root: `plugins/happy-ai-life`.
- Metadata includes name, description, repository, versioning approach, and any limitations that affect install behavior.
- Install, list, update if supported, and uninstall are validated from the marketplace path.
- The direct install path remains documented only as a deprecated fallback while Copilot CLI still supports it.
- The publication path does not introduce MCP config, plugin hooks, or repo bootstrap automation implicitly.

### 2. MCP server / MCP Registry work

**Purpose**: expose safe tool-like capabilities, such as repo checks, validators, or sync previews, if they provide value beyond prompt assets.

**Acceptance criteria / conditions**:

- The candidate capability is a tool or integration, not a skill / agent / instruction distribution mechanism.
- Initial tools are read-only or preview-only unless a separate design approves safe apply behavior.
- Tool names are namespaced to avoid collisions.
- Required permissions, file access, network access, and secret handling are documented.
- The MCP server can be installed, disabled, and removed without modifying user-owned `mcp-config.json` unexpectedly.
- MCP Registry submission is evaluated against current GitHub requirements because registry behavior may change.
- Context7 is not implemented as this repo's MCP config. It remains an external plugin marketplace install path.

### 3. Plugin hooks

**Purpose**: decide whether any existing hook behavior belongs in the plugin package rather than repo-local `.github/hooks/`.

**Acceptance criteria / conditions**:

- Copilot CLI plugin hook event semantics are verified with a minimal test plugin before migrating existing hooks.
- Hook scope is documented: plugin-level behavior must not be confused with repo-scoped `.github/hooks/`.
- Only non-mutating or low-risk hooks are considered first.
- Any hook that writes files, blocks tool use, or changes session behavior has an explicit opt-in path and rollback instructions.
- Existing `.github/hooks/` remains the source of truth for repo-scoped hook implementation unless a new ADR changes that boundary.

### 4. Plugin commands / repo bootstrap automation

**Purpose**: provide a plugin-owned command or skill that helps apply repo-local assets to a target repository.

**Acceptance criteria / conditions**:

- The command is dry-run-first and shows exactly which files would be added, updated, archived, or left untouched.
- Apply mode is explicit and separate from install mode.
- `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.github/hooks/`, `.githooks/`, and `.github/.gitignore` behavior is documented per target.
- Git client hooks require explicit consent before changing `core.hooksPath`.
- Existing `scripts/sync-to-repo.ps1` and `scripts/install-git-hooks.ps1` semantics are reused or intentionally superseded with documented reasons.
- Generated target repo changes are reviewable as normal Git diffs.
- Uninstall or rollback guidance exists for files and Git config touched by the bootstrap command.

### 5. Generator-based plugin packaging

**Purpose**: reduce drift between `home-template/.copilot/` and `plugins/happy-ai-life/` by generating or checking the plugin package from a defined source of truth.

**Acceptance criteria / conditions**:

- The source of truth is explicitly declared before generator implementation starts.
- The generator can run in check mode and fail when curated plugin content is stale.
- Generated files do not overwrite user-owned live files.
- Curated exclusions are supported so private, local-only, or unsafe assets are not published accidentally.
- CI or a documented validation command proves generated plugin content matches the source.
- The generator does not hide reviewability: PR diffs must still show meaningful plugin content changes.

## Review checklist for follow-up work

Use this checklist before implementing any deferred item:

- **Source of truth**
  - Is the authoritative source for each asset clear?
  - Does the change create duplicate editable copies?
  - Is drift detectable by tests, scripts, or review steps?

- **Non-destructive behavior**
  - Does install avoid overwriting personal `skills/`, `agents/`, instructions, and live `mcp-config.json`?
  - Does apply mode preserve unknown user files unless explicitly approved?
  - Are archive / rollback paths documented for destructive operations?

- **Distribution paths**
  - Is the path direct plugin install, marketplace install, repo bootstrap, MCP, or trusted home sync?
  - Are personal assets and repo-local assets still separated?
  - Does Context7 remain an external plugin marketplace dependency rather than a bundled MCP config?

- **Install / uninstall**
  - Are install, list, update if applicable, and uninstall commands validated?
  - Does uninstall leave expected user-owned files untouched?
  - Are any remaining repo-local files or Git config changes documented?

- **Validation**
  - Is there a smoke test or manual validation path for the new distribution surface?
  - Are dry-run and apply outputs consistent?
  - Are docs, README, and repo instructions aligned with the actual behavior?
  - Are current GitHub / Copilot CLI docs checked for changed plugin, marketplace, hook, command, or MCP requirements?
