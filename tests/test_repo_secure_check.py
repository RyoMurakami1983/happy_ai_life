from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "repo-secure-check.ps1"


def _powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    pytest.skip("PowerShell executable not found")


pytestmark = pytest.mark.skipif(
    os.name != "nt",
    reason="repo-secure-check.ps1 is exercised through PowerShell on Windows",
)


def _run_check(target_repo: Path, *, source_root: Path | None = None) -> dict[str, Any]:
    effective_source_root = source_root or ROOT
    completed = subprocess.run(
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
            str(effective_source_root),
            "-AsJson",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert isinstance(report, dict), f"repo-secure-check output must be a JSON object, got: {type(report)}"
    return report


def _git(repo: Path, *args: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_repo_secure_check_reports_missing_local_safety_valves(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert set(report["missing"]) == {
        "repoInstructions",
        "copilotHooks",
        "gitHooksDirectory",
        "coreHooksPath",
    }


def test_repo_secure_check_reports_secure_repo(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "sample.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (target_repo / ".githooks").mkdir(parents=True)
    (target_repo / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == []


def test_repo_secure_check_requires_copilot_hook_json_files(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks" / "scripts").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "scripts" / "sample.ps1").write_text("# script\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (target_repo / ".githooks").mkdir(parents=True)
    (target_repo / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["copilotHooks"]
    copilot_hooks_check = next(check for check in report["checks"] if check["key"] == "copilotHooks")
    assert "JSON" in copilot_hooks_check["details"]


def test_repo_secure_check_accepts_repo_template_hooks_for_source_repo(tmp_path: Path) -> None:
    target_repo = tmp_path / "source-root"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "sample.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (target_repo / ".githooks").mkdir(parents=True)
    (target_repo / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    (target_repo / "repo-template" / ".githooks").mkdir(parents=True)
    (target_repo / "repo-template" / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    _git(target_repo, "config", "--local", "core.hooksPath", "repo-template/.githooks")

    report = _run_check(target_repo, source_root=target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == []
