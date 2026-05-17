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


def _run_check(
    target_repo: Path,
    *,
    source_root: Path | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    effective_env = _build_tool_env(target_repo)
    return _run_check_with_env(
        target_repo,
        source_root=source_root,
        env=effective_env,
        strict=strict,
    )


def _run_check_with_env(
    target_repo: Path,
    *,
    source_root: Path | None = None,
    env: dict[str, str],
    strict: bool = False,
) -> dict[str, Any]:
    effective_source_root = source_root or ROOT
    completed = _run_check_process(
        target_repo,
        source_root=effective_source_root,
        env=env,
        strict=strict,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert isinstance(report, dict), f"repo-secure-check output must be a JSON object, got: {type(report)}"
    return report


def _run_check_process(
    target_repo: Path,
    *,
    source_root: Path | None = None,
    env: dict[str, str] | None = None,
    strict: bool = False,
) -> subprocess.CompletedProcess[str]:
    effective_source_root = source_root or ROOT
    command = [
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
    ]
    if strict:
        command.append("-Strict")
    command.append("-AsJson")
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def _git(repo: Path, *args: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _write_cmd_shim(bin_dir: Path, name: str, body: str = "") -> None:
    script = bin_dir / f"{name}.cmd"
    script.write_text(f"@echo off\n{body}exit /b 0\n", encoding="utf-8")


def _git_hooks_path(repo: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "--get", "core.hooksPath"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    hooks_path = completed.stdout.strip()
    return hooks_path or None


def _build_tool_env(
    repo: Path,
    *,
    include_git: bool = True,
    include_gitleaks: bool = True,
    include_shell: bool = True,
    include_python: bool = True,
    include_node: bool = True,
    include_gh: bool = True,
) -> dict[str, str]:
    bin_dir = repo / ".test-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    if include_git:
        hooks_path = _git_hooks_path(repo)
        config_body = (
            "if /I \"%~1\"==\"config\" if /I \"%~2\"==\"--local\" if /I \"%~3\"==\"--get\" if /I \"%~4\"==\"core.hooksPath\" (\n"
            f"  echo {hooks_path}\n"
            "  exit /b 0\n"
            ")\n"
        ) if hooks_path else (
            "if /I \"%~1\"==\"config\" if /I \"%~2\"==\"--local\" if /I \"%~3\"==\"--get\" if /I \"%~4\"==\"core.hooksPath\" exit /b 1\n"
        )
        git_body = (
            "if /I \"%~1\"==\"-C\" (\n"
            "  shift\n"
            "  shift\n"
            ")\n"
            "if /I \"%~1\"==\"rev-parse\" if /I \"%~2\"==\"--is-inside-work-tree\" (\n"
            "  echo true\n"
            "  exit /b 0\n"
            ")\n"
            f"{config_body}"
            "exit /b 1\n"
        )
        _write_cmd_shim(bin_dir, "git", git_body)

    if include_gitleaks:
        _write_cmd_shim(bin_dir, "gitleaks")

    if include_shell:
        _write_cmd_shim(bin_dir, "powershell")

    if include_python:
        _write_cmd_shim(bin_dir, "python")

    if include_node:
        _write_cmd_shim(bin_dir, "node")

    if include_gh:
        _write_cmd_shim(bin_dir, "gh")

    env = os.environ.copy()
    env["PATH"] = str(bin_dir)
    env.setdefault("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    return env


def _write_required_git_hooks(repo: Path, relative: str = ".githooks") -> None:
    hooks = repo / relative
    (hooks / "lib").mkdir(parents=True, exist_ok=True)
    (hooks / "pre-commit").write_text(
        '#!/usr/bin/env sh\nsh "$(dirname "$0")/lib/commit-safety-guard.sh"\nsh "$(dirname "$0")/lib/secret-guard.sh"\n',
        encoding="utf-8",
    )
    (hooks / "pre-push").write_text(
        '#!/usr/bin/env sh\nsh "$(dirname "$0")/lib/secret-guard.sh" --range "$remote_sha..$local_sha"\n',
        encoding="utf-8",
    )
    for file_name in ("secret-guard.sh", "commit-safety-guard.sh"):
        (hooks / "lib" / file_name).write_text("#!/usr/bin/env sh\n", encoding="utf-8")


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
        "githubWorkflows",
        "coreHooksPath",
    }


def test_repo_secure_check_strict_returns_non_zero_when_missing(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    completed = _run_check_process(
        target_repo,
        env=_build_tool_env(target_repo),
        strict=True,
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert set(report["missing"]) == {
        "repoInstructions",
        "copilotHooks",
        "gitHooksDirectory",
        "githubWorkflows",
        "coreHooksPath",
    }


def test_repo_secure_check_reports_secure_repo(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == []
    copilot_hooks_check = next(check for check in report["checks"] if check["key"] == "copilotHooks")
    assert "session continuity hooks" in copilot_hooks_check["details"]
    assert report["toolDependencies"]["required"] == ["git", "gitleaks", "pwsh or powershell"]


def test_repo_secure_check_strict_succeeds_for_secure_repo(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    completed = _run_check_process(
        target_repo,
        env=_build_tool_env(target_repo),
        strict=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert report["missing"] == []


def test_repo_secure_check_accepts_repo_template_githooks_for_source_root(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    _git(source_root, "init")

    (source_root / ".github" / "hooks").mkdir(parents=True)
    (source_root / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (source_root / ".github" / "workflows").mkdir(parents=True)
    (source_root / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (source_root / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (source_root / "repo-template" / ".githooks" / "lib").mkdir(parents=True)
    _write_required_git_hooks(source_root / "repo-template")
    _git(source_root, "config", "--local", "core.hooksPath", "repo-template/.githooks")

    report = _run_check(source_root, source_root=source_root)

    assert report["isGitRepo"] is True
    assert report["missing"] == []
    git_hooks_check = next(check for check in report["checks"] if check["key"] == "gitHooksDirectory")
    assert git_hooks_check["path"].endswith("repo-template\\.githooks")


def test_repo_secure_check_requires_concrete_git_hook_files(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (target_repo / ".githooks" / "lib").mkdir(parents=True)
    (target_repo / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    (target_repo / ".githooks" / "lib" / "secret-guard.sh").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["gitHooksDirectory"]
    git_hooks_check = next(check for check in report["checks"] if check["key"] == "gitHooksDirectory")
    assert "pre-push" in git_hooks_check["details"]
    assert "commit-safety-guard.sh" in git_hooks_check["details"]


def test_repo_secure_check_rejects_stub_git_hooks(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (target_repo / ".githooks" / "lib").mkdir(parents=True)
    for file_name in ("pre-commit", "pre-push"):
        (target_repo / ".githooks" / file_name).write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    for file_name in ("secret-guard.sh", "commit-safety-guard.sh"):
        (target_repo / ".githooks" / "lib" / file_name).write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["gitHooksDirectory"]
    git_hooks_check = next(check for check in report["checks"] if check["key"] == "gitHooksDirectory")
    assert "pre-commit does not call commit-safety-guard.sh" in git_hooks_check["details"]
    assert "pre-push does not call secret-guard.sh --range" in git_hooks_check["details"]


def test_repo_secure_check_requires_copilot_hook_json_files(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks" / "scripts").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "scripts" / "sample.ps1").write_text("# script\n", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["copilotHooks"]
    copilot_hooks_check = next(check for check in report["checks"] if check["key"] == "copilotHooks")
    assert "safety-guard.json" in copilot_hooks_check["details"]


def test_repo_secure_check_rejects_legacy_session_continuity_hook_without_safety_guard(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "session-continuity.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["copilotHooks"]
    copilot_hooks_check = next(check for check in report["checks"] if check["key"] == "copilotHooks")
    assert "safety-guard.json" in copilot_hooks_check["details"]


def test_repo_secure_check_requires_node_and_gh_for_session_continuity(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "hooks" / "session-continuity.json").write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {
                    "sessionStart": [
                        {"type": "command", "powershell": "node .github/hooks/scripts/session-start.js"}
                    ],
                    "sessionEnd": [
                        {"type": "command", "powershell": "node .github/hooks/scripts/session-end.js"}
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check_with_env(
        target_repo,
        env=_build_tool_env(target_repo, include_node=False, include_gh=False),
    )

    assert report["isGitRepo"] is True
    assert "toolDependencies" in report["missing"]
    assert report["toolDependencies"]["required"] == [
        "git",
        "gitleaks",
        "pwsh or powershell",
        "node",
        "gh",
    ]
    assert report["toolDependencies"]["missing"] == ["node", "gh"]


def test_repo_secure_check_requires_python_for_windows_powershell_variant(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {
                    "preToolUse": [
                        {
                            "type": "command",
                            "bash": "bash .github/hooks/scripts/guard_pre_tool.sh",
                            "powershell": "if ($PSVersionTable.PSEdition -eq 'Core') { & '.github\\hooks\\scripts\\guard_pre_tool.ps1' } elseif (Get-Command pwsh -ErrorAction SilentlyContinue) { & pwsh -NoProfile -File '.github\\hooks\\scripts\\guard_pre_tool.ps1' } else { & '.github\\hooks\\scripts\\guard_pre_tool.ps1' }",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check_with_env(
        target_repo,
        env=_build_tool_env(target_repo, include_python=False),
    )

    assert report["isGitRepo"] is True
    assert "toolDependencies" in report["missing"]
    assert report["toolDependencies"]["required"] == ["git", "gitleaks", "pwsh or powershell", "python3 or python or py -3"]
    assert report["toolDependencies"]["missing"] == ["python3 or python or py -3"]


def test_repo_secure_check_rejects_python_older_than_310(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {
                    "preToolUse": [
                        {
                            "type": "command",
                            "bash": "bash .github/hooks/scripts/guard_pre_tool.sh",
                            "powershell": "if ($PSVersionTable.PSEdition -eq 'Core') { & '.github\\hooks\\scripts\\guard_pre_tool.ps1' } elseif (Get-Command pwsh -ErrorAction SilentlyContinue) { & pwsh -NoProfile -File '.github\\hooks\\scripts\\guard_pre_tool.ps1' } else { & '.github\\hooks\\scripts\\guard_pre_tool.ps1' }",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    env = _build_tool_env(target_repo)
    bin_dir = Path(env["PATH"])
    _write_cmd_shim(bin_dir, "python", "if /I \"%~1\"==\"-c\" exit /b 2\n")

    report = _run_check_with_env(target_repo, env=env)

    assert report["isGitRepo"] is True
    assert "toolDependencies" in report["missing"]
    assert report["toolDependencies"]["required"] == ["git", "gitleaks", "pwsh or powershell", "python3 or python or py -3"]
    assert report["toolDependencies"]["missing"] == ["python3 or python or py -3"]


def test_repo_secure_check_reports_missing_git_dependency(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check_with_env(
        target_repo,
        env=_build_tool_env(target_repo, include_git=False),
    )

    assert report["isGitRepo"] is False
    assert "toolDependencies" in report["missing"]
    assert "git" in report["toolDependencies"]["missing"]


def test_repo_secure_check_accepts_repo_template_hooks_for_source_repo(tmp_path: Path) -> None:
    target_repo = tmp_path / "source-root"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _write_required_git_hooks(target_repo, "repo-template/.githooks")
    _git(target_repo, "config", "--local", "core.hooksPath", "repo-template/.githooks")

    report = _run_check(target_repo, source_root=target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == []


def test_repo_secure_check_reports_missing_github_workflows(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["githubWorkflows"]
    workflow_check = next(check for check in report["checks"] if check["key"] == "githubWorkflows")
    assert "repo-onboarding" in workflow_check["details"]


def test_repo_secure_check_rejects_non_yaml_files_in_github_workflows(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "README.md").write_text("# workflows\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["githubWorkflows"]


def test_repo_secure_check_rejects_dotnet_template_without_dotnet_project(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "dotnet-quality.yml").write_text("name: .NET Quality Gate\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == ["githubWorkflows"]
    workflow_check = next(check for check in report["checks"] if check["key"] == "githubWorkflows")
    assert ".NET project" in workflow_check["details"]


def test_repo_secure_check_accepts_dotnet_template_with_dotnet_project(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / "App.csproj").write_text("<Project Sdk=\"Microsoft.NET.Sdk\" />\n", encoding="utf-8")
    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "dotnet-quality.yml").write_text("name: .NET Quality Gate\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == []


def test_repo_secure_check_accepts_dotnet_template_with_fsharp_project(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / "App.fsproj").write_text("<Project Sdk=\"Microsoft.NET.Sdk\" />\n", encoding="utf-8")
    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "dotnet-quality.yml").write_text("name: .NET Quality Gate\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == []


def test_repo_secure_check_accepts_yaml_github_workflow(tmp_path: Path) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    (target_repo / ".github" / "hooks").mkdir(parents=True)
    (target_repo / ".github" / "hooks" / "safety-guard.json").write_text("{}", encoding="utf-8")
    (target_repo / ".github" / "workflows").mkdir(parents=True)
    (target_repo / ".github" / "workflows" / "quality.yaml").write_text("name: quality\n", encoding="utf-8")
    (target_repo / ".github" / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    _write_required_git_hooks(target_repo)
    _git(target_repo, "config", "--local", "core.hooksPath", ".githooks")

    report = _run_check(target_repo)

    assert report["isGitRepo"] is True
    assert report["missing"] == []
