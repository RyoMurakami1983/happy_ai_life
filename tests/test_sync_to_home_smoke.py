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


@pytest.mark.skipif(os.name != "nt", reason="sync-to-home.ps1 smoke test runs through PowerShell on Windows")
def test_sync_to_home_preserves_comment_prefixed_config_json(tmp_path: Path) -> None:
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
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    rendered = (destination / "config.json").read_text(encoding="utf-8")
    assert rendered.startswith("// User settings belong in settings.json.\n// This file is managed automatically.\n")
    config = json.loads("\n".join(rendered.splitlines()[2:]))
    assert config["hooks"]["preToolUse"][0]["bash"] == "echo keep"
    assert config["hooks"]["preToolUse"][-1]["env"]["HAPPY_AI_LIFE_HOOK_ID"] == "happy-ai-life-safety-guard"


@pytest.mark.skipif(os.name != "nt", reason="sync-to-home.ps1 smoke test runs through PowerShell on Windows")
def test_sync_to_home_writes_home_safety_guard_hook_file(tmp_path: Path) -> None:
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
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    hook_path = destination / "hooks" / "safety-guard.json"
    assert hook_path.exists()

    hook_doc = json.loads(hook_path.read_text(encoding="utf-8"))
    entry = hook_doc["hooks"]["preToolUse"][0]
    assert entry.get("env", {}).get("HAPPY_AI_LIFE_HOOK_ID") == "happy-ai-life-safety-guard"
    assert "bash" not in entry
    assert str(destination).lower() in entry["powershell"].lower()
    assert "guard_pre_tool.ps1" in entry["powershell"]
    assert ".github" not in entry["powershell"].lower()
