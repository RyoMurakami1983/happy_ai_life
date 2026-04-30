from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "happy-core" / "skills" / "pptx" / "scripts" / "add_slide.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pptx_add_slide", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_duplicate_slide_rejects_path_traversal(tmp_path: Path) -> None:
    module = _load_module()
    unpacked_dir = tmp_path / "unpacked"
    slides_dir = unpacked_dir / "ppt" / "slides"
    rels_dir = slides_dir / "_rels"
    rels_dir.mkdir(parents=True)
    (unpacked_dir / "ppt" / "slideLayouts").mkdir(parents=True)
    (slides_dir / "slide1.xml").write_text("<p:sld/>", encoding="utf-8")

    with pytest.raises(SystemExit):
        module.duplicate_slide(unpacked_dir, "../outside.xml")

    assert not any(tmp_path.glob("outside.xml"))


def test_create_slide_from_layout_rejects_path_traversal(tmp_path: Path) -> None:
    module = _load_module()
    unpacked_dir = tmp_path / "unpacked"
    slides_dir = unpacked_dir / "ppt" / "slides"
    rels_dir = slides_dir / "_rels"
    layouts_dir = unpacked_dir / "ppt" / "slideLayouts"
    rels_dir.mkdir(parents=True)
    layouts_dir.mkdir(parents=True)
    (slides_dir / "slide1.xml").write_text("<p:sld/>", encoding="utf-8")
    (unpacked_dir / "ppt" / "presentation.xml").write_text(
        '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldIdLst><p:sldId id="256" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></p:sldIdLst></p:presentation>',
        encoding="utf-8",
    )
    (unpacked_dir / "ppt" / "_rels").mkdir(parents=True)
    (unpacked_dir / "ppt" / "_rels" / "presentation.xml.rels").write_text(
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>',
        encoding="utf-8",
    )

    with pytest.raises(SystemExit):
        module.create_slide_from_layout(unpacked_dir, "../outside.xml")

    assert not any(tmp_path.glob("outside.xml"))
