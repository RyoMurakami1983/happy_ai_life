from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal


HookEvent = Literal["preToolUse", "permissionRequest"]
DecisionKind = Literal["allow", "ask", "deny"]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / "policy" / "guard-policy.json"
MAX_MAINTENANCE_TTL = timedelta(minutes=120)
HOME_PREFIXES = ("~/", "~\\", "$HOME/", "$HOME\\", "${HOME}/", "${HOME}\\", "$env:HOME/", "$env:HOME\\")
WINDOWS_DRIVE_PATTERN = re.compile(r"^[a-zA-Z]:/")
SECRET_SCAN_SUBPROCESS_TIMEOUT_SECONDS = 12

REQUIRED_SPECIALIZED_RULE_IDS = {
    "maintenance-mode-manual-only",
    "git-hooks-no-verify",
    "git-hooks-path-change",
    "git-hooks-update-index-bypass",
    "git-push-force",
    "git-commit-secret-scan",
    "git-push-secret-scan",
    "gh-pr-create-secret-scan",
}

MINIMAL_FALLBACK_POLICY_DATA = json.loads(
    r"""
    {
      "schemaVersion": 1,
      "pathPropertyNames": ["path", "filePath", "file_path", "targetPath", "target_path"],
      "toolNames": {
        "shell": ["bash", "powershell"],
        "fileWrite": ["create", "edit"],
        "observe": ["view", "web_fetch"],
        "delegation": ["task"]
      },
      "protectedPaths": [
        {"id": "repo-hooks", "path": ".github/hooks/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "repo-githooks", "path": ".githooks/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "repo-workflows", "path": ".github/workflows/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "repo-instructions-dir", "path": ".github/instructions/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "repo-skills-dir", "path": ".github/skills/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "agents-skills-dir", "path": ".agents/skills/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "claude-skills-dir", "path": ".claude/skills/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "repo-copilot-instructions", "path": ".github/copilot-instructions.md", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "repo-mcp", "path": ".github/mcp.json", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "root-mcp", "path": ".mcp.json", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "gitleaks-config", "path": ".gitleaks.toml", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "security-policy", "path": "SECURITY.md", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "trust-boundary-doc", "path": "docs/TRUST_BOUNDARY.md", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "hooks-governance-doc", "path": "docs/HOOKS_GOVERNANCE.md", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "enterprise-security-review-doc", "path": "docs/ENTERPRISE_SECURITY_REVIEW.md", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "enterprise-security-doc", "path": "docs/ENTERPRISE_SECURITY.md", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "enterprise-security-roadmap-doc", "path": "docs/ISSUE_ROADMAP_ENTERPRISE_SECURITY.md", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "sync-to-home-script", "path": "scripts/sync-to-home.ps1", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "sync-to-repo-script", "path": "scripts/sync-to-repo.ps1", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "repo-secure-check-script", "path": "scripts/repo-secure-check.ps1", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "home-template-copilot-root", "path": "home-template/.copilot/**", "scope": "directory", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "guard-policy-json", "path": "policy/guard-policy.json", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "guard-policy-schema", "path": "policy/guard-policy.schema.json", "scope": "file", "action": "ask", "maintenanceScope": "protectedPathEdit"},
        {"id": "maintenance-mode-state", "path": "$HOME/.copilot/maintenance-mode.json", "scope": "file", "action": "deny", "maintenanceScope": null},
        {"id": "home-copilot-root", "path": "$HOME/.copilot/**", "scope": "directory", "action": "ask", "maintenanceScope": null}
      ],
      "denyCommandRules": [
        {"id": "maintenance-mode-manual-only", "kind": "specialized", "description": "AI must not enter or exit maintenance mode, or edit the maintenance state file."},
        {"id": "git-hooks-no-verify", "kind": "specialized", "description": "Block git commit --no-verify, git commit -n, and git push --no-verify."},
        {"id": "git-hooks-path-change", "kind": "specialized", "description": "Block core.hooksPath writes, unsets, and inline git -c core.hooksPath usage."},
        {"id": "git-hooks-update-index-bypass", "kind": "specialized", "description": "Block git update-index --skip-worktree and --assume-unchanged."},
        {"id": "git-push-force", "kind": "specialized", "description": "Block git push -f, --force, and --force-with-lease."},
        {"id": "git-commit-secret-scan", "kind": "specialized", "description": "Run staged gitleaks scan before git commit."},
        {"id": "git-push-secret-scan", "kind": "specialized", "description": "Run unpushed-commit gitleaks scan before git push."},
        {"id": "gh-pr-create-secret-scan", "kind": "specialized", "description": "Run unpushed-commit gitleaks scan before gh pr create."},
        {"id": "rm-rf-root", "kind": "pattern", "matchAgainst": "normalized", "description": "Block recursive forced rm against root.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*f[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-fr-root", "kind": "pattern", "matchAgainst": "normalized", "description": "Block forced recursive rm against root.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*r[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-r-f-root", "kind": "pattern", "matchAgainst": "normalized", "description": "Block split recursive forced rm against root.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*f[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-f-r-root", "kind": "pattern", "matchAgainst": "normalized", "description": "Block split forced recursive rm against root.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*r[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-rf-dot", "kind": "pattern", "matchAgainst": "normalized", "description": "Block recursive forced rm against current directory.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*f[a-z]*[^;&|]*\\s+\\.\\/?(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-fr-dot", "kind": "pattern", "matchAgainst": "normalized", "description": "Block forced recursive rm against current directory.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*r[a-z]*[^;&|]*\\s+\\.\\/?(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-r-f-dot", "kind": "pattern", "matchAgainst": "normalized", "description": "Block split recursive forced rm against current directory.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*f[a-z]*[^;&|]*\\s+\\.\\/?(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-f-r-dot", "kind": "pattern", "matchAgainst": "normalized", "description": "Block split forced recursive rm against current directory.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*r[a-z]*[^;&|]*\\s+\\.\\/?(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-recursive-force-root", "kind": "pattern", "matchAgainst": "normalized", "description": "Block recursive forced rm with long options against root.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*(?:\\s-[a-z]*r[a-z]*|\\s--recursive)(?=\\s|$|[;&|])[^;&|]*(?:\\s-[a-z]*f[a-z]*|\\s--force)(?=\\s|$|[;&|])[^;&|]*\\s+\\/(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-force-recursive-root", "kind": "pattern", "matchAgainst": "normalized", "description": "Block forced recursive rm with long options against root.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*(?:\\s-[a-z]*f[a-z]*|\\s--force)(?=\\s|$|[;&|])[^;&|]*(?:\\s-[a-z]*r[a-z]*|\\s--recursive)(?=\\s|$|[;&|])[^;&|]*\\s+\\/(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-recursive-force-dot", "kind": "pattern", "matchAgainst": "normalized", "description": "Block recursive forced rm with long options against current directory.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*(?:\\s-[a-z]*r[a-z]*|\\s--recursive)(?=\\s|$|[;&|])[^;&|]*(?:\\s-[a-z]*f[a-z]*|\\s--force)(?=\\s|$|[;&|])[^;&|]*\\s+\\.\\/?(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "rm-force-recursive-dot", "kind": "pattern", "matchAgainst": "normalized", "description": "Block forced recursive rm with long options against current directory.", "pattern": "(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?(?:(?:(?:bash|sh|powershell|pwsh)(?:\\.exe)?)(?:\\s+\\S+)*\\s+-(?:c|lc|command)\\s+(?:\\\"|')?)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*(?:\\s-[a-z]*f[a-z]*|\\s--force)(?=\\s|$|[;&|])[^;&|]*(?:\\s-[a-z]*r[a-z]*|\\s--recursive)(?=\\s|$|[;&|])[^;&|]*\\s+\\.\\/?(?=\\s|$|[;&|]|[\\\"'])"},
        {"id": "windows-del-force-recursive", "kind": "pattern", "matchAgainst": "normalized", "description": "Block recursive forced del regardless of flag order.", "pattern": "(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])"},
        {"id": "windows-del-force-quiet-recursive", "kind": "pattern", "matchAgainst": "normalized", "description": "Block forced quiet recursive del.", "pattern": "(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])"},
        {"id": "windows-del-recursive-force-quiet", "kind": "pattern", "matchAgainst": "normalized", "description": "Block recursive forced quiet del.", "pattern": "(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])"},
        {"id": "windows-del-recursive-quiet-force", "kind": "pattern", "matchAgainst": "normalized", "description": "Block recursive quiet forced del.", "pattern": "(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])"},
        {"id": "windows-del-quiet-force-recursive", "kind": "pattern", "matchAgainst": "normalized", "description": "Block quiet forced recursive del.", "pattern": "(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])"},
        {"id": "windows-del-quiet-recursive-force", "kind": "pattern", "matchAgainst": "normalized", "description": "Block quiet recursive forced del.", "pattern": "(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])"},
        {"id": "format-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block disk format command.", "pattern": "(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?format(?:\\.com|\\.exe)?(?:\\s|$)"},
        {"id": "mkfs-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block mkfs.", "pattern": "\\bmkfs\\b"},
        {"id": "shutdown-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block shutdown.", "pattern": "\\bshutdown\\b"},
        {"id": "reboot-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block reboot.", "pattern": "\\breboot\\b"},
        {"id": "init-zero-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block init 0.", "pattern": "\\binit\\s+0\\b"},
        {"id": "poweroff-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block poweroff.", "pattern": "\\bpoweroff\\b"},
        {"id": "stop-computer-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block Stop-Computer.", "pattern": "\\bstop-computer\\b"},
        {"id": "restart-computer-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block Restart-Computer.", "pattern": "\\brestart-computer\\b"},
        {"id": "remove-item-recurse-force", "kind": "pattern", "matchAgainst": "normalized", "description": "Block Remove-Item -Recurse -Force.", "pattern": "(?=.*\\bremove-item\\b)(?=.*(?:^|\\s)-recurse(?:\\s|$))(?=.*(?:^|\\s)-force(?:\\s|$))"},
        {"id": "git-reset-hard", "kind": "pattern", "matchAgainst": "normalized", "description": "Block git reset --hard.", "pattern": "\\bgit\\s+reset\\s+--hard\\b"},
        {"id": "powershell-encoded-command", "kind": "pattern", "matchAgainst": "normalized", "description": "Block powershell/pwsh -EncodedCommand.", "pattern": "(^|[;&|]\\s*)(?:powershell|pwsh)(?:\\.exe)?(?:\\s+[^;&|]+)*\\s+-(?:encodedcommand|enc|ec)(?=\\s|$|[;&|])"},
        {"id": "invoke-expression", "kind": "pattern", "matchAgainst": "normalized", "description": "Block Invoke-Expression / iex.", "pattern": "(^|[;&|]\\s*)(?:(?:[\\w.\\\\]+\\\\)?invoke-expression|iex)(?=\\s|$|[;&|])"},
        {"id": "powershell-command-invoke-expression", "kind": "pattern", "matchAgainst": "normalized", "description": "Block powershell -Command Invoke-Expression / iex.", "pattern": "(^|[;&|]\\s*)(?:powershell|pwsh)(?:\\.exe)?(?:\\s+[^;&|]+)*\\s+-(?:command|c)\\s+(?:\\\"|')?(?:&\\s*\\{\\s*)?(?:(?:[\\w.\\\\]+\\\\)?invoke-expression|iex)\\b"},
        {"id": "curl-pipe-sh", "kind": "pattern", "matchAgainst": "normalized", "description": "Block curl ... | sh.", "pattern": "\\bcurl(?:\\.exe)?\\b[^;&|]*\\|\\s*sh\\b"},
        {"id": "wget-pipe-sh", "kind": "pattern", "matchAgainst": "normalized", "description": "Block wget ... | sh.", "pattern": "\\bwget(?:\\.exe)?\\b[^;&|]*\\|\\s*sh\\b"}
      ]
    }
    """
)


