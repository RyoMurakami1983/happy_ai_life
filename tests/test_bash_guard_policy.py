from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GUARD_SCRIPT_PATH = ROOT / ".github" / "hooks" / "scripts" / "guard_pre_tool.sh"
GUARD_POLICY_PATH = ROOT / "policy" / "guard-policy.json"


@lru_cache(maxsize=1)
def _bash_executable() -> str:
    candidates = [
        shutil.which("bash"),
        str(Path(r"C:\Program Files\Git\bin\bash.exe")),
        str(Path(r"C:\Program Files\Git\usr\bin\bash.exe")),
        str(Path(r"C:\Program Files (x86)\Git\bin\bash.exe")),
        str(Path(r"C:\Program Files (x86)\Git\usr\bin\bash.exe")),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if "WindowsApps" in candidate:
            continue
        if not Path(candidate).exists():
            continue
        try:
            probe = subprocess.run(
                [candidate, "-lc", "set -o pipefail >/dev/null 2>&1 && command -v jq >/dev/null 2>&1"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            continue
        if probe.returncode == 0:
            return candidate

    pytest.skip("bash with jq support not found")


def _invoke_bash_guard_pre_tool(
    payload: dict[str, object],
    cwd: Path,
    *,
    stringify_tool_args: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    bash_payload: dict[str, object] = dict(payload)
    tool_args = bash_payload.get("toolArgs")
    if stringify_tool_args and tool_args is not None and not isinstance(tool_args, str):
        bash_payload["toolArgs"] = json.dumps(tool_args)

    effective_env = None
    if env is not None:
        effective_env = {**os.environ, **env}

    bash_path = _bash_executable()
    return subprocess.run(
        [bash_path, "-lc", 'exec "$0" .github/hooks/scripts/guard_pre_tool.sh', bash_path],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        input=json.dumps(bash_payload),
        env=effective_env,
    )


def _init_repo_with_bash_guard(repo: Path) -> None:
    repo.mkdir()
    init = subprocess.run(["git", "init"], cwd=repo, check=False, capture_output=True, text=True)
    assert init.returncode == 0, init.stdout + init.stderr

    hooks_dir = repo / ".github" / "hooks" / "scripts"
    hooks_dir.mkdir(parents=True)
    shutil.copy2(GUARD_SCRIPT_PATH, hooks_dir / "guard_pre_tool.sh")


def _write_policy(repo: Path, policy: dict[str, object]) -> None:
    policy_dir = repo / "policy"
    policy_dir.mkdir(exist_ok=True)
    (policy_dir / "guard-policy.json").write_text(json.dumps(policy), encoding="utf-8")


def _write_maintenance_state(home_root: Path) -> Path:
    state_path = home_root / ".copilot" / "maintenance-mode.json"
    state_path.parent.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    state_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "enabled": True,
                "createdAt": now.isoformat(),
                "expiresAt": (now + timedelta(minutes=30)).isoformat(),
                "scopes": ["protectedPathEdit"],
            }
        ),
        encoding="utf-8",
    )
    return state_path


def test_bash_guard_script_avoids_mapfile_for_bash32_compatibility() -> None:
    content = GUARD_SCRIPT_PATH.read_text(encoding="utf-8")

    assert "mapfile" not in content


def test_bash_guard_pre_tool_uses_policy_shell_tool_names_cross_platform(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    policy["toolNames"]["shell"] = ["terminal"]
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "terminal", "toolArgs": {"command": "git reset --hard HEAD"}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_uses_policy_deny_rule_patterns_cross_platform(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    for rule in policy["denyCommandRules"]:
        if rule["id"] == "git-reset-hard":
            rule["pattern"] = r"\bcustom-danger\b"
            break
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "custom-danger"}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_uses_policy_file_write_tool_names_and_path_properties(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    policy["toolNames"]["fileWrite"] = ["rewrite"]
    policy["pathPropertyNames"] = ["destination"]
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "rewrite",
            "toolArgs": {
                "destination": "policy/guard-policy.json",
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "ask"
    assert "policy/guard-policy.json" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_allows_protected_edit_during_active_maintenance_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home_root = tmp_path / "home"
    _init_repo_with_bash_guard(repo)
    _write_maintenance_state(home_root)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "policy/guard-policy.json",
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
        env={"HOME": str(home_root)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_bash_guard_pre_tool_asks_for_home_managed_path_during_active_maintenance_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home_root = tmp_path / "home"
    _init_repo_with_bash_guard(repo)
    _write_maintenance_state(home_root)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(home_root / ".copilot" / "copilot-instructions.md"),
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
        env={"HOME": str(home_root)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "ask"
    assert "Home-managed Copilot files always require explicit human review" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_normalizes_backslash_directory_policy_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    policy["protectedPaths"].append(
        {
            "id": "backslash-hooks-directory",
            "path": ".github\\hooks\\**",
            "scope": "directory",
            "action": "ask",
            "maintenanceScope": "protectedPathEdit",
        }
    )
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": ".github/hooks/test.json",
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "ask"
    assert ".github/hooks/**" in response["permissionDecisionReason"]


def test_bash_guard_permission_request_denies_maintenance_state_edit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home_root = tmp_path / "home"
    _init_repo_with_bash_guard(repo)
    state_path = _write_maintenance_state(home_root)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(state_path),
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
        env={"HOME": str(home_root), "HAPPY_AI_LIFE_HOOK_EVENT": "permissionRequest"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["behavior"] == "deny"
    assert response["interrupt"] is True
    assert "Maintenance state changes must go through the maintenance scripts" in response["message"]


def test_bash_guard_permission_request_prefers_specific_deny_over_broad_ask_policy_order(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home_root = tmp_path / "home"
    _init_repo_with_bash_guard(repo)
    state_path = _write_maintenance_state(home_root)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    deny_entry = next(entry for entry in policy["protectedPaths"] if entry["path"] == "$HOME/.copilot/maintenance-mode.json")
    broad_entry = next(entry for entry in policy["protectedPaths"] if entry["path"] == "$HOME/.copilot/**")
    remaining_entries = [
        entry
        for entry in policy["protectedPaths"]
        if entry["path"] not in {"$HOME/.copilot/maintenance-mode.json", "$HOME/.copilot/**"}
    ]
    policy["protectedPaths"] = [broad_entry, deny_entry, *remaining_entries]
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(state_path),
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
        env={"HOME": str(home_root), "HAPPY_AI_LIFE_HOOK_EVENT": "permissionRequest"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["behavior"] == "deny"
    assert response["interrupt"] is True
    assert "Maintenance state changes must go through the maintenance scripts" in response["message"]


def test_bash_guard_pre_tool_normalizes_home_backslash_directory_policy_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home_root = tmp_path / "home"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    policy["protectedPaths"].append(
        {
            "id": "home-backslash-hooks-directory",
            "path": "$HOME\\.copilot\\hooks\\**",
            "scope": "directory",
            "action": "ask",
            "maintenanceScope": "protectedPathEdit",
        }
    )
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(home_root / ".copilot" / "hooks" / "test.json"),
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
        env={"HOME": str(home_root)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "ask"
    assert "$HOME/.copilot/hooks/**" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_blocks_remove_item_recurse_force_in_fallback_baseline(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "powershell",
            "toolArgs": {"command": "Remove-Item temp.txt -Recurse -Force"},
        },
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]


def test_bash_guard_permission_request_uses_event_specific_deny_response(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "git push origin main -f"}},
        cwd=repo,
        env={"HAPPY_AI_LIFE_HOOK_EVENT": "permissionRequest"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["behavior"] == "deny"
    assert response["interrupt"] is True
    assert "Blocked potentially destructive command" in response["message"]


@pytest.mark.parametrize(
    "command",
    [
        "ruff format .",
        "git log --format=%H",
    ],
)
def test_bash_guard_pre_tool_allows_safe_format_neighbors(tmp_path: Path, command: str) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": command}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_bash_guard_pre_tool_blocks_disk_format_command(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "format c:"}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]


@pytest.mark.parametrize(
    "command",
    [
        "cmd /c format c:",
        "cmd.exe /c format c:",
        "cmd /c del /s /q /f temp",
        "cmd.exe /c del /q /f /s temp",
        "cmd /c rm -fr /",
        "cmd.exe /c rm -r -f .",
        "sudo rm -fr /",
        "doas rm -r -f .",
        "cmd /c sudo rm -fr /",
        "rm --recursive --force /",
        "rm --force --recursive .",
        "rm -r --force ./",
        "cmd /c rm --recursive --force /",
        "del /s /q /f temp",
        "del /q /f /s temp",
        "rm -fr /",
        "rm -r -f .",
    ],
)
def test_bash_guard_pre_tool_blocks_destructive_command_variants(tmp_path: Path, command: str) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": command}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /tmp/build",
        "sudo rm -rf /tmp/build",
        "rm --recursive --force /tmp/build",
    ],
)
def test_bash_guard_pre_tool_allows_non_root_absolute_rm_targets(tmp_path: Path, command: str) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": command}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    "policy_mutation",
    [
        "duplicate_path_property_name",
        "duplicate_protected_path_id",
        "duplicate_normalized_protected_path",
        "duplicate_deny_rule_id",
    ],
)
def test_bash_guard_pre_tool_falls_back_when_policy_uniqueness_is_invalid(
    tmp_path: Path,
    policy_mutation: str,
) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    policy["toolNames"]["fileWrite"] = ["rewrite"]
    policy["pathPropertyNames"] = ["destination"]
    policy["protectedPaths"].append(
        {
            "id": "custom-protected-file",
            "path": "custom-protected.txt",
            "scope": "file",
            "action": "ask",
            "maintenanceScope": "protectedPathEdit",
        }
    )

    if policy_mutation == "duplicate_path_property_name":
        policy["pathPropertyNames"].append("destination")
    elif policy_mutation == "duplicate_protected_path_id":
        policy["protectedPaths"].append(
            {
                "id": "custom-protected-file",
                "path": "another-custom-protected.txt",
                "scope": "file",
                "action": "ask",
                "maintenanceScope": "protectedPathEdit",
            }
        )
    elif policy_mutation == "duplicate_normalized_protected_path":
        policy["protectedPaths"].append(
            {
                "id": "custom-protected-file-uppercase",
                "path": "CUSTOM-PROTECTED.TXT/",
                "scope": "file",
                "action": "ask",
                "maintenanceScope": "protectedPathEdit",
            }
        )
    elif policy_mutation == "duplicate_deny_rule_id":
        policy["denyCommandRules"].append(dict(policy["denyCommandRules"][0]))

    _write_policy(repo, policy)

    custom_tool_result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "rewrite",
            "toolArgs": {"destination": "custom-protected.txt"},
        },
        cwd=repo,
    )
    assert custom_tool_result.returncode == 0, custom_tool_result.stdout + custom_tool_result.stderr
    assert custom_tool_result.stdout == ""

    fallback_result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "git push origin main -f"}},
        cwd=repo,
    )
    assert fallback_result.returncode == 0, fallback_result.stdout + fallback_result.stderr
    response = json.loads(fallback_result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_falls_back_when_required_specialized_rule_is_missing_cross_platform(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    policy["denyCommandRules"] = [rule for rule in policy["denyCommandRules"] if rule["id"] != "git-push-force"]
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "git push origin main -f"}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]
