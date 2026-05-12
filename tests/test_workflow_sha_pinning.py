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
        "git ls-remote https://github.com/gitleaks/gitleaks-action",
        "Dependabot",
        "`github-actions` ecosystem",
        "人間レビュー",
    )

    for phrase in required_phrases:
        assert phrase in content


def test_quality_workflow_runs_hook_parity_matrix() -> None:
    workflow = yaml.safe_load(QUALITY_WORKFLOW_PATH.read_text(encoding="utf-8"))

    assert isinstance(workflow, dict)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)

    hook_parity = jobs.get("hook-parity")
    assert isinstance(hook_parity, dict)
    assert hook_parity.get("name") == "hook parity (${{ matrix.os }})"
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
        "Windows / macOS / Linux",
        "`tests/test_git_hooks_secret_guard.py`",
        "`ubuntu-latest`",
        "`macos-latest`",
        "`windows-latest`",
        "uv run python -m pytest -q tests/test_git_hooks_secret_guard.py",
    ):
        assert phrase in quality_gates

    assert "uv run python -m pytest -q tests/test_git_hooks_secret_guard.py" in development
    assert "`hook-parity` job" in development
