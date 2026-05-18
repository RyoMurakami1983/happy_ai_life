from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import pytest

import scripts.guard_policy as guard_policy
from scripts.guard_policy import EvaluationContext, HookEvent, evaluate_payload, resolve_full_path


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_home(tmp_path: Path) -> Path:
    return tmp_path / "home"


def _evaluate(
    payload: dict[str, object],
    *,
    hook_event: HookEvent = "preToolUse",
    cwd: Path | None = ROOT,
    repo_root: Path | None = ROOT,
    home: Path,
    policy_path: Path | None = None,
) -> dict[str, object] | None:
    decision = evaluate_payload(
        payload,
        context=EvaluationContext(
            hook_event=hook_event,
            cwd=str(cwd) if cwd is not None else None,
            repo_root=str(repo_root) if repo_root is not None else None,
            home=str(home),
            policy_path=str(policy_path) if policy_path is not None else None,
        ),
    )
    return decision.render(hook_event)


def _write_maintenance_state(home_root: Path, *, created_at: datetime | None = None, expires_at: datetime | None = None) -> Path:
    now = datetime.now(timezone.utc)
    state_path = home_root / ".copilot" / "maintenance-mode.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "enabled": True,
                "createdAt": (created_at or now).isoformat(),
                "expiresAt": (expires_at or (now + timedelta(minutes=30))).isoformat(),
                "scopes": ["protectedPathEdit"],
            }
        ),
        encoding="utf-8",
    )
    return state_path


def _write_policy(policy_path: Path, policy: dict[str, Any]) -> None:
    policy_path.write_text(json.dumps(policy), encoding="utf-8")


def _default_policy() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ROOT / "policy" / "guard-policy.json").read_text(encoding="utf-8")))


def test_engine_asks_for_protected_edit_path_from_stringified_json(isolated_home: Path) -> None:
    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": json.dumps(
                {
                    "filePath": "docs/HOOKS_GOVERNANCE.md",
                    "oldString": "old",
                    "newString": "new",
                }
            ),
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for docs/HOOKS_GOVERNANCE.md via edit. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_permission_request_falls_through_for_protected_path(isolated_home: Path) -> None:
    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "docs/HOOKS_GOVERNANCE.md",
                "oldString": "old",
                "newString": "new",
            },
        },
        hook_event="permissionRequest",
        home=isolated_home,
    )

    assert response is None


def test_engine_permission_request_denies_maintenance_state_edit(isolated_home: Path) -> None:
    state_path = _write_maintenance_state(isolated_home)

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(state_path),
                "oldString": "{}",
                "newString": '{"enabled":false}',
            },
        },
        hook_event="permissionRequest",
        home=isolated_home,
    )

    assert response == {
        "behavior": "deny",
        "message": "Protected path change detected for $HOME/.copilot/maintenance-mode.json via edit. Maintenance state changes must go through the maintenance scripts and are denied from Copilot tool edits.",
        "interrupt": True,
    }


