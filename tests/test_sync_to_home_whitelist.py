from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-to-home.ps1"
ROBOCOPY = shutil.which("robocopy")
SKIP_REASON = "sync-to-home.ps1 requires Windows robocopy"


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
    destination: Path,
    *,
    dry_run: bool,
    mirror: bool = False,
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
        "-DestinationPath",
        str(destination),
    ]
    if dry_run:
        command.append("-DryRun")
    if mirror:
        command.append("-Mirror")

    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _create_minimal_source_root(base: Path) -> Path:
    copilot_dir = base / "home-template" / ".copilot"
    (copilot_dir / "skills" / "sample-skill").mkdir(parents=True)
    (copilot_dir / "agents").mkdir(parents=True)
    (copilot_dir / "docs" / "furikaeri").mkdir(parents=True)
    (copilot_dir / "skills" / "sample-skill" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (copilot_dir / "agents" / "tdd-coder.agent.md").write_text("# agent\n", encoding="utf-8")
    (copilot_dir / "docs" / "furikaeri" / ".gitkeep").write_text("\n", encoding="utf-8")
    (copilot_dir / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (copilot_dir / "mcp-config.sample.json").write_text("{}", encoding="utf-8")
    (copilot_dir / "config.json").write_text('{"runtime":true}', encoding="utf-8")
    (copilot_dir / "session-state").mkdir()

    repo_template = base / "repo-template"
    (repo_template / ".github").mkdir(parents=True)
    (repo_template / ".githooks").mkdir(parents=True)
    (repo_template / ".github" / "copilot-instructions.md").write_text("# repo instructions\n", encoding="utf-8")
    (repo_template / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    repo_hooks = base / ".github" / "hooks" / "scripts"
    repo_hooks.mkdir(parents=True)
    (repo_hooks / "sample.js").write_text("console.log('hook');\n", encoding="utf-8")

    scripts_dir = base / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "sync-to-repo.ps1").write_text("Write-Host 'sync repo'\n", encoding="utf-8")
    (scripts_dir / "install-git-hooks.ps1").write_text("Write-Host 'install hooks'\n", encoding="utf-8")
    (scripts_dir / "repo-secure-check.ps1").write_text("Write-Host 'secure check'\n", encoding="utf-8")
    return base


def _collect_relative_files(base: Path) -> dict[str, str]:
    return {
        str(path.relative_to(base)).replace("\\", "/"): path.read_text(encoding="utf-8")
        for path in base.rglob("*")
        if path.is_file()
    }


def _create_extra_files(base: Path) -> None:
    (base / "a").mkdir(parents=True, exist_ok=True)
    (base / "a" / "b.md").write_text("extra markdown\n", encoding="utf-8")
    (base / "c.py").write_text("print('extra')\n", encoding="utf-8")
    (base / "d").mkdir(parents=True, exist_ok=True)
    (base / "d" / "e.ps1").write_text("Write-Host 'extra'\n", encoding="utf-8")


def test_sync_to_home_copies_tracked_targets_and_preserves_runtime_files(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    destination.mkdir(parents=True)
    (destination / "config.json").write_text('{"user":true}', encoding="utf-8")
    (destination / "session-state").mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")

    result = _run_sync(source_root, destination, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (destination / "skills" / "sample-skill" / "SKILL.md").exists()
    assert (destination / "agents" / "tdd-coder.agent.md").exists()
    assert (destination / "repo-template" / ".github" / "copilot-instructions.md").exists()
    assert (destination / ".github" / "hooks" / "scripts" / "sample.js").exists()
    assert (destination / "scripts" / "sync-to-repo.ps1").exists()
    assert (destination / "scripts" / "install-git-hooks.ps1").exists()
    assert (destination / "scripts" / "repo-secure-check.ps1").exists()
    assert (destination / "copilot-instructions.md").exists()
    assert (destination / "mcp-config.sample.json").exists()
    assert (destination / "docs" / "furikaeri" / ".gitkeep").exists()
    assert (destination / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert (destination / "config.json").read_text(encoding="utf-8") == '{"user":true}'
    assert (destination / "session-state").exists()


def test_sync_to_home_mirrors_skills_and_agents_to_template(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    source_agents = source_root / "home-template" / ".copilot" / "agents"
    (source_agents / "draft.agent.md").write_text("# draft\n", encoding="utf-8")

    destination = tmp_path / "home"
    _create_extra_files(destination / "skills")
    _create_extra_files(destination / "agents")

    result = _run_sync(source_root, destination, dry_run=False)

    combined_output = result.stdout + result.stderr
    assert result.returncode == 0, combined_output

    for top_level in ("skills", "agents"):
        assert not (destination / top_level / "a" / "b.md").exists()
        assert not (destination / top_level / "c.py").exists()
        assert not (destination / top_level / "d" / "e.ps1").exists()
        assert not (destination / top_level / "a").exists()
        assert not (destination / top_level / "d").exists()

    assert _collect_relative_files(destination / "skills") == _collect_relative_files(
        source_root / "home-template" / ".copilot" / "skills"
    )
    assert _collect_relative_files(destination / "agents") == _collect_relative_files(source_agents)


def test_sync_to_home_mirror_flag_is_compatibility_only(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    destination.mkdir(parents=True)

    result = _run_sync(source_root, destination, dry_run=True, mirror=True)

    combined_output = result.stdout + result.stderr
    assert result.returncode == 0, combined_output
    assert "追加効果を持ちません" in combined_output


def test_sync_to_home_does_not_delete_home_only_furikaeri_docs(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    destination.mkdir(parents=True)
    furikaeri_dir = destination / "docs" / "furikaeri"
    furikaeri_dir.mkdir(parents=True)
    user_doc = furikaeri_dir / "20260101-120000-my-session.md"
    user_doc.write_text("# user furikaeri\n", encoding="utf-8")

    result = _run_sync(source_root, destination, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert user_doc.exists(), "home-only furikaeri doc must not be deleted by sync"
    assert (furikaeri_dir / ".gitkeep").exists()
