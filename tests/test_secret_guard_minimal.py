from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.guard_policy import EvaluationContext, evaluate_payload


ROOT = Path(__file__).resolve().parents[1]


def _evaluate(payload: dict[str, object], *, home: Path, hook_event: str = "preToolUse") -> dict[str, object] | None:
    decision = evaluate_payload(
        payload,
        context=EvaluationContext(
            hook_event=hook_event,  # type: ignore[arg-type]
            cwd=str(ROOT),
            repo_root=str(ROOT),
            home=str(home),
            policy_path=str(ROOT / "policy" / "guard-policy.json"),
        ),
    )
    return decision.render(hook_event)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "command",
    [
        "git commit --no-verify -m skip",
        "git push --no-verify origin HEAD",
        "git push --force origin HEAD",
        "git config core.hooksPath .git/hooks",
        "git reset --hard HEAD",
        "rm -rf /",
        "powershell -EncodedCommand SQBFAFgA",
        "Invoke-Expression $payload",
    ],
)
def test_guard_denies_accident_prone_commands(tmp_path: Path, command: str) -> None:
    response = _evaluate(
        {"toolName": "powershell", "toolArgs": {"command": command}},
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/quality.yml",
        ".githooks/pre-commit",
        "policy/guard-policy.json",
    ],
)
def test_guard_asks_for_critical_safety_paths(tmp_path: Path, path: str) -> None:
    response = _evaluate(
        {"toolName": "edit", "toolArgs": {"path": path, "oldString": "old", "newString": "new"}},
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "ask"


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "docs/FAQ.md",
        "plugins/happy-core/skills/git-commit/SKILL.md",
    ],
)
def test_guard_allows_daily_use_docs_and_skills(tmp_path: Path, path: str) -> None:
    response = _evaluate(
        {"toolName": "edit", "toolArgs": {"path": path, "oldString": "old", "newString": "new"}},
        home=tmp_path,
    )

    assert response is None


def test_guard_denies_direct_maintenance_mode_state_edit(tmp_path: Path) -> None:
    state_path = tmp_path / ".copilot" / "maintenance-mode.json"
    state_path.parent.mkdir()
    state_path.write_text(json.dumps({"enabled": False}), encoding="utf-8")

    response = _evaluate(
        {
            "toolName": "edit",
            "toolArgs": {"path": str(state_path), "oldString": "false", "newString": "true"},
        },
        home=tmp_path,
        hook_event="permissionRequest",
    )

    assert response == {
        "behavior": "deny",
        "message": "Protected path change detected for $HOME/.copilot/maintenance-mode.json via edit. Maintenance state changes must go through the maintenance scripts and are denied from Copilot tool edits.",
        "interrupt": True,
    }

