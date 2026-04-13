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
    (copilot_dir / "agents" / "sample.agent.md").write_text("# agent\n", encoding="utf-8")
    (copilot_dir / "docs" / "furikaeri" / ".gitkeep").write_text("\n", encoding="utf-8")
    (copilot_dir / "copilot-instructions.md").write_text("# instructions\n", encoding="utf-8")
    (copilot_dir / "mcp-config.sample.json").write_text("{}", encoding="utf-8")
    (copilot_dir / "config.json").write_text('{"runtime":true}', encoding="utf-8")
    (copilot_dir / "session-state").mkdir()
    return base


def test_sync_to_home_copies_only_whitelisted_targets(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    destination.mkdir(parents=True)
    (destination / "config.json").write_text('{"user":true}', encoding="utf-8")
    (destination / "session-state").mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")

    result = _run_sync(source_root, destination, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (destination / "skills" / "sample-skill" / "SKILL.md").exists()
    assert (destination / "agents" / "sample.agent.md").exists()
    assert (destination / "copilot-instructions.md").exists()
    assert (destination / "mcp-config.sample.json").exists()
    assert (destination / "docs" / "furikaeri" / ".gitkeep").exists()
    assert (destination / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert (destination / "config.json").read_text(encoding="utf-8") == '{"user":true}'
    assert (destination / "session-state").exists()


def test_sync_to_home_mirror_does_not_delete_existing_home_files(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    destination.mkdir(parents=True)
    (destination / "skills" / "custom-only").mkdir(parents=True)
    (destination / "skills" / "custom-only" / "SKILL.md").write_text("# custom\n", encoding="utf-8")
    (destination / "custom-root.txt").write_text("keep", encoding="utf-8")

    result = _run_sync(source_root, destination, dry_run=False, mirror=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "無視されます" in (result.stdout + result.stderr)
    assert (destination / "skills" / "custom-only" / "SKILL.md").exists()
    assert (destination / "custom-root.txt").read_text(encoding="utf-8") == "keep"


def test_sync_to_home_does_not_delete_home_only_furikaeri_docs(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    destination = tmp_path / "home"
    destination.mkdir(parents=True)
    # home 側にのみ存在するふりかえりドキュメント（ユーザーが作成したもの）
    furikaeri_dir = destination / "docs" / "furikaeri"
    furikaeri_dir.mkdir(parents=True)
    user_doc = furikaeri_dir / "20260101-120000-my-session.md"
    user_doc.write_text("# user furikaeri\n", encoding="utf-8")

    result = _run_sync(source_root, destination, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    # ホーム側のドキュメントは削除されていないこと
    assert user_doc.exists(), "home-only furikaeri doc must not be deleted by sync"
    # テンプレートの .gitkeep も追加されていること
    assert (furikaeri_dir / ".gitkeep").exists()
