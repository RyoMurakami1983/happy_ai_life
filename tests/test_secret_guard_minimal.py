from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.guard_policy import EvaluationContext, HookEvent, evaluate_payload


ROOT = Path(__file__).resolve().parents[1]


def _evaluate(
    payload: dict[str, object], *, home: Path, hook_event: HookEvent = "preToolUse"
) -> dict[str, object] | None:
    decision = evaluate_payload(
        payload,
        context=EvaluationContext(
            hook_event=hook_event,
            cwd=str(ROOT),
            repo_root=str(ROOT),
            home=str(home),
            policy_path=str(ROOT / "policy" / "guard-policy.json"),
        ),
    )
    return decision.render(hook_event)


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


@pytest.mark.parametrize(
    "command",
    [
        "gh gist create note.md --public",
        "gh gist create -p note.md",
        "echo https://github.com/MyOrg/private-repo | gh gist create -",
        'gh api --method POST /gists --raw-field public=true --raw-field description="see 10.0.0.12"',
        'gh api --method POST /gists --raw-field "public=true"',
        "gh api --method=POST /gists --raw-field public=true",
        'gh api --method POST "https://api.github.com/gists" --raw-field public=true',
        "gh api gists -f public=true -F files[a.txt][content]=hello",
        "gh api /gists --field=public=true -F files[a.txt][content]=hello",
    ],
)
def test_guard_asks_for_public_or_inline_sensitive_gist_commands(
    tmp_path: Path, command: str
) -> None:
    response = _evaluate(
        {"toolName": "powershell", "toolArgs": {"command": command}},
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "ask"


def test_guard_asks_for_file_based_secret_gist_review(tmp_path: Path) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {"command": 'gh gist create issue_evidence.md --desc "anonymous memo"'},
        },
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "ask"
    assert response["permissionDecisionReason"] == (
        "Gist command detected. Confirm the gist content is anonymized and safe to share before continuing."
    )


def test_guard_combines_public_and_sensitive_gist_review_reason(tmp_path: Path) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": 'gh api --method POST /gists --raw-field public=true --raw-field description="see 10.0.0.12"'
            },
        },
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "ask"
    reason = response["permissionDecisionReason"]
    assert isinstance(reason, str)
    assert "visibility" in reason
    assert "anonymization" in reason


def test_guard_does_not_treat_github_api_endpoint_as_sensitive_inline_url(
    tmp_path: Path,
) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": "gh api --method POST https://api.github.com/gists --raw-field files[a.txt][content]=hello"
            },
        },
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "ask"
    assert response["permissionDecisionReason"] == (
        "Gist command detected. Confirm the gist content is anonymized and safe to share before continuing."
    )


def test_guard_does_not_treat_quoted_github_api_endpoint_as_sensitive_inline_url(
    tmp_path: Path,
) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {
                "command": 'gh api --method POST "https://api.github.com/gists" --raw-field files[a.txt][content]=hello'
            },
        },
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "ask"
    assert response["permissionDecisionReason"] == (
        "Gist command detected. Confirm the gist content is anonymized and safe to share before continuing."
    )


def test_guard_allows_explicit_read_only_gist_api_commands(tmp_path: Path) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {"command": "gh api --method GET /gists -f per_page=100"},
        },
        home=tmp_path,
    )

    assert response is None


def test_guard_keeps_destructive_command_denied_even_when_gist_review_applies(
    tmp_path: Path,
) -> None:
    response = _evaluate(
        {
            "toolName": "powershell",
            "toolArgs": {"command": "gh gist create note.md ; rm -rf /"},
        },
        home=tmp_path,
    )

    assert response is not None
    assert response["permissionDecision"] == "deny"