def test_engine_asks_for_traversed_protected_create_path(isolated_home: Path) -> None:
    response = _evaluate(
        {
            "tool_name": "create",
            "tool_input": {
                "path": "..\\.github\\workflows\\quality.yml",
                "content": "name: test",
            },
        },
        cwd=ROOT / "tests",
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for .github/workflows/** via create. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_infers_repo_root_from_cwd_when_repo_root_missing(isolated_home: Path, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)
    subdir = repo_root / "packages" / "guard"
    subdir.mkdir(parents=True)

    response = _evaluate(
        {
            "tool_name": "create",
            "tool_input": {
                "path": "..\\..\\.github\\workflows\\quality.yml",
                "content": "name: test",
            },
        },
        cwd=subdir,
        repo_root=None,
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for .github/workflows/** via create. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_denies_git_reset_hard(isolated_home: Path) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "git reset --hard HEAD",
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Blocked potentially destructive command: git reset --hard HEAD",
    }


def test_engine_uses_policy_shell_tool_names(isolated_home: Path, tmp_path: Path) -> None:
    policy = _default_policy()
    policy["toolNames"]["shell"] = ["terminal"]
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    response = _evaluate(
        {
            "toolName": "terminal",
            "toolArgs": {
                "command": "git reset --hard HEAD",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Blocked potentially destructive command: git reset --hard HEAD",
    }


def test_engine_uses_policy_deny_rule_patterns(isolated_home: Path, tmp_path: Path) -> None:
    policy = _default_policy()
    for rule in policy["denyCommandRules"]:
        if rule["id"] == "git-reset-hard":
            rule["pattern"] = r"\bcustom-danger\b"
            break
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "custom-danger",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Blocked potentially destructive command: custom-danger",
    }


def test_engine_uses_policy_file_write_tool_names_and_path_properties(isolated_home: Path, tmp_path: Path) -> None:
    policy = _default_policy()
    policy["toolNames"]["fileWrite"] = ["rewrite"]
    policy["pathPropertyNames"] = ["destination"]
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    response = _evaluate(
        {
            "toolName": "rewrite",
            "toolArgs": {
                "destination": "policy/guard-policy.json",
                "oldString": "old",
                "newString": "new",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for policy/guard-policy.json via rewrite. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_normalizes_backslash_directory_policy_path(isolated_home: Path, tmp_path: Path) -> None:
    policy = _default_policy()
    policy["protectedPaths"].append(
        {
            "id": "backslash-hooks-directory",
            "path": ".github\\hooks\\**",
            "scope": "directory",
            "action": "ask",
            "maintenanceScope": "protectedPathEdit",
        }
    )
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": ".github/hooks/test.json",
                "oldString": "old",
                "newString": "new",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for .github/hooks/** via edit. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_normalizes_home_backslash_directory_policy_path(isolated_home: Path, tmp_path: Path) -> None:
    policy = _default_policy()
    policy["protectedPaths"].append(
        {
            "id": "home-backslash-hooks-directory",
            "path": "$HOME\\.copilot\\hooks\\**",
            "scope": "directory",
            "action": "ask",
            "maintenanceScope": "protectedPathEdit",
        }
    )
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(isolated_home / ".copilot" / "hooks" / "test.json"),
                "oldString": "old",
                "newString": "new",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for $HOME/.copilot/hooks/** via edit. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_denies_shell_maintenance_mode_command(isolated_home: Path) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": ".\\scripts\\enter-copilot-maintenance-mode.ps1 -Minutes 30",
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "AI is not allowed to enter or exit maintenance mode, or modify the maintenance state file. Ask a human to run the maintenance scripts manually.",
    }


@pytest.mark.parametrize(
    ("command",),
    [
        ("git commit --no-verify -m \"skip hooks\"",),
        ("git commit -n -m \"skip hooks\"",),
        ("git push origin HEAD --no-verify",),
    ],
)
def test_engine_denies_git_hooks_no_verify_variants(isolated_home: Path, command: str) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": command,
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "AI is not allowed to bypass Git hooks with --no-verify or git commit -n.",
    }


@pytest.mark.parametrize(
    "command",
    [
        "ruff format .",
        "git log --format=%H",
        "rm -rf /tmp/build",
        "sudo rm -rf /tmp/build",
        "rm --recursive --force /tmp/build",
    ],
)
def test_engine_allows_safe_command_neighbors(isolated_home: Path, command: str) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": command,
            },
        },
        home=isolated_home,
    )

    assert response is None


@pytest.mark.parametrize(
    "command",
    [
        "cmd /c format c:",
        "cmd.exe /c format c:",
        "format c:",
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
        'bash -c "rm -rf /"',
        "sh -c 'rm --recursive --force /'",
        'powershell -Command "rm -rf /"',
        "del /s /q /f temp",
        "del /q /f /s temp",
        "rm -fr /",
        "rm -r -f .",
        "Remove-Item temp.txt -Recurse -Force",
    ],
)
def test_engine_blocks_destructive_command_variants(isolated_home: Path, command: str) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": command,
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Blocked potentially destructive command: {command}",
    }


def test_engine_denies_commit_when_staged_secret_scan_finds_secrets(
    isolated_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(guard_policy, "_resolve_secret_scan_repo_root", lambda repo_root, resolution_base: ROOT)
    monkeypatch.setattr(
        guard_policy,
        "_run_staged_secret_scan",
        lambda repo_root: "Potential secrets were detected in staged changes. Commit was blocked before secrets entered Git history.",
    )

    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "git commit -m \"test\"",
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Potential secrets were detected in staged changes. Commit was blocked before secrets entered Git history.",
    }


def test_run_staged_secret_scan_denies_when_git_diff_name_only_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard_policy, "_resolve_gitleaks", lambda: "gitleaks")

    results = iter(
        [
            subprocess.CompletedProcess(args=["git"], returncode=1, stdout=b"", stderr=b""),
            subprocess.CompletedProcess(args=["git"], returncode=1, stdout=b"", stderr=b"fatal"),
        ]
    )

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return next(results)

    monkeypatch.setattr(guard_policy.subprocess, "run", fake_run)

    assert (
        guard_policy._run_staged_secret_scan(ROOT)
        == "Failed to enumerate staged files for AI pre-commit secret scan."
    )


def test_run_staged_secret_scan_denies_when_checkout_index_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard_policy, "_resolve_gitleaks", lambda: "gitleaks")

    results = iter(
        [
            subprocess.CompletedProcess(args=["git"], returncode=1, stdout=b"", stderr=b""),
            subprocess.CompletedProcess(args=["git"], returncode=0, stdout=b"secret.txt\0", stderr=b""),
        ]
    )

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        if "checkout-index" in args:
            raise subprocess.TimeoutExpired(args, timeout=guard_policy.SECRET_SCAN_CHECKOUT_TIMEOUT_SECONDS)
        return next(results)

    monkeypatch.setattr(guard_policy.subprocess, "run", fake_run)

    assert (
        guard_policy._run_staged_secret_scan(ROOT)
        == "Timed out while preparing staged content for AI pre-commit secret scan."
    )


def test_run_staged_secret_scan_denies_when_gitleaks_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard_policy, "_resolve_gitleaks", lambda: "gitleaks")

    results = iter(
        [
            subprocess.CompletedProcess(args=["git"], returncode=1, stdout=b"", stderr=b""),
            subprocess.CompletedProcess(args=["git"], returncode=0, stdout=b"secret.txt\0", stderr=b""),
            subprocess.CompletedProcess(args=["git"], returncode=0, stdout=b"", stderr=b""),
        ]
    )

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        if args[:2] == ["gitleaks", "dir"]:
            raise subprocess.TimeoutExpired(args, timeout=guard_policy.SECRET_SCAN_GITLEAKS_TIMEOUT_SECONDS)
        return next(results)

    monkeypatch.setattr(guard_policy.subprocess, "run", fake_run)

    assert (
        guard_policy._run_staged_secret_scan(ROOT)
        == "Timed out while scanning staged changes for secrets. Commit was blocked before secret scanning could complete."
    )


def test_run_unpushed_secret_scan_denies_when_gitleaks_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard_policy, "_resolve_gitleaks", lambda: "gitleaks")
    monkeypatch.setattr(guard_policy, "_get_unpushed_log_options", lambda repo_root: (["origin/main..HEAD"], "origin/main..HEAD"))

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(args, timeout=guard_policy.SECRET_SCAN_GITLEAKS_TIMEOUT_SECONDS)

    monkeypatch.setattr(guard_policy.subprocess, "run", fake_run)

    assert (
        guard_policy._run_unpushed_secret_scan(ROOT, action_name="git push")
        == "Timed out while scanning commits for secrets. git push was blocked before secret scanning could complete."
    )


def test_secret_scan_subprocess_timeouts_fit_within_wrapper_budget() -> None:
    assert (
        guard_policy.SECRET_SCAN_CHECKOUT_TIMEOUT_SECONDS + guard_policy.SECRET_SCAN_GITLEAKS_TIMEOUT_SECONDS
        < guard_policy.SECRET_SCAN_WRAPPER_TIMEOUT_SECONDS
    )


def test_engine_denies_push_when_unpushed_secret_scan_finds_secrets(
    isolated_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(guard_policy, "_resolve_secret_scan_repo_root", lambda repo_root, resolution_base: ROOT)
    monkeypatch.setattr(
        guard_policy,
        "_run_unpushed_secret_scan",
        lambda repo_root, *, action_name: f"Potential secrets were detected in commits that may be published. {action_name} was blocked.",
    )

    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "git push origin HEAD",
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Potential secrets were detected in commits that may be published. git push was blocked.",
    }


def test_resolve_full_path_preserves_unc_prefix(isolated_home: Path) -> None:
    resolved = resolve_full_path(
        "//SERVER//Share///guards/../policy/guard-policy.json",
        base_path=str(ROOT),
        home=str(isolated_home),
    )

    assert resolved == "//server/share/policy/guard-policy.json"


def test_engine_allows_protected_edit_path_during_active_maintenance_mode(tmp_path: Path) -> None:
    home_root = tmp_path / "home"
    _write_maintenance_state(home_root)

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "docs/HOOKS_GOVERNANCE.md",
                "oldString": "old",
                "newString": "new",
            },
        },
        home=home_root,
    )

    assert response is None


def test_engine_treats_mixed_timezone_maintenance_state_as_inactive(isolated_home: Path) -> None:
    created_at = datetime.now()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    _write_maintenance_state(isolated_home, created_at=created_at, expires_at=expires_at)

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "docs/HOOKS_GOVERNANCE.md",
                "oldString": "old",
                "newString": "new",
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for docs/HOOKS_GOVERNANCE.md via edit. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_keeps_home_copilot_under_ask_during_maintenance_mode(tmp_path: Path) -> None:
    home_root = tmp_path / "home"
    _write_maintenance_state(home_root)

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "$HOME/.copilot/config.json",
                "oldString": "{}",
                "newString": '{"hooks":{}}',
            },
        },
        home=home_root,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for $HOME/.copilot/** via edit. Home-managed Copilot files always require explicit human review, even during maintenance mode.",
    }


def test_engine_uses_generic_deny_reason_for_non_maintenance_protected_path(tmp_path: Path, isolated_home: Path) -> None:
    policy = json.loads((ROOT / "policy" / "guard-policy.json").read_text(encoding="utf-8"))
    for entry in policy["protectedPaths"]:
        if entry["path"] == "docs/HOOKS_GOVERNANCE.md":
            entry["action"] = "deny"
            entry["maintenanceScope"] = None
            break
    else:
        raise AssertionError("docs/HOOKS_GOVERNANCE.md protected path not found")
    policy_path = tmp_path / "guard-policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "docs/HOOKS_GOVERNANCE.md",
                "oldString": "old",
                "newString": "new",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Protected path change detected for docs/HOOKS_GOVERNANCE.md via edit. This protected path is denied from Copilot tool edits.",
    }


def test_engine_prefers_specific_deny_over_broad_ask_policy_order(tmp_path: Path, isolated_home: Path) -> None:
    policy = json.loads((ROOT / "policy" / "guard-policy.json").read_text(encoding="utf-8"))
    deny_entry = next(entry for entry in policy["protectedPaths"] if entry["path"] == "$HOME/.copilot/maintenance-mode.json")
    broad_entry = next(entry for entry in policy["protectedPaths"] if entry["path"] == "$HOME/.copilot/**")
    remaining_entries = [
        entry
        for entry in policy["protectedPaths"]
        if entry["path"] not in {"$HOME/.copilot/maintenance-mode.json", "$HOME/.copilot/**"}
    ]
    policy["protectedPaths"] = [broad_entry, deny_entry, *remaining_entries]
    policy_path = tmp_path / "guard-policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    state_path = _write_maintenance_state(isolated_home)
    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(state_path),
                "oldString": "{}",
                "newString": '{"enabled":false}',
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Protected path change detected for $HOME/.copilot/maintenance-mode.json via edit. Maintenance state changes must go through the maintenance scripts and are denied from Copilot tool edits.",
    }


def test_engine_prefers_deny_across_all_candidate_paths(tmp_path: Path, isolated_home: Path) -> None:
    policy = _default_policy()
    deny_entry = next(entry for entry in policy["protectedPaths"] if entry["path"] == "$HOME/.copilot/maintenance-mode.json")
    broad_entry = next(entry for entry in policy["protectedPaths"] if entry["path"] == "$HOME/.copilot/**")
    remaining_entries = [
        entry
        for entry in policy["protectedPaths"]
        if entry["path"] not in {"$HOME/.copilot/maintenance-mode.json", "$HOME/.copilot/**"}
    ]
    policy["protectedPaths"] = [broad_entry, deny_entry, *remaining_entries]
    policy["pathPropertyNames"] = ["path", "destination"]
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    state_path = _write_maintenance_state(isolated_home)
    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(isolated_home / ".copilot" / "copilot-instructions.md"),
                "destination": str(state_path),
                "oldString": "old",
                "newString": "new",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Protected path change detected for $HOME/.copilot/maintenance-mode.json via edit. Maintenance state changes must go through the maintenance scripts and are denied from Copilot tool edits.",
    }


def test_engine_denies_git_hooks_path_change_with_specific_reason(isolated_home: Path) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "git config core.hooksPath .githooks",
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "AI is not allowed to disable or bypass Git hooks via core.hooksPath changes or git -c core.hooksPath.",
    }


def test_engine_denies_git_update_index_bypass_with_specific_reason(isolated_home: Path) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "git update-index --skip-worktree scripts/guard_policy.py",
            },
        },
        home=isolated_home,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "AI is not allowed to disable or bypass Git hooks via git update-index --skip-worktree or --assume-unchanged.",
    }


def test_engine_invalid_policy_falls_back_to_protected_rule(tmp_path: Path, isolated_home: Path) -> None:
    policy_path = tmp_path / "guard-policy.json"
    policy_path.write_text("{invalid json", encoding="utf-8")

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "home-template/.copilot/config.json",
                "oldString": "{}",
                "newString": '{"hooks":{}}',
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for home-template/.copilot/** via edit. This path requires an atomic issue/PR and explicit human review.",
    }


def test_engine_invalid_policy_uniqueness_falls_back_to_minimal_deny_rules(tmp_path: Path, isolated_home: Path) -> None:
    policy = _default_policy()
    policy["denyCommandRules"].append(dict(policy["denyCommandRules"][0]))
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "git push origin main -f",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Blocked potentially destructive command: git push origin main -f",
    }


def test_engine_missing_required_specialized_rule_falls_back_to_minimal_deny_rules(
    tmp_path: Path, isolated_home: Path
) -> None:
    policy = _default_policy()
    policy["denyCommandRules"] = [rule for rule in policy["denyCommandRules"] if rule["id"] != "git-push-force"]
    policy_path = tmp_path / "guard-policy.json"
    _write_policy(policy_path, policy)

    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": 'bash -c "rm -rf /"',
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "deny",
        "permissionDecisionReason": 'Blocked potentially destructive command: bash -c "rm -rf /"',
    }


def test_engine_invalid_policy_falls_back_to_trust_boundary_protection(tmp_path: Path, isolated_home: Path) -> None:
    policy_path = tmp_path / "guard-policy.json"
    policy_path.write_text("{invalid json", encoding="utf-8")

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": "docs/TRUST_BOUNDARY.md",
                "oldString": "old",
                "newString": "new",
            },
        },
        home=isolated_home,
        policy_path=policy_path,
    )

    assert response == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "Protected path change detected for docs/TRUST_BOUNDARY.md via edit. This path requires an atomic issue/PR and explicit human review.",
    }
