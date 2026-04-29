from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "happy-ai-life" / "skills" / "pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
THUMBNAIL_SCRIPT = SCRIPTS_ROOT / "thumbnail.py"
BASE_VALIDATOR_SCRIPT = SCRIPTS_ROOT / "office" / "validators" / "base.py"
DOCX_VALIDATOR_SCRIPT = SCRIPTS_ROOT / "office" / "validators" / "docx.py"


def _load_module(module_name: str, script_path: Path):
    original_sys_path = sys.path.copy()
    try:
        assert script_path.exists()
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module(module_name)
    finally:
        sys.path[:] = original_sys_path


def test_validate_content_types_reports_parse_errors(tmp_path: Path, capsys) -> None:
    module = _load_module("office.validators.base", BASE_VALIDATOR_SCRIPT)
    unpacked_dir = tmp_path / "unpacked"
    ppt_dir = unpacked_dir / "ppt"
    ppt_dir.mkdir(parents=True)
    (unpacked_dir / "[Content_Types].xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
        <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
          <Default Extension="xml" ContentType="application/xml" />
        </Types>
        """,
        encoding="utf-8",
    )
    (ppt_dir / "presentation.xml").write_text("<broken", encoding="utf-8")

    validator = module.BaseSchemaValidator(unpacked_dir)

    assert validator.validate_content_types() is False
    captured = capsys.readouterr()
    assert "Error parsing XML" in captured.out


def test_repair_whitespace_preservation_reports_parse_errors(
    tmp_path: Path, capsys
) -> None:
    module = _load_module("office.validators.base", BASE_VALIDATOR_SCRIPT)
    unpacked_dir = tmp_path / "unpacked"
    word_dir = unpacked_dir / "word"
    word_dir.mkdir(parents=True)
    (word_dir / "document.xml").write_text("<broken", encoding="utf-8")

    validator = module.BaseSchemaValidator(unpacked_dir)

    assert validator.repair_whitespace_preservation() == 0
    captured = capsys.readouterr()
    assert "FAILED - Could not repair whitespace preservation" in captured.out


def test_validate_id_constraints_reports_parse_errors(tmp_path: Path, capsys) -> None:
    module = _load_module("office.validators.docx", DOCX_VALIDATOR_SCRIPT)
    unpacked_dir = tmp_path / "unpacked"
    word_dir = unpacked_dir / "word"
    word_dir.mkdir(parents=True)
    (word_dir / "document.xml").write_text("<broken", encoding="utf-8")

    validator = module.DOCXSchemaValidator(unpacked_dir)

    assert validator.validate_id_constraints() is False
    captured = capsys.readouterr()
    assert "Error parsing XML" in captured.out


def test_repair_durable_id_reports_parse_errors(tmp_path: Path, capsys) -> None:
    module = _load_module("office.validators.docx", DOCX_VALIDATOR_SCRIPT)
    unpacked_dir = tmp_path / "unpacked"
    word_dir = unpacked_dir / "word"
    word_dir.mkdir(parents=True)
    (word_dir / "document.xml").write_text("<broken", encoding="utf-8")

    validator = module.DOCXSchemaValidator(unpacked_dir)

    assert validator.repair_durableId() == 0
    captured = capsys.readouterr()
    assert "FAILED - Could not repair durableId" in captured.out


def test_build_slide_list_keeps_missing_slides_visible(tmp_path: Path) -> None:
    module = _load_module("thumbnail", THUMBNAIL_SCRIPT)
    visible_image = tmp_path / "slide-01.jpg"
    Image.new("RGB", (16, 9), color="white").save(visible_image)

    slides = module.build_slide_list(
        [
            {"name": "slide1.xml", "hidden": False},
            {"name": "slide2.xml", "hidden": False},
        ],
        [visible_image],
        tmp_path,
    )

    assert len(slides) == 2
    assert slides[0][1] == "slide1.xml"
    assert slides[1][1] == "slide2.xml (missing)"
    assert slides[1][0].exists()


def test_create_grid_rejects_empty_slide_list(tmp_path: Path) -> None:
    module = _load_module("thumbnail", THUMBNAIL_SCRIPT)

    with pytest.raises(RuntimeError, match="No slides available for thumbnail grid generation"):
        module.create_grid([], 3, module.THUMBNAIL_WIDTH)
