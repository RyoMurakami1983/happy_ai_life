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
        if resolved is not None:
            return resolved
    pytest.skip("PowerShell executable not found")


pytestmark = pytest.mark.skipif(
    os.name != "nt",
    reason="repo-secure-check.ps1 smoke test runs through PowerShell on Windows",
)


def _git(repo: Path, *args: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _write_required_git_hooks(repo: Path, relative: str) -> None:
    hooks = repo / relative
    (hooks / "lib").mkdir(parents=True)
    (hooks / "pre-commit").write_text(
        '#!/usr/bin/env sh\nsh "$(dirname "$0")/lib/commit-safety-guard.sh"\nsh "$(dirname "$0")/lib/secret-guard.sh"\n',
        encoding="utf-8",
    )
    (hooks / "pre-push").write_text(
        '#!/usr/bin/env sh\nsh "$(dirname "$0")/lib/secret-guard.sh" --range "$remote_sha..$local_sha"\n',
        encoding="utf-8",
    )
    (hooks / "lib" / "secret-guard.sh").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    (hooks / "lib" / "commit-safety-guard.sh").write_text("#!/usr/bin/env sh\n", encoding="utf-8")


def _write_cmd_shim(bin_dir: Path, name: str) -> None:
    shim = bin_dir / f"{name}.cmd"
    shim.write_text("@echo off\nexit /b 0\n", encoding="utf-8")


def _tool_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("gitleaks", "jq", "node", "gh"):
        _write_cmd_shim(bin_dir, tool)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env.setdefault("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    return env


def _run_check(repo: Path, source_root: Path, env: dict[str, str], *, strict: bool = True) -> dict[str, Any]:
    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-TargetRepoPath",
        str(repo),
        "-SourceRoot",
        str(source_root),
        "-AsJson",
    ]
    if strict:
        command.insert(-1, "-Strict")

    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_repo_secure_check_uses_repo_template_githooks_for_source_repo(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    _git(source_repo, "init")
    _git(source_repo, "config", "--local", "core.hooksPath", "repo-template/.githooks")

    (source_repo / ".github" / "copilot-instructions.md").parent.mkdir(parents=True)
    (source_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (source_repo / ".github" / "hooks").mkdir()
    (source_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (source_repo / ".github" / "workflows").mkdir()
    (source_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    _write_required_git_hooks(source_repo, "repo-template/.githooks")

    report = _run_check(source_repo, source_repo, _tool_env(tmp_path))

    assert report["missing"] == []
    git_hooks = next(check for check in report["checks"] if check["key"] == "gitHooksDirectory")
    assert git_hooks["label"] == "repo-template/.githooks"

