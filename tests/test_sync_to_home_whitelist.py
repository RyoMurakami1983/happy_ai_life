from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-to-home.ps1"
SKIP_REASON = "sync-to-home.ps1 tests require Windows"


def _powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    pytest.skip("PowerShell executable not found")


pytestmark = pytest.mark.skipif(
    os.name != "nt",
    reason=SKIP_REASON,
)


def _run_sync(
    source_root: Path,
    destination: Path,
    *,
    archive_root: Path,
    dry_run: bool,
    verbose_log: bool = False,
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
        "-ArchiveRoot",
        str(archive_root),
        "-PythonExecutable",
        str(Path(sys.executable)),
    ]
    if dry_run:
        command.append("-DryRun")
    if verbose_log:
        command.append("-VerboseLog")
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
    copilot_dir.mkdir(parents=True)
    (copilot_dir / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
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
    archive_root = tmp_path / "archive"
    destination.mkdir(parents=True)
    (destination / "config.json").write_text('{"user":true}', encoding="utf-8")
    (destination / "mcp-config.json").write_text('{"user":true}', encoding="utf-8")
    (destination / "session-state").mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")

    result = _run_sync(source_root, destination, archive_root=archive_root, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (destination / "repo-template" / ".github" / "copilot-instructions.md").exists()
    assert not (destination / ".github" / "hooks" / "scripts" / "sample.js").exists()
    assert (destination / "scripts" / "sync-to-repo.ps1").exists()
    assert (destination / "scripts" / "install-git-hooks.ps1").exists()
    assert (destination / "scripts" / "repo-secure-check.ps1").exists()
    assert (destination / "copilot-instructions.md").exists()
    assert not (destination / "mcp-config.sample.json").exists()
    assert (destination / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert (destination / "config.json").read_text(encoding="utf-8") == '{"user":true}'
    assert (destination / "mcp-config.json").read_text(encoding="utf-8") == '{"user":true}'
    assert (destination / "session-state").exists()


def test_sync_to_home_removes_legacy_home_hook_transport(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    archive_root = tmp_path / "archive"
    legacy_hooks = destination / ".github" / "hooks"
    legacy_hooks.mkdir(parents=True)
    (legacy_hooks / "session-continuity.json").write_text("{}", encoding="utf-8")
    (legacy_hooks / "scripts").mkdir()
    (legacy_hooks / "scripts" / "session-start.js").write_text("console.log('stale');\n", encoding="utf-8")

    result = _run_sync(source_root, destination, archive_root=archive_root, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not legacy_hooks.exists()
    assert not (destination / ".github").exists()
    assert "Legacy home hook transport detected" in result.stdout


def test_sync_to_home_dry_run_preserves_legacy_home_hook_transport(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    archive_root = tmp_path / "archive"
    legacy_hooks = destination / ".github" / "hooks"
    legacy_hooks.mkdir(parents=True)
    (legacy_hooks / "session-continuity.json").write_text("{}", encoding="utf-8")

    result = _run_sync(source_root, destination, archive_root=archive_root, dry_run=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert legacy_hooks.exists()
    assert "Legacy home hook transport detected" in result.stdout


def test_sync_to_home_preserves_unknown_files_under_legacy_home_hook_path(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    archive_root = tmp_path / "archive"
    legacy_hooks = destination / ".github" / "hooks"
    legacy_hooks.mkdir(parents=True)
    known_file = legacy_hooks / "session-continuity.json"
    unknown_file = legacy_hooks / "custom.json"
    known_file.write_text("{}", encoding="utf-8")
    unknown_file.write_text('{"user":true}', encoding="utf-8")

    result = _run_sync(source_root, destination, archive_root=archive_root, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not known_file.exists()
    assert unknown_file.exists()
    assert legacy_hooks.exists()
    assert "Legacy home hook transport detected" in result.stdout


def test_sync_to_home_leaves_home_skills_agents_and_docs_untouched(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    archive_root = tmp_path / "archive"

    destination = tmp_path / "home"
    (destination / "skills" / "local-extra").mkdir(parents=True)
    (destination / "skills" / "local-extra" / "SKILL.md").write_text("# local extra skill\n", encoding="utf-8")
    _create_extra_files(destination / "skills")

    (destination / "agents").mkdir(parents=True, exist_ok=True)
    (destination / "agents" / "custom.agent.md").write_text("# custom agent\n", encoding="utf-8")
    _create_extra_files(destination / "agents")
    (destination / "docs" / "furikaeri").mkdir(parents=True)
    (destination / "docs" / "furikaeri" / "local.md").write_text("# local furikaeri\n", encoding="utf-8")

    result = _run_sync(source_root, destination, archive_root=archive_root, dry_run=False)

    combined_output = result.stdout + result.stderr
    assert result.returncode == 0, combined_output

    assert (destination / "skills" / "local-extra" / "SKILL.md").read_text(encoding="utf-8") == "# local extra skill\n"
    assert (destination / "skills" / "a" / "b.md").exists()
    assert (destination / "skills" / "c.py").exists()
    assert (destination / "skills" / "d" / "e.ps1").exists()

    assert (destination / "agents" / "custom.agent.md").read_text(encoding="utf-8") == "# custom agent\n"
    assert (destination / "agents" / "a" / "b.md").exists()
    assert (destination / "docs" / "furikaeri" / "local.md").read_text(encoding="utf-8") == "# local furikaeri\n"
    assert not archive_root.exists()


def test_sync_to_home_mirror_flag_is_compatibility_only(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    archive_root = tmp_path / "archive"
    destination.mkdir(parents=True)

    result = _run_sync(source_root, destination, archive_root=archive_root, dry_run=True, mirror=True)

    combined_output = result.stdout + result.stderr
    assert result.returncode == 0, combined_output
    assert "互換オプションです" in combined_output


def test_sync_to_home_verbose_log_shows_detailed_plan(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    archive_root = tmp_path / "archive"
    destination.mkdir(parents=True)

    result = _run_sync(
        source_root,
        destination,
        archive_root=archive_root,
        dry_run=True,
        verbose_log=True,
    )

    combined_output = result.stdout + result.stderr
    assert result.returncode == 0, combined_output
    assert "◆ 詳細ログ" in combined_output
    assert "[repo-template/" in combined_output


def test_sync_to_home_does_not_delete_home_only_furikaeri_docs(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    archive_root = tmp_path / "archive"
    destination.mkdir(parents=True)
    furikaeri_dir = destination / "docs" / "furikaeri"
    furikaeri_dir.mkdir(parents=True)
    user_doc = furikaeri_dir / "20260101-120000-my-session.md"
    user_doc.write_text("# user furikaeri\n", encoding="utf-8")

    result = _run_sync(source_root, destination, archive_root=archive_root, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert user_doc.exists(), "home-only furikaeri doc must not be deleted by sync"
