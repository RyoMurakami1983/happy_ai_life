from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MANAGED_MANIFEST_PATH = ROOT_DIR / "home-template" / ".copilot" / "managed-manifest.json"


def test_repo_managed_manifest_lists_home_sync_scope() -> None:
    manifest = json.loads(MANAGED_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["distribution"] == "home-sync-managed-surface"
    assert manifest["managedFiles"] == [
        "copilot-instructions.md",
        "managed-manifest.json",
        "scripts/sync-to-repo.ps1",
        "scripts/install-git-hooks.ps1",
        "scripts/repo-secure-check.ps1",
        "scripts/enter-copilot-maintenance-mode.ps1",
        "scripts/exit-copilot-maintenance-mode.ps1",
        "hooks/scripts/guard_pre_tool.ps1",
    ]
    assert manifest["managedDirectories"] == ["repo-template/"]
    assert manifest["managedEntries"] == [
        {
            "file": "config.json",
            "kind": "hook-entry",
            "id": "happy-ai-life-safety-guard",
            "label": "managed enterprise/global guard",
            "events": ["preToolUse", "permissionRequest"],
        }
    ]
    assert manifest["userOwnedPaths"] == [
        "mcp-config.json",
        "skills/",
        "agents/",
        "docs/",
        "session-state/",
    ]
    assert manifest["userOwnedEntries"] == [
        "config.json: non-managed settings and hook entries"
    ]
