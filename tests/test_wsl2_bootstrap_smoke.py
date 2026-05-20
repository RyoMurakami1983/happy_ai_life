from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _require_linux_bootstrap_tools() -> None:
    missing = [tool for tool in ("bash", "rsync", "git") if shutil.which(tool) is None]
    if missing:
        pytest.skip(f"Missing required Linux bootstrap tools: {', '.join(missing)}")


def _bash(script: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout.strip()


def _write_shell_shim(bin_dir: Path, name: str) -> None:
    shim = bin_dir / name
    shim.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    shim.chmod(0o755)


def _tool_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("gitleaks", "jq", "node", "gh"):
        _write_shell_shim(bin_dir, tool)

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def test_sync_to_home_sh_writes_bash_managed_hook_entry(tmp_path: Path) -> None:
    _require_linux_bootstrap_tools()
    destination = tmp_path / ".copilot"
    destination.mkdir()
    (destination / "config.json").write_text(
        json.dumps({"permissions": {"allow": None}, "hooks": {}}),
        encoding="utf-8",
    )

    completed = _bash(
        ROOT / "scripts" / "sync-to-home.sh",
        "--DestinationPath",
        str(destination),
        "--ArchiveRoot",
        str(tmp_path / "archives"),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    config = json.loads((destination / "config.json").read_text(encoding="utf-8"))
    entry = config["hooks"]["preToolUse"][-1]
    assert entry["env"]["HAPPY_AI_LIFE_HOOK_ID"] == "happy-ai-life-safety-guard"
    assert entry["bash"] == 'bash "hooks/scripts/guard_pre_tool.sh"'
    assert "guard_pre_tool.ps1" in entry["powershell"]
    assert (destination / "hooks" / "safety-guard.json").exists()


def test_sync_to_home_sh_preserves_comment_prefixed_config_json(tmp_path: Path) -> None:
    _require_linux_bootstrap_tools()
    destination = tmp_path / ".copilot"
    destination.mkdir()
    (destination / "config.json").write_text(
        "// User settings belong in settings.json.\n"
        "// This file is managed automatically.\n"
        "{\n"
        '  "permissions": {"allow": null},\n'
        '  "hooks": {\n'
        '    "preToolUse": [\n'
        '      {"type": "command", "bash": "echo keep", "env": {"OTHER": "1"}}\n'
        "    ]\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _bash(
        ROOT / "scripts" / "sync-to-home.sh",
        "--DestinationPath",
        str(destination),
        "--ArchiveRoot",
        str(tmp_path / "archives"),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    rendered = (destination / "config.json").read_text(encoding="utf-8")
    assert rendered.startswith("// User settings belong in settings.json.\n// This file is managed automatically.\n")
    config = json.loads("\n".join(rendered.splitlines()[2:]))
    assert config["permissions"]["allow"] is None
    assert config["hooks"]["preToolUse"][0]["bash"] == "echo keep"
    assert config["hooks"]["preToolUse"][-1]["env"]["HAPPY_AI_LIFE_HOOK_ID"] == "happy-ai-life-safety-guard"
    assert config["hooks"]["preToolUse"][-1]["bash"] == 'bash "hooks/scripts/guard_pre_tool.sh"'


def test_install_git_hooks_sh_configures_source_repo_hooks_path(tmp_path: Path) -> None:
    _require_linux_bootstrap_tools()
    source_repo = tmp_path / "source"
    (source_repo / "repo-template" / ".githooks").mkdir(parents=True)
    (source_repo / "repo-template" / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    _git(source_repo, "init")

    completed = _bash(
        ROOT / "scripts" / "install-git-hooks.sh",
        "-TargetRepoPath",
        str(source_repo),
        "-SourceRoot",
        str(source_repo),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert _git(source_repo, "config", "--local", "--get", "core.hooksPath") == "repo-template/.githooks"


def test_sync_to_repo_and_repo_secure_check_sh_work_on_linux(tmp_path: Path) -> None:
    _require_linux_bootstrap_tools()
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    _git(target_repo, "init")

    sync_completed = _bash(
        ROOT / "scripts" / "sync-to-repo.sh",
        "-TargetRepoPath",
        str(target_repo),
        "-SourceRoot",
        str(ROOT),
    )

    assert sync_completed.returncode == 0, sync_completed.stdout + sync_completed.stderr
    assert (target_repo / ".github" / "copilot-instructions.md").exists()
    assert (target_repo / ".github" / "hooks" / "safety-guard.json").exists()
    assert not (target_repo / ".github" / "hooks" / "session-continuity.json").exists()
    assert (target_repo / ".githooks" / "pre-commit").exists()
    assert (target_repo / "policy" / "guard-policy.json").exists()

    install_completed = _bash(
        ROOT / "scripts" / "install-git-hooks.sh",
        "-TargetRepoPath",
        str(target_repo),
        "-SourceRoot",
        str(ROOT),
    )
    assert install_completed.returncode == 0, install_completed.stdout + install_completed.stderr
    assert _git(target_repo, "config", "--local", "--get", "core.hooksPath") == ".githooks"
    (target_repo / "Sample.csproj").write_text("<Project Sdk=\"Microsoft.NET.Sdk\" />\n", encoding="utf-8")

    report_completed = _bash(
        ROOT / "scripts" / "repo-secure-check.sh",
        "-TargetRepoPath",
        str(target_repo),
        "-SourceRoot",
        str(ROOT),
        "-Strict",
        "-AsJson",
        env=_tool_env(tmp_path),
    )
    assert report_completed.returncode == 0, report_completed.stdout + report_completed.stderr
    report = json.loads(report_completed.stdout)
    assert report["missing"] == []


def test_home_synced_shell_script_can_generate_repo_assets(tmp_path: Path) -> None:
    _require_linux_bootstrap_tools()
    home_destination = tmp_path / "home" / ".copilot"
    target_repo = tmp_path / "repo"
    home_destination.mkdir(parents=True)
    target_repo.mkdir()
    _git(target_repo, "init")

    home_completed = _bash(
        ROOT / "scripts" / "sync-to-home.sh",
        "--DestinationPath",
        str(home_destination),
        "--ArchiveRoot",
        str(tmp_path / "archives"),
    )
    assert home_completed.returncode == 0, home_completed.stdout + home_completed.stderr

    repo_completed = _bash(
        home_destination / "scripts" / "sync-to-repo.sh",
        "-TargetRepoPath",
        str(target_repo),
    )
    assert repo_completed.returncode == 0, repo_completed.stdout + repo_completed.stderr
    assert (target_repo / ".github" / "copilot-instructions.md").exists()
    assert (target_repo / ".github" / "hooks" / "safety-guard.json").exists()
