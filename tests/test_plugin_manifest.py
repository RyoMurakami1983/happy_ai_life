from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins"


def test_plugin_manifests_point_to_existing_distribution_dirs() -> None:
    manifest_paths = sorted(PLUGIN_DIR.glob("*/plugin.json"))

    assert {path.parent.name for path in manifest_paths} == {"happy-core", "happy-coding"}

    for manifest_path in manifest_paths:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["name"] == manifest_path.parent.name
        assert manifest["version"]
        assert manifest["description"]

        skills_dir = manifest_path.parent / manifest["skills"]
        assert skills_dir.is_dir()
        assert any(skills_dir.glob("*/SKILL.md"))

        agents = manifest.get("agents")
        if agents is not None:
            agents_dir = manifest_path.parent / agents
            assert agents_dir.is_dir()
            assert any(agents_dir.glob("*.agent.md"))

