from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKFLOW_DIRS = (
    ROOT_DIR / ".github" / "workflows",
    ROOT_DIR / "repo-template" / ".github" / "workflows",
)
QUALITY_GATES_PATH = ROOT_DIR / "docs" / "QUALITY_GATES.md"
DEVELOPMENT_PATH = ROOT_DIR / "docs" / "DEVELOPMENT.md"
QUALITY_WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "quality.yml"

USES_PATTERN = re.compile(r"^\s*uses:\s*([^\s#]+)")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def iter_workflow_files() -> list[Path]:
    files: list[Path] = []
    for workflow_dir in WORKFLOW_DIRS:
        if workflow_dir.exists():
            files.extend(sorted(workflow_dir.glob("*.yml")))
            files.extend(sorted(workflow_dir.glob("*.yaml")))
    return files


def test_third_party_actions_are_sha_pinned() -> None:
    violations: list[str] = []

    for workflow_path in iter_workflow_files():
        for line_number, line in enumerate(
            workflow_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            match = USES_PATTERN.match(line)
            if match is None:
                continue

            spec = match.group(1)
            if spec.startswith("./") or spec.startswith("docker://"):
                continue

            action, separator, ref = spec.partition("@")
            if not separator:
                continue

            owner = action.split("/", 1)[0]
            if owner == "actions":
                continue

            if SHA_PATTERN.fullmatch(ref) is None:
                relative_path = workflow_path.relative_to(ROOT_DIR)
                violations.append(f"{relative_path}:{line_number} -> {spec}")

    assert not violations, "third-party actions must use full commit SHA pinning:\n" + "\n".join(violations)


def test_quality_gates_doc_describes_sha_pinning_update_policy() -> None:
    content = QUALITY_GATES_PATH.read_text(encoding="utf-8")

    required_phrases = (
        "full commit SHA で pin",
        "gitleaks/gitleaks-action",
        "upstream tag の SHA",
    )

    for phrase in required_phrases:
        assert phrase in content


def test_quality_workflow_splits_fast_pr_and_full_checks() -> None:
    workflow = yaml.safe_load(QUALITY_WORKFLOW_PATH.read_text(encoding="utf-8"))

    assert isinstance(workflow, dict)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)

    happy_default = jobs.get("happy-default")
    assert isinstance(happy_default, dict)
    assert happy_default.get("name") == "HappyDefault fast checks"
    assert happy_default.get("if") == "github.event_name == 'pull_request'"
    assert happy_default.get("runs-on") == "ubuntu-latest"

    happy_default_steps = {
        step.get("name"): step.get("run")
        for step in happy_default.get("steps", [])
        if isinstance(step, dict) and "name" in step and "run" in step
    }
    assert (
        happy_default_steps.get("Run focused tests")
        == "uv run python -m pytest -q tests/test_guard_policy.py tests/test_guard_policy_engine.py tests/test_workflow_sha_pinning.py"
    )
    assert happy_default_steps.get("Run ruff") == "uv run ruff check ."
    assert happy_default_steps.get("Run ty") == "uv run ty check ."

    hook_parity_smoke = jobs.get("hook-parity-smoke")
    assert isinstance(hook_parity_smoke, dict)
    assert hook_parity_smoke.get("name") == "hook parity smoke"
    assert hook_parity_smoke.get("if") == "github.event_name == 'pull_request'"
    assert hook_parity_smoke.get("runs-on") == "ubuntu-latest"
    smoke_run_steps = {
        step.get("name"): step.get("run")
        for step in hook_parity_smoke.get("steps", [])
        if isinstance(step, dict) and "name" in step and "run" in step
    }
    assert smoke_run_steps.get("Run hook parity tests") == "uv run python -m pytest -q tests/test_git_hooks_secret_guard.py"

    full_quality = jobs.get("full-quality")
    assert isinstance(full_quality, dict)
    assert full_quality.get("name") == "full quality"
    assert full_quality.get("if") == "github.event_name != 'pull_request'"
    full_quality_steps = {
        step.get("name"): step.get("run")
        for step in full_quality.get("steps", [])
        if isinstance(step, dict) and "name" in step and "run" in step
    }
    assert full_quality_steps.get("Run tests") == "uv run python -m pytest -q"
    assert full_quality_steps.get("Run ruff") == "uv run ruff check ."
    assert full_quality_steps.get("Run ty") == "uv run ty check ."

    hook_parity = jobs.get("hook-parity-full")
    assert isinstance(hook_parity, dict)
    assert hook_parity.get("name") == "hook parity full (${{ matrix.os }})"
    assert hook_parity.get("if") == "github.event_name != 'pull_request'"
    assert hook_parity.get("runs-on") == "${{ matrix.os }}"

    strategy = hook_parity.get("strategy")
    assert isinstance(strategy, dict)
    assert strategy.get("fail-fast") is False

    matrix = strategy.get("matrix")
    assert isinstance(matrix, dict)
    assert matrix.get("os") == ["ubuntu-latest", "macos-latest", "windows-latest"]

    steps = hook_parity.get("steps")
    assert isinstance(steps, list)

    uses_steps = [step.get("uses") for step in steps if isinstance(step, dict)]
    assert "actions/checkout@v4" in uses_steps
    assert "actions/setup-python@v5" in uses_steps

    setup_python = next(step for step in steps if isinstance(step, dict) and step.get("uses") == "actions/setup-python@v5")
    with_config = setup_python.get("with")
    assert isinstance(with_config, dict)
    assert with_config.get("python-version") == "3.14"

    run_steps = {
        step.get("name"): step.get("run")
        for step in steps
        if isinstance(step, dict) and "name" in step and "run" in step
    }
    assert run_steps.get("Install uv") == "python -m pip install uv==0.9.15"
    assert run_steps.get("Sync dev dependencies") == "uv sync --dev --frozen"
    assert run_steps.get("Run hook parity tests") == "uv run python -m pytest -q tests/test_git_hooks_secret_guard.py"


def test_docs_describe_hook_parity_ci_and_local_command() -> None:
    quality_gates = QUALITY_GATES_PATH.read_text(encoding="utf-8")
    development = DEVELOPMENT_PATH.read_text(encoding="utf-8")

    for phrase in (
        "hook parity",
        "`tests/test_git_hooks_secret_guard.py`",
        "manual workflow",
        "uv run python -m pytest -q tests/test_git_hooks_secret_guard.py",
    ):
        assert phrase in quality_gates

    assert "uv run python -m pytest -q tests/test_git_hooks_secret_guard.py" in development
    assert "`hook parity smoke`" in development
