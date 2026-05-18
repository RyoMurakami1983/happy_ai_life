from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD_ENGINE_PATH = ROOT / "scripts" / "guard_policy.py"


def ensure_guard_engine_for_script(script_path: Path) -> None:
    scripts_dir = script_path.parent
    hooks_dir = scripts_dir.parent
    layout_root = hooks_dir.parent

    if layout_root.name == ".copilot":
        destination = layout_root / "scripts" / "guard_policy.py"
    elif layout_root.name == ".github" and layout_root.parent is not None:
        destination = layout_root.parent / "scripts" / "guard_policy.py"
    else:
        return

    if destination.exists() and destination.resolve() == GUARD_ENGINE_PATH.resolve():
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GUARD_ENGINE_PATH, destination)
