from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_MAP = ROOT / "docs" / "SKILL_MAP.md"
PLUGIN_DIRS = (
    ROOT / "plugins" / "happy-core" / "skills",
    ROOT / "plugins" / "happy-coding" / "skills",
)


def test_skill_map_lists_every_distributed_skill_once() -> None:
    skill_map = SKILL_MAP.read_text(encoding="utf-8")
    skill_names = sorted(
        skill_dir.name
        for plugin_dir in PLUGIN_DIRS
        for skill_dir in plugin_dir.iterdir()
        if (skill_dir / "SKILL.md").is_file()
    )

    for skill_name in skill_names:
        assert skill_map.count(f"`{skill_name}`") >= 1


def test_skill_map_does_not_reference_missing_skill_directories() -> None:
    skill_map = SKILL_MAP.read_text(encoding="utf-8")
    existing_skill_names = {
        skill_dir.name
        for plugin_dir in PLUGIN_DIRS
        for skill_dir in plugin_dir.iterdir()
        if (skill_dir / "SKILL.md").is_file()
    }
    documented_skill_names = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", skill_map))

    allowed_non_skill_terms = {
        "skills",
        "skill-eval",
    }
    missing = documented_skill_names - existing_skill_names - allowed_non_skill_terms

    assert missing == set()
