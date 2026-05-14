from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install-git-hooks.ps1"
HOOKS_SOURCE = ROOT / "repo-template" / ".githooks"


def _powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    pytest.skip("PowerShell executable not found")


pytestmark = pytest.mark.skipif(
    os.name != "nt",
    reason="install-git-hooks.ps1 is exercised through PowerShell on Windows",
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    init = _git(repo, "init")
    assert init.returncode == 0, init.stdout + init.stderr


def _run_install(target_repo: Path, *, source_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _powershell_executable(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            "-TargetRepoPath",
            str(target_repo),
            "-SourceRoot",
            str(source_root),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _configured_hooks_path(repo: Path) -> str:
    completed = _git(repo, "config", "--local", "--get", "core.hooksPath")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout.strip()


def test_install_git_hooks_configures_source_repo_to_repo_template_hooks(tmp_path: Path) -> None:
    source_root = tmp_path / "source-root"
    _init_repo(source_root)
    shutil.copytree(HOOKS_SOURCE, source_root / "repo-template" / ".githooks")

    result = _run_install(source_root, source_root=source_root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _configured_hooks_path(source_root) == "repo-template/.githooks"


def test_install_git_hooks_copies_hooks_and_configures_target_repo(tmp_path: Path) -> None:
    target_repo = tmp_path / "target-repo"
    _init_repo(target_repo)

    result = _run_install(target_repo, source_root=ROOT)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _configured_hooks_path(target_repo) == ".githooks"
    assert (target_repo / ".githooks" / "pre-commit").exists()
    assert (target_repo / ".githooks" / "pre-push").exists()
