from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.guard_policy import EvaluationContext, HookEvent, evaluate_payload


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_home(tmp_path: Path) -> Path:
    return tmp_path / "home"


def _evaluate(
    payload: dict[str, object],
    *,
    hook_event: HookEvent = "preToolUse",
    cwd: Path | None = None,
    repo_root: Path | None = None,
    home: Path,
    policy_path: Path | None = None,
) -> dict[str, object] | None:
    decision = evaluate_payload(
        payload,
        context=EvaluationContext(
            hook_event=hook_event,
            cwd=str(cwd) if cwd is not None else str(ROOT),
            repo_root=str(repo_root) if repo_root is not None else str(ROOT),
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
