from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS_DIR = ROOT / "evals"
GITIGNORE = ROOT / ".gitignore"

FORBIDDEN_EVAL_PATH_MARKERS = (
    "runs",
    "viewer.html",
    "transcript",
    "raw",
)

REQUIRED_GITIGNORE_PATTERNS = (
    "evals/**/runs/",
    "evals/**/viewer.html",
    "evals/**/*transcript*",
    "evals/**/*raw*",
)


def test_private_eval_raw_artifacts_are_ignored() -> None:
    gitignore = GITIGNORE.read_text(encoding="utf-8")

    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        assert pattern in gitignore


def test_private_eval_does_not_track_raw_artifact_paths() -> None:
    if not EVALS_DIR.exists():
        return

    tracked_eval_files = [path for path in EVALS_DIR.rglob("*") if path.is_file()]

    for path in tracked_eval_files:
        relative_parts = {part.lower() for part in path.relative_to(EVALS_DIR).parts}
        relative_name = path.name.lower()
        assert "runs" not in relative_parts
        assert relative_name != "viewer.html"
        assert "transcript" not in relative_name
        assert "raw" not in relative_name
