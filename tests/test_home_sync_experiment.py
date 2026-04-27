from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import home_sync_experiment as experiment


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "home_sync_experiment.py"


def test_plan_experiment_sync_classifies_copy_update_and_preserve(tmp_path: Path) -> None:
    workspace = experiment.create_demo_workspace(tmp_path)

    actions = experiment.plan_experiment_sync(workspace)
    kinds = {(action.kind, action.item) for action in actions}

    assert ("update-skill", "managed-skill") in kinds
    assert ("copy-skill", "new-skill") in kinds
    assert ("preserve-skill-extra", "local-extra") in kinds
    assert ("update-agent", "review.agent.md") in kinds
    assert ("copy-agent", "nested/triage.agent.md") in kinds
    assert ("preserve-agent-extra", "custom.agent.md") in kinds


def test_apply_sync_actions_updates_home_and_preserves_extra_items(tmp_path: Path) -> None:
    workspace = experiment.create_demo_workspace(tmp_path)
    actions = experiment.plan_experiment_sync(workspace)

    experiment.apply_sync_actions(actions)

    assert (workspace.destination_root / "skills" / "new-skill" / "SKILL.md").read_text(encoding="utf-8") == "# new skill\n"
    assert (workspace.destination_root / "skills" / "managed-skill" / "SKILL.md").read_text(encoding="utf-8") == "# managed v2\n"
    assert (workspace.destination_root / "skills" / "local-extra" / "SKILL.md").read_text(encoding="utf-8") == "# local extra\n"
    assert (workspace.destination_root / "agents" / "review.agent.md").read_text(encoding="utf-8") == "# review v2\n"
    assert (workspace.destination_root / "agents" / "custom.agent.md").read_text(encoding="utf-8") == "# custom extra\n"
    assert (workspace.destination_root / "agents" / "nested" / "triage.agent.md").read_text(encoding="utf-8") == "# triage v1\n"


def test_apply_sync_actions_creates_single_generation_archive(tmp_path: Path) -> None:
    workspace = experiment.create_demo_workspace(tmp_path)
    actions = experiment.plan_experiment_sync(workspace)
    experiment.apply_sync_actions(actions)

    assert (workspace.archive_root / "skills" / "managed-skill" / "SKILL.md").read_text(encoding="utf-8") == "# managed v1\n"
    assert (workspace.archive_root / "agents" / "review.agent.md").read_text(encoding="utf-8") == "# review v1\n"

    (workspace.destination_root / "skills" / "managed-skill" / "SKILL.md").write_text("# managed local v3\n", encoding="utf-8")
    (workspace.destination_root / "skills" / "managed-skill" / "references.txt").write_text("local reference\n", encoding="utf-8")
    (workspace.destination_root / "agents" / "review.agent.md").write_text("# review local v3\n", encoding="utf-8")

    second_actions = experiment.plan_experiment_sync(workspace)
    experiment.apply_sync_actions(second_actions)

    assert (workspace.archive_root / "skills" / "managed-skill" / "SKILL.md").read_text(encoding="utf-8") == "# managed local v3\n"
    assert (workspace.archive_root / "agents" / "review.agent.md").read_text(encoding="utf-8") == "# review local v3\n"


def test_run_demo_cli_outputs_workspace_state(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--workspace", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["workspace"] == str(tmp_path)
    assert any(action["kind"] == "update-skill" for action in payload["actions"])
    assert "skills/managed-skill/SKILL.md" in payload["skills"]
    assert "agents/review.agent.md" in payload["archives"]
