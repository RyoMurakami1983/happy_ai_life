from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUTO_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "quality.yml"
MANUAL_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "quality-full-manual.yml"


def _load_workflow(path: Path) -> dict[str, Any]:
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(workflow, dict)
    return cast(dict[str, Any], workflow)


def test_quality_workflow_is_limited_to_pr_and_main_push() -> None:
    workflow = _load_workflow(AUTO_WORKFLOW_PATH)

    assert workflow["name"] == "Quality Gate"
    assert workflow["on"] == {"pull_request": "", "push": {"branches": ["main"]}}

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    jobs = cast(dict[str, Any], jobs)
    assert "gitleaks" in jobs
    assert "happy-default" in jobs
    assert "full-quality" not in jobs


def test_manual_quality_workflow_is_dispatch_only() -> None:
    workflow = _load_workflow(MANUAL_WORKFLOW_PATH)

    assert workflow["name"] == "Quality Gate / Manual Full Quality"
    assert workflow["on"] == {"workflow_dispatch": ""}

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    jobs = cast(dict[str, Any], jobs)

    full_quality = jobs["full-quality"]
    assert isinstance(full_quality, dict)
    full_quality = cast(dict[str, Any], full_quality)
    assert full_quality["name"] == "full quality (manual)"

    steps = full_quality["steps"]
    assert isinstance(steps, list)

    run_steps = {
        step.get("name"): step.get("run")
        for step in steps
        if isinstance(step, dict) and "name" in step and "run" in step
    }
    assert run_steps["Run tests"] == "uv run python -m pytest -q"
    assert run_steps["Run ruff"] == "uv run ruff check ."
    assert run_steps["Run ty"] == "uv run ty check ."
