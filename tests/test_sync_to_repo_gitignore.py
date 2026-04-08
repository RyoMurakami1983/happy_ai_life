from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-to-repo.ps1"
ROBOCOPY = shutil.which("robocopy")
SKIP_REASON = "sync-to-repo.ps1 requires Windows robocopy"


def _powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    pytest.skip("PowerShell executable not found")


pytestmark = pytest.mark.skipif(
    os.name != "nt" or ROBOCOPY is None,
    reason=SKIP_REASON,
)


def _run_sync(
    source_root: Path,
    target_repo: Path,
    *,
    dry_run: bool,
) -> subprocess.CompletedProcess[str]:
    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-SourceRoot",
        str(source_root),
        "-TargetRepoPath",
        str(target_repo),
        "-HooksRelativePath",
        "",
        "-GitHooksRelativePath",
        "",
        "-DocsSessionsRelativePath",
        "",
    ]
    if dry_run:
        command.append("-DryRun")

    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _create_minimal_source_root(base: Path) -> Path:
    template_dir = base / "repo-template" / ".github"
    template_dir.mkdir(parents=True)
    (template_dir / ".gitignore").write_text(
        "# Session and local files\n"
        "sessions/\n"
        "instructions/session-context.instructions.md\n",
        encoding="utf-8",
    )
    return base


def test_sync_to_repo_preserves_existing_github_gitignore_on_dry_run(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    github_dir = target_repo / ".github"
    github_dir.mkdir(parents=True)
    original = "# custom local rule\ncustom.local\n"
    target_file = github_dir / ".gitignore"
    target_file.write_text(original, encoding="utf-8")

    result = _run_sync(source_root, target_repo, dry_run=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert target_file.read_text(encoding="utf-8") == original


def test_sync_to_repo_appends_missing_github_gitignore_rules(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    github_dir = target_repo / ".github"
    github_dir.mkdir(parents=True)
    target_file = github_dir / ".gitignore"
    target_file.write_text("# custom local rule\ncustom.local\n", encoding="utf-8")

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr

    content = target_file.read_text(encoding="utf-8")
    assert "# custom local rule" in content
    assert "custom.local" in content
    assert "sessions/" in content
    assert "instructions/session-context.instructions.md" in content


def test_sync_to_repo_creates_missing_github_gitignore(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    (target_repo / ".github").mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr

    target_file = target_repo / ".github" / ".gitignore"
    assert target_file.exists()
    content = target_file.read_text(encoding="utf-8")
    assert "sessions/" in content
    assert "instructions/session-context.instructions.md" in content
