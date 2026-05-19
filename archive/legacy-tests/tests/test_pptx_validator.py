from __future__ import annotations

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "plugins" / "happy-core" / "skills" / "pptx" / "scripts"


def _load_module():
    original_sys_path = sys.path.copy()
    try:
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module("office.validators.pptx")
    finally:
        sys.path[:] = original_sys_path


def test_notes_slide_targets_are_normalized_as_zip_paths(
    tmp_path: Path, capsys
) -> None:
    module = _load_module()
    rels_dir = tmp_path / "ppt" / "slides" / "_rels"
    rels_dir.mkdir(parents=True)

    rels_template = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" '
        'Target="{target}"/>'
        "</Relationships>"
    )
    (rels_dir / "slide1.xml.rels").write_text(
        rels_template.format(target="../notesSlides/shared/../notesSlide1.xml"),
        encoding="utf-8",
    )
    (rels_dir / "slide2.xml.rels").write_text(
        rels_template.format(target="../notesSlides/notesSlide1.xml"),
        encoding="utf-8",
    )

    validator = module.PPTXSchemaValidator(tmp_path)

    assert validator.validate_notes_slide_references() is False

    captured = capsys.readouterr()
    assert (
        "Notes slide 'ppt/notesSlides/notesSlide1.xml' is referenced by multiple slides: "
        "slide1, slide2"
    ) in captured.out
    assert "Each slide may optionally have its own notes slide file." in captured.out
