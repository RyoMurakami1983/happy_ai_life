from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "home-template" / ".copilot" / "skills" / "pptx" / "scripts" / "clean.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pptx_clean", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_clean_rejects_symlinked_resource_directories(tmp_path: Path) -> None:
    module = _load_module()
    unpacked_dir = tmp_path / "unpacked"
    ppt_dir = unpacked_dir / "ppt"
    ppt_dir.mkdir(parents=True)
    (ppt_dir / "presentation.xml").write_text("<p:presentation/>", encoding="utf-8")
    (ppt_dir / "_rels").mkdir()
    (ppt_dir / "_rels" / "presentation.xml.rels").write_text(
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
        encoding="utf-8",
    )
    (unpacked_dir / "[Content_Types].xml").write_text("<Types/>", encoding="utf-8")

    external_media = tmp_path / "external-media"
    external_media.mkdir()
    external_file = external_media / "image1.png"
    external_file.write_bytes(b"png")

    symlink_dir = ppt_dir / "media"
    try:
        symlink_dir.symlink_to(external_media, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    with pytest.raises(ValueError, match="Symlinks are not supported"):
        module.clean_unused_files(unpacked_dir)

    assert external_file.exists()
