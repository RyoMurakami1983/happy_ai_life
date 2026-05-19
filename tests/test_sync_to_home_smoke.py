from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-to-home.ps1"


def _powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved is not None:
            return resolved
    pytest.skip("PowerShell executable not found")


@pytest.mark.skipif(os.name != "nt", reason="sync-to-home.ps1 smoke test runs through PowerShell on Windows")
def test_sync_to_home_dry_run_accepts_null_values_in_existing_config(tmp_path: Path) -> None:
    destination = tmp_path / ".copilot"
    destination.mkdir()
    (destination / "config.json").write_text(
        json.dumps({"permissions": {"allow": None}, "hooks": {}}),
        encoding="utf-8",
    )

    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-SourceRoot",
        str(ROOT),
        "-DestinationPath",
        str(destination),
        "-ArchiveRoot",
        str(tmp_path / "archives"),
        "-DryRun",
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "SYNC_STATS:" in completed.stdout