@dataclass(frozen=True)
class ProtectedPathRule:
    id: str
    path: str
    scope: Literal["file", "directory"]
    action: Literal["ask", "deny"]
    maintenance_scope: str | None


@dataclass(frozen=True)
class DenyCommandRule:
    id: str
    kind: Literal["specialized", "pattern"]
    description: str
    match_against: Literal["normalized", "compact"] | None = None
    pattern: str | None = None


@dataclass(frozen=True)
class ToolNames:
    shell: tuple[str, ...]
    file_write: tuple[str, ...]


@dataclass(frozen=True)
class GuardPolicy:
    path_property_names: tuple[str, ...]
    tool_names: ToolNames
    protected_paths: tuple[ProtectedPathRule, ...]
    deny_command_rules: tuple[DenyCommandRule, ...]


@dataclass(frozen=True)
class GuardDecision:
    kind: DecisionKind
    reason: str | None = None

    def render(self, hook_event: HookEvent) -> dict[str, Any] | None:
        if self.kind == "allow":
            return None
        if self.kind == "deny":
            if hook_event == "permissionRequest":
                return {"behavior": "deny", "message": self.reason, "interrupt": True}
            return {"permissionDecision": "deny", "permissionDecisionReason": self.reason}
        if hook_event == "permissionRequest":
            return None
        return {"permissionDecision": "ask", "permissionDecisionReason": self.reason}


@dataclass(frozen=True)
class HookPayload:
    tool_name: str
    tool_args: Any
    cwd: str | None


@dataclass(frozen=True)
class EvaluationContext:
    hook_event: HookEvent = "preToolUse"
    cwd: str | None = None
    repo_root: str | None = None
    home: str | None = None
    policy_path: str | None = None
    staged_secret_scan_reason: str | None = None
    unpushed_secret_scan_reason_for_push: str | None = None
    unpushed_secret_scan_reason_for_pr: str | None = None


def allow() -> GuardDecision:
    return GuardDecision("allow")


def ask(reason: str) -> GuardDecision:
    return GuardDecision("ask", reason)


def deny(reason: str) -> GuardDecision:
    return GuardDecision("deny", reason)


def _default_home() -> str:
    return str(Path.home())


def _normalize_policy_path_value(path_value: str) -> str:
    normalized = path_value.strip().replace("\\", "/")
    if normalized.endswith("/**"):
        return normalized.lower()
    return normalized.rstrip("/").lower()


def _looks_like_json_string(value: str) -> bool:
    trimmed = value.strip()
    return trimmed.startswith("{") or trimmed.startswith("[")


def _convert_to_hook_object(value: Any, *, parse_json_strings: bool = False) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
        if not parse_json_strings or not _looks_like_json_string(value):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _get_payload_property_value(obj: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name not in obj:
            continue
        value = obj[name]
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def parse_hook_payload(raw_or_payload: str | dict[str, Any]) -> HookPayload | None:
    if isinstance(raw_or_payload, str):
        try:
            parsed = json.loads(raw_or_payload)
        except json.JSONDecodeError:
            return None
    else:
        parsed = raw_or_payload

    if not isinstance(parsed, dict):
        return None

    tool_name_value = _get_payload_property_value(parsed, ("toolName", "tool_name"))
    if not isinstance(tool_name_value, str) or not tool_name_value.strip():
        return None

    tool_args_value = _get_payload_property_value(parsed, ("toolArgs", "tool_input"))
    hook_cwd = _get_payload_property_value(parsed, ("cwd",))
    return HookPayload(
        tool_name=tool_name_value,
        tool_args=_convert_to_hook_object(tool_args_value, parse_json_strings=True),
        cwd=hook_cwd if isinstance(hook_cwd, str) else None,
    )


def _is_string_sequence(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_policy_shape(policy: Any) -> bool:
    if not isinstance(policy, dict) or policy.get("schemaVersion") != 1:
        return False

    path_property_names = policy.get("pathPropertyNames")
    if not _is_string_sequence(path_property_names) or len(path_property_names) != len(set(path_property_names)):
        return False

    tool_names = policy.get("toolNames")
    if not isinstance(tool_names, dict):
        return False
    shell_tool_names = tool_names.get("shell")
    file_write_tool_names = tool_names.get("fileWrite")
    if not _is_string_sequence(shell_tool_names) or not _is_string_sequence(file_write_tool_names):
        return False

    protected_paths = policy.get("protectedPaths")
    if not isinstance(protected_paths, list) or not protected_paths:
        return False
    normalized_paths: set[str] = set()
    protected_ids: set[str] = set()
    for entry in protected_paths:
        if not isinstance(entry, dict):
            return False
        entry_id = entry.get("id")
        path = entry.get("path")
        scope = entry.get("scope")
        action = entry.get("action")
        maintenance_scope = entry.get("maintenanceScope")
        if not isinstance(entry_id, str) or not entry_id.strip():
            return False
        if not isinstance(path, str) or not path.strip():
            return False
        if scope not in {"file", "directory"}:
            return False
        if action not in {"ask", "deny"}:
            return False
        if maintenance_scope is not None and not isinstance(maintenance_scope, str):
            return False
        if action == "deny" and maintenance_scope is not None:
            return False
        if scope == "file" and re.search(r"(?:/|\\)\*\*$", path):
            return False
        if entry_id in protected_ids:
            return False
        normalized_path = _normalize_policy_path_value(path)
        if normalized_path in normalized_paths:
            return False
        protected_ids.add(entry_id)
        normalized_paths.add(normalized_path)

    deny_command_rules = policy.get("denyCommandRules")
    if not isinstance(deny_command_rules, list) or not deny_command_rules:
        return False
    deny_ids: set[str] = set()
    for entry in deny_command_rules:
        if not isinstance(entry, dict):
            return False
        entry_id = entry.get("id")
        kind = entry.get("kind")
        description = entry.get("description")
        if not isinstance(entry_id, str) or not entry_id.strip():
            return False
        if entry_id in deny_ids:
            return False
        if kind not in {"specialized", "pattern"}:
            return False
        if not isinstance(description, str) or not description:
            return False
        if kind == "specialized":
            if "matchAgainst" in entry or "pattern" in entry:
                return False
        else:
            match_against = entry.get("matchAgainst")
            pattern = entry.get("pattern")
            if match_against not in {"normalized", "compact"}:
                return False
            if not isinstance(pattern, str) or not pattern.strip():
                return False
            try:
                re.compile(pattern)
            except re.error:
                return False
        deny_ids.add(entry_id)

    return REQUIRED_SPECIALIZED_RULE_IDS.issubset(deny_ids)


def _build_policy(policy_data: dict[str, Any]) -> GuardPolicy:
    return GuardPolicy(
        path_property_names=tuple(str(name) for name in policy_data["pathPropertyNames"]),
        tool_names=ToolNames(
            shell=tuple(str(name) for name in policy_data["toolNames"]["shell"]),
            file_write=tuple(str(name) for name in policy_data["toolNames"]["fileWrite"]),
        ),
        protected_paths=tuple(
            ProtectedPathRule(
                id=str(entry["id"]),
                path=str(entry["path"]),
                scope=entry["scope"],
                action=entry["action"],
                maintenance_scope=entry["maintenanceScope"] if entry["maintenanceScope"] is None else str(entry["maintenanceScope"]),
            )
            for entry in policy_data["protectedPaths"]
        ),
        deny_command_rules=tuple(
            DenyCommandRule(
                id=str(entry["id"]),
                kind=entry["kind"],
                description=str(entry["description"]),
                match_against=entry.get("matchAgainst"),
                pattern=entry.get("pattern"),
            )
            for entry in policy_data["denyCommandRules"]
        ),
    )


def load_guard_policy(policy_path: str | Path | None = None) -> GuardPolicy:
    candidate = Path(policy_path) if policy_path is not None else DEFAULT_POLICY_PATH
    if candidate.is_file():
        try:
            loaded = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            loaded = None
        if isinstance(loaded, dict) and _validate_policy_shape(loaded):
            return _build_policy(loaded)
    return _build_policy(MINIMAL_FALLBACK_POLICY_DATA)


def _normalize_runtime_path_text(path_value: str) -> str:
    return path_value.strip().replace("\\", "/")


def _split_path_prefix(path_value: str) -> tuple[str, str]:
    if path_value.startswith("//"):
        return "//", path_value[2:]
    drive_match = WINDOWS_DRIVE_PATTERN.match(path_value)
    if drive_match:
        return drive_match.group(0), path_value[3:]
    if path_value.startswith("/"):
        return "/", path_value[1:]
    return "", path_value


def _collapse_path(path_value: str) -> str:
    prefix, remainder = _split_path_prefix(path_value)
    normalized_remainder = re.sub(r"/{2,}", "/", remainder)
    parts: list[str] = []
    for segment in normalized_remainder.split("/"):
        if segment in {"", "."}:
            continue
        if segment == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            elif not prefix:
                parts.append(segment)
            continue
        parts.append(segment)
    joined = "/".join(parts)
    if prefix == "//":
        result = f"//{joined}" if joined else "//"
    elif prefix:
        result = f"{prefix}{joined}" if joined else prefix
    else:
        result = joined or "."
    return result.lower()


def _expand_home_prefix(path_value: str, home: str) -> str:
    if path_value.startswith(HOME_PREFIXES):
        suffix = path_value[2:] if path_value.startswith(("~/", "~\\")) else path_value.split("/", 1)[1] if "/" in path_value else path_value.split("\\", 1)[1]
        return _collapse_path(f"{_normalize_runtime_path_text(home)}/{suffix}")
    if path_value in {"~", "$HOME", "${HOME}", "$env:HOME"}:
        return _collapse_path(_normalize_runtime_path_text(home))
    return path_value


def resolve_full_path(path_value: str, *, base_path: str, home: str) -> str:
    normalized = _expand_home_prefix(_normalize_runtime_path_text(path_value), home)
    if normalized in {"$home", "${home}", "$env:home"}:
        return _collapse_path(_normalize_runtime_path_text(home))
    if normalized.startswith("$home/") or normalized.startswith("${home}/") or normalized.startswith("$env:home/"):
        return _collapse_path(f"{_normalize_runtime_path_text(home)}/{normalized.split('/', 1)[1]}")
    if normalized.startswith("$home\\") or normalized.startswith("${home}\\") or normalized.startswith("$env:home\\"):
        home_suffix = normalized.split("\\", 1)[1]
        return _collapse_path(f"{_normalize_runtime_path_text(home)}/{home_suffix}")
    if normalized.startswith(("/", "//")) or WINDOWS_DRIVE_PATTERN.match(normalized):
        return _collapse_path(normalized)
    return _collapse_path(f"{_normalize_runtime_path_text(base_path)}/{normalized}")


def _resolve_repo_root(repo_root: str | None, resolution_base: str) -> str:
    if repo_root:
        return _collapse_path(_normalize_runtime_path_text(repo_root))

    start_path = Path(resolution_base)
    for candidate in (start_path, *start_path.parents):
        if (candidate / ".git").exists():
            return _collapse_path(_normalize_runtime_path_text(str(candidate)))
    return _collapse_path(_normalize_runtime_path_text(resolution_base))


def _path_within_root(candidate_path: str, root_path: str) -> bool:
    candidate = _collapse_path(candidate_path).rstrip("/")
    root = _collapse_path(root_path).rstrip("/")
    return candidate == root or candidate.startswith(f"{root}/")


def _extract_known_property_paths(value: Any, *, property_names: tuple[str, ...], depth: int = 0) -> list[str]:
    if depth > 64 or value is None:
        return []
    normalized_value = _convert_to_hook_object(value, parse_json_strings=depth == 0)
    if normalized_value is None or isinstance(normalized_value, str):
        return []
    if isinstance(normalized_value, list):
        results: list[str] = []
        for item in normalized_value:
            results.extend(_extract_known_property_paths(item, property_names=property_names, depth=depth + 1))
        return results
    if isinstance(normalized_value, dict):
        results: list[str] = []
        for key, item in normalized_value.items():
            if key in property_names:
                results.extend(_extract_values_from_known_property(item, property_names=property_names, depth=depth + 1))
            else:
                results.extend(_extract_known_property_paths(item, property_names=property_names, depth=depth + 1))
        return results
    return []


def _extract_values_from_known_property(value: Any, *, property_names: tuple[str, ...], depth: int = 0) -> list[str]:
    if depth > 64 or value is None:
        return []
    normalized_value = _convert_to_hook_object(value)
    if normalized_value is None:
        return []
    if isinstance(normalized_value, str):
        return [normalized_value] if normalized_value.strip() else []
    if isinstance(normalized_value, list):
        results: list[str] = []
        for item in normalized_value:
            normalized_item = _convert_to_hook_object(item)
            if isinstance(normalized_item, str):
                if normalized_item.strip():
                    results.append(normalized_item)
            else:
                results.extend(_extract_known_property_paths(normalized_item, property_names=property_names, depth=depth + 1))
        return results
    return _extract_known_property_paths(normalized_value, property_names=property_names, depth=depth + 1)


@dataclass(frozen=True)
class ResolvedProtectedRule:
    rule: ProtectedPathRule
    display: str
    full_path: str


def _get_resolved_protected_rules(policy: GuardPolicy, *, repo_root: str | None, home: str, resolution_base: str) -> tuple[ResolvedProtectedRule, ...]:
    rules: list[ResolvedProtectedRule] = []
    for entry in policy.protected_paths:
        display = _normalize_runtime_path_text(entry.path)
        if display.startswith(("$HOME", "${HOME}", "$env:HOME", "~/", "~\\")):
            base_path = home
        elif repo_root:
            base_path = repo_root
        else:
            base_path = resolution_base
        path_text = display[:-3] if entry.scope == "directory" and display.endswith("/**") else display
        full_path = resolve_full_path(path_text, base_path=base_path, home=home)
        rules.append(ResolvedProtectedRule(rule=entry, display=display, full_path=full_path))
    return tuple(rules)


@dataclass(frozen=True)
class ProtectedPathMatch:
    candidate: str
    resolved_rule: ResolvedProtectedRule


def _find_protected_path_match(candidate_paths: list[str], protected_rules: tuple[ResolvedProtectedRule, ...]) -> ProtectedPathMatch | None:
    best_match: ProtectedPathMatch | None = None
    for candidate in candidate_paths:
        for resolved_rule in protected_rules:
            if resolved_rule.rule.scope == "directory":
                is_match = _path_within_root(candidate, resolved_rule.full_path)
            else:
                is_match = _collapse_path(candidate).rstrip("/") == _collapse_path(resolved_rule.full_path).rstrip("/")
            if not is_match:
                continue
            candidate_match = ProtectedPathMatch(candidate=candidate, resolved_rule=resolved_rule)
            if best_match is None:
                best_match = candidate_match
                continue
            best_action_rank = 1 if best_match.resolved_rule.rule.action == "deny" else 0
            candidate_action_rank = 1 if candidate_match.resolved_rule.rule.action == "deny" else 0
            if candidate_action_rank != best_action_rank:
                if candidate_action_rank > best_action_rank:
                    best_match = candidate_match
                continue
            best_scope_rank = 1 if best_match.resolved_rule.rule.scope == "file" else 0
            candidate_scope_rank = 1 if candidate_match.resolved_rule.rule.scope == "file" else 0
            if candidate_scope_rank != best_scope_rank:
                if candidate_scope_rank > best_scope_rank:
                    best_match = candidate_match
                continue
            if len(candidate_match.resolved_rule.full_path) > len(best_match.resolved_rule.full_path):
                best_match = candidate_match
    return best_match


def _normalize_hook_event(hook_event: str | None) -> HookEvent:
    if hook_event == "permissionRequest":
        return "permissionRequest"
    return "preToolUse"


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _datetimes_share_timezone_style(*values: datetime) -> bool:
    has_aware = any(value.tzinfo is not None for value in values)
    has_naive = any(value.tzinfo is None for value in values)
    return not (has_aware and has_naive)


def is_maintenance_mode_active(*, scope: str | None, home: str, now: datetime | None = None) -> bool:
    if not scope:
        return False
    state_path = Path(home) / ".copilot" / "maintenance-mode.json"
    if not state_path.is_file():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(state, dict):
        return False
    if state.get("schemaVersion") != 1 or state.get("enabled") is not True:
        return False
    scopes = state.get("scopes")
    if not isinstance(scopes, list) or scope not in scopes:
        return False
    created_at = _parse_datetime(state.get("createdAt"))
    expires_at = _parse_datetime(state.get("expiresAt"))
    if created_at is None or expires_at is None:
        return False
    current = now if now is not None else datetime.now(created_at.tzinfo)
    if not _datetimes_share_timezone_style(created_at, expires_at, current):
        return False
    if created_at > current:
        return False
    if expires_at <= created_at:
        return False
    if expires_at > created_at + MAX_MAINTENANCE_TTL:
        return False
    if expires_at > current + MAX_MAINTENANCE_TTL:
        return False
    return expires_at > current


def _rule_enabled(policy: GuardPolicy, rule_id: str) -> bool:
    return any(rule.id == rule_id for rule in policy.deny_command_rules)


def _resolve_secret_scan_repo_root(repo_root: str | None, resolution_base: str) -> Path | None:
    if repo_root is not None:
        candidate = Path(repo_root)
        if (candidate / ".git").exists():
            return candidate

    start_path = Path(resolution_base)
    if start_path.is_file():
        start_path = start_path.parent
    for candidate in (start_path, *start_path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _resolve_gitleaks() -> str | None:
    configured = os.environ.get("GITLEAKS_BIN", "").strip()
    if configured:
        configured_path = Path(configured)
        if configured_path.is_file():
            return str(configured_path)
        resolved = shutil.which(configured)
        if resolved:
            return resolved
        return None
    return shutil.which("gitleaks")


def _gitleaks_config_args(repo_root: Path) -> list[str]:
    config_path = repo_root / ".gitleaks.toml"
    if config_path.is_file():
        return ["--config", str(config_path)]
    return []


def _run_staged_secret_scan(repo_root: Path) -> str | None:
    gitleaks = _resolve_gitleaks()
    if gitleaks is None:
        return "gitleaks is required before AI can run git commit."

    staged_probe = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--cached", "--quiet", "--exit-code"],
        check=False,
        capture_output=True,
    )
    if staged_probe.returncode == 0:
        return None

    staged_files = subprocess.run(
        ["git", "-C", str(repo_root), "-c", "core.quotepath=false", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
        check=False,
        capture_output=True,
    )
    if staged_files.returncode != 0:
        return "Failed to enumerate staged files for AI pre-commit secret scan."
    if not staged_files.stdout:
        return None

    with tempfile.TemporaryDirectory(prefix="copilot-secret-scan-") as scratch_dir:
        snapshot_dir = Path(scratch_dir) / "snapshot"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_prefix = f"{str(snapshot_dir).replace('\\', '/').rstrip('/')}/"
        try:
            checkout = subprocess.run(
                ["git", "-C", str(repo_root), "checkout-index", f"--prefix={snapshot_prefix}", "--stdin", "-z"],
                input=staged_files.stdout,
                check=False,
                capture_output=True,
                timeout=SECRET_SCAN_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return "Timed out while preparing staged content for AI pre-commit secret scan."
        if checkout.returncode != 0:
            return "Failed to prepare staged content for AI pre-commit secret scan."

        try:
            scan = subprocess.run(
                [
                    gitleaks,
                    "dir",
                    str(snapshot_dir),
                    *_gitleaks_config_args(repo_root),
                    "--no-banner",
                    "--redact=100",
                    "--exit-code",
                    "1",
                ],
                check=False,
                capture_output=True,
                timeout=SECRET_SCAN_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return "Timed out while scanning staged changes for secrets. Commit was blocked before secret scanning could complete."
        if scan.returncode != 0:
            return "Potential secrets were detected in staged changes. Commit was blocked before secrets entered Git history."
    return None


def _get_unpushed_log_options(repo_root: Path) -> tuple[list[str], str] | None:
    upstream = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    upstream_name = upstream.stdout.strip() if upstream.returncode == 0 else ""
    if upstream_name:
        rev_list_args = [f"{upstream_name}..HEAD"]
        log_opts = f"{upstream_name}..HEAD"
    else:
        rev_list_args = ["HEAD", "--not", "--remotes"]
        log_opts = "HEAD --not --remotes"

    commits = subprocess.run(
        ["git", "-C", str(repo_root), "rev-list", *rev_list_args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if commits.returncode != 0 or not commits.stdout.strip():
        return None
    return rev_list_args, log_opts


def _run_unpushed_secret_scan(repo_root: Path, *, action_name: str) -> str | None:
    gitleaks = _resolve_gitleaks()
    if gitleaks is None:
        return f"gitleaks is required before AI can run {action_name}."

    log_options = _get_unpushed_log_options(repo_root)
    if log_options is None:
        return None

    _, log_opts_text = log_options
    try:
        scan = subprocess.run(
            [
                gitleaks,
                "git",
                str(repo_root),
                "--log-opts",
                log_opts_text,
                *_gitleaks_config_args(repo_root),
                "--no-banner",
                "--redact=100",
                "--exit-code",
                "1",
            ],
            check=False,
            capture_output=True,
            timeout=SECRET_SCAN_SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"Timed out while scanning commits for secrets. {action_name} was blocked before secret scanning could complete."
    if scan.returncode != 0:
        return f"Potential secrets were detected in commits that may be published. {action_name} was blocked."
    return None


def _evaluate_file_write(payload: HookPayload, *, policy: GuardPolicy, context: EvaluationContext) -> GuardDecision:
    home = context.home or _default_home()
    resolution_base = context.cwd or payload.cwd or str(ROOT)
    repo_root = _resolve_repo_root(context.repo_root, resolution_base)
    path_values = _extract_known_property_paths(payload.tool_args, property_names=policy.path_property_names)
    if not path_values:
        return allow()

    candidate_paths: list[str] = []
    for path_value in dict.fromkeys(path_values):
        normalized = _normalize_runtime_path_text(path_value)
        if repo_root and not (normalized.startswith(("/", "//")) or WINDOWS_DRIVE_PATTERN.match(normalized) or normalized.startswith(HOME_PREFIXES) or normalized.startswith(("$HOME", "${HOME}", "$env:HOME"))):
            candidate_paths.append(resolve_full_path(path_value, base_path=repo_root, home=home))
        candidate_paths.append(resolve_full_path(path_value, base_path=resolution_base, home=home))

    protected_match = _find_protected_path_match(
        candidate_paths,
        _get_resolved_protected_rules(policy, repo_root=repo_root, home=home, resolution_base=resolution_base),
    )
    if protected_match is None:
        return allow()

    display = protected_match.resolved_rule.display
    tool_name = payload.tool_name
    rule = protected_match.resolved_rule.rule
    if rule.action == "deny":
        if rule.id == "maintenance-mode-state":
            return deny(
                f"Protected path change detected for {display} via {tool_name}. "
                "Maintenance state changes must go through the maintenance scripts and are denied from Copilot tool edits."
            )
        return deny(
            f"Protected path change detected for {display} via {tool_name}. "
            "This protected path is denied from Copilot tool edits."
        )
    if context.hook_event == "permissionRequest":
        return allow()
    if display == "$HOME/.copilot/**":
        return ask(
            f"Protected path change detected for {display} via {tool_name}. "
            "Home-managed Copilot files always require explicit human review, even during maintenance mode."
        )
    if is_maintenance_mode_active(scope=rule.maintenance_scope, home=home):
        return allow()
    return ask(
        f"Protected path change detected for {display} via {tool_name}. "
        "This path requires an atomic issue/PR and explicit human review."
    )


def _extract_command(tool_args: Any) -> str | None:
    if isinstance(tool_args, str):
        return tool_args
    if isinstance(tool_args, dict):
        command = tool_args.get("command")
        if isinstance(command, str) and command.strip():
            return command
    return None


def _evaluate_shell(payload: HookPayload, *, policy: GuardPolicy, context: EvaluationContext) -> GuardDecision:
    command = _extract_command(payload.tool_args)
    if command is None or not command.strip():
        return allow()

    normalized = command.strip().lower()
    compact = re.sub(r"\s+", " ", normalized)
    normalized_for_path = normalized.replace("/", "\\")
    maintenance_state_path = str(Path(context.home or _default_home()) / ".copilot" / "maintenance-mode.json").lower()

    touches_maintenance_mode_script = re.search(
        r"(^|[;&|]\s*)(?:\.\s+)?(?:&\s+)?[^;&|]*?(?:enter|exit)-copilot-maintenance-mode(?:\.ps1)?(?=\s|$|[;&|])",
        compact,
    )
    touches_maintenance_state_file = maintenance_state_path.replace("/", "\\") in normalized_for_path or re.search(
        r"maintenance-mode\.json|(?:\$home|\$env:home|\$\{home\}|~)[\\/]\.copilot[\\/](?:[^;&|]*[\\/])?maintenance-mode\.json",
        compact,
    )

    if _rule_enabled(policy, "maintenance-mode-manual-only") and (touches_maintenance_mode_script or touches_maintenance_state_file):
        return deny("AI is not allowed to enter or exit maintenance mode, or modify the maintenance state file. Ask a human to run the maintenance scripts manually.")

    is_git_commit = re.search(r"(^|[;&|]\s*)git\s+commit(\s|$)", compact) is not None
    is_git_push = re.search(r"(^|[;&|]\s*)git\s+push(\s|$)", compact) is not None
    is_gh_pr_create = re.search(r"(^|[;&|]\s*)gh\s+pr\s+create(\s|$)", compact) is not None
    has_no_verify = re.search(r"(^|\s)--no-verify(\s|$)", compact) is not None
    has_commit_n = is_git_commit and re.search(r"(^|\s)-[a-z]*n[a-z]*(\s|$)", compact) is not None
    if _rule_enabled(policy, "git-hooks-no-verify") and ((is_git_commit and (has_no_verify or has_commit_n)) or (is_git_push and has_no_verify)):
        return deny("AI is not allowed to bypass Git hooks with --no-verify or git commit -n.")

    is_git_config_hooks_path_write = re.search(r"(^|[;&|]\s*)git\s+config(\s|$)", compact) and re.search(r"(^|\s)core\.hookspath(?:\s*=\s*|\s+)[^;&|]+", compact)
    is_git_config_hooks_path_unset = re.search(r"(^|[;&|]\s*)git\s+config(?:\s+[^;&|]+)*\s+--unset(?:-all)?(?:\s+[^;&|]+)*\s+core\.hookspath(?=\s*($|[;&|]))", compact)
    is_git_config_remove_core_section = re.search(r"(^|[;&|]\s*)git\s+config(?:\s+[^;&|]+)*\s+--remove-section(?:\s+[^;&|]+)*\s+core(?=\s*($|[;&|]))", compact)
    has_inline_git_hooks_path_config = re.search(r"(^|[;&|]\s*)git(?:\s+[^;&|]+)*\s+-c\s+core\.hookspath(?:\s*=\s*|\s+)[^;&|]+", compact)
    is_git_update_index_skip_worktree = re.search(r"(^|[;&|]\s*)git\s+update-index(\s|$)", compact) and re.search(r"(^|\s)--skip-worktree(\s|$)", compact)
    is_git_update_index_assume_unchanged = re.search(r"(^|[;&|]\s*)git\s+update-index(\s|$)", compact) and re.search(r"(^|\s)--assume-unchanged(\s|$)", compact)

    if _rule_enabled(policy, "git-hooks-path-change") and any(
        value is not None
        for value in (is_git_config_hooks_path_write, is_git_config_hooks_path_unset, is_git_config_remove_core_section, has_inline_git_hooks_path_config)
    ):
        return deny("AI is not allowed to disable or bypass Git hooks via core.hooksPath changes or git -c core.hooksPath.")
    if _rule_enabled(policy, "git-hooks-update-index-bypass") and any(
        value is not None for value in (is_git_update_index_skip_worktree, is_git_update_index_assume_unchanged)
    ):
        return deny("AI is not allowed to disable or bypass Git hooks via git update-index --skip-worktree or --assume-unchanged.")

    has_git_push_force = re.search(
        r"(^|[;&|]\s*)git\s+push(?:\s+[^;&|]+)*\s+(?:-f|--force(?:-with-lease(?:=[^;&|]+)?)?)(?=\s|$|[;&|])",
        compact,
    )
    if _rule_enabled(policy, "git-push-force") and has_git_push_force:
        return deny(f"Blocked potentially destructive command: {command}")

    resolution_base = context.cwd or payload.cwd or str(ROOT)
    secret_scan_repo_root = _resolve_secret_scan_repo_root(context.repo_root, resolution_base)

    if _rule_enabled(policy, "git-commit-secret-scan") and is_git_commit:
        secret_scan_reason = context.staged_secret_scan_reason
        if secret_scan_reason is None and secret_scan_repo_root is not None:
            secret_scan_reason = _run_staged_secret_scan(secret_scan_repo_root)
        if secret_scan_reason is not None:
            return deny(secret_scan_reason)
    if _rule_enabled(policy, "git-push-secret-scan") and is_git_push:
        secret_scan_reason = context.unpushed_secret_scan_reason_for_push
        if secret_scan_reason is None and secret_scan_repo_root is not None:
            secret_scan_reason = _run_unpushed_secret_scan(secret_scan_repo_root, action_name="git push")
        if secret_scan_reason is not None:
            return deny(secret_scan_reason)
    if _rule_enabled(policy, "gh-pr-create-secret-scan") and is_gh_pr_create:
        secret_scan_reason = context.unpushed_secret_scan_reason_for_pr
        if secret_scan_reason is None and secret_scan_repo_root is not None:
            secret_scan_reason = _run_unpushed_secret_scan(secret_scan_repo_root, action_name="gh pr create")
        if secret_scan_reason is not None:
            return deny(secret_scan_reason)

    for rule in policy.deny_command_rules:
        if rule.kind != "pattern" or rule.pattern is None:
            continue
        candidate = compact if rule.match_against == "compact" else normalized
        if re.search(rule.pattern, candidate):
            return deny(f"Blocked potentially destructive command: {command}")
    return allow()


def evaluate_payload(raw_or_payload: str | dict[str, Any], *, context: EvaluationContext | None = None) -> GuardDecision:
    evaluation_context = context or EvaluationContext()
    normalized_context = EvaluationContext(
        hook_event=_normalize_hook_event(evaluation_context.hook_event),
        cwd=evaluation_context.cwd,
        repo_root=evaluation_context.repo_root,
        home=evaluation_context.home or _default_home(),
        policy_path=evaluation_context.policy_path,
        staged_secret_scan_reason=evaluation_context.staged_secret_scan_reason,
        unpushed_secret_scan_reason_for_push=evaluation_context.unpushed_secret_scan_reason_for_push,
        unpushed_secret_scan_reason_for_pr=evaluation_context.unpushed_secret_scan_reason_for_pr,
    )
    payload = parse_hook_payload(raw_or_payload)
    if payload is None:
        return allow()

    policy = load_guard_policy(normalized_context.policy_path)
    if payload.tool_name in policy.tool_names.file_write:
        return _evaluate_file_write(payload, policy=policy, context=normalized_context)
    if payload.tool_name in policy.tool_names.shell:
        return _evaluate_shell(payload, policy=policy, context=normalized_context)
    return allow()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Copilot guard policy decisions.")
    parser.add_argument("--hook-event", choices=("preToolUse", "permissionRequest"), default="preToolUse")
    parser.add_argument("--cwd")
    parser.add_argument("--repo-root")
    parser.add_argument("--home")
    parser.add_argument("--policy-path")
    parser.add_argument("--staged-secret-scan-reason")
    parser.add_argument("--unpushed-secret-scan-reason-for-push")
    parser.add_argument("--unpushed-secret-scan-reason-for-pr")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    decision = evaluate_payload(
        raw,
        context=EvaluationContext(
            hook_event=args.hook_event,
            cwd=args.cwd,
            repo_root=args.repo_root,
            home=args.home,
            policy_path=args.policy_path,
            staged_secret_scan_reason=args.staged_secret_scan_reason,
            unpushed_secret_scan_reason_for_push=args.unpushed_secret_scan_reason_for_push,
            unpushed_secret_scan_reason_for_pr=args.unpushed_secret_scan_reason_for_pr,
        ),
    )
    rendered = decision.render(args.hook_event)
    if rendered is not None:
        sys.stdout.write(json.dumps(rendered, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
