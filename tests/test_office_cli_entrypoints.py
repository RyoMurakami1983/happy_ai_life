from __future__ import annotations

import importlib.util
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "home-template" / ".copilot" / "skills" / "pptx"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
PACK_SCRIPT = SCRIPTS_ROOT / "office" / "pack.py"
UNPACK_SCRIPT = SCRIPTS_ROOT / "office" / "unpack.py"
VALIDATE_SCRIPT = SCRIPTS_ROOT / "office" / "validate.py"
REDLINING_SCRIPT = SCRIPTS_ROOT / "office" / "validators" / "redlining.py"


def _load_module(module_name: str, script_path: Path):
    sys.path.insert(0, str(SCRIPTS_ROOT))
    try:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def _run_skill_script(script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=SKILL_ROOT,
        capture_output=True,
        text=True,
    )


def test_pack_script_runs_via_documented_path(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    result = _run_skill_script(
        PACK_SCRIPT,
        str(input_dir),
        str(tmp_path / "output.pptx"),
        "--validate",
        "false",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Successfully packed" in result.stdout
    assert "ModuleNotFoundError" not in result.stdout + result.stderr


def test_unpack_script_runs_via_documented_path(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.pptx"

    result = _run_skill_script(
        UNPACK_SCRIPT,
        str(missing_file),
        str(tmp_path / "unpacked"),
    )

    assert result.returncode == 1
    assert f"Error: {missing_file} does not exist" in result.stdout
    assert "ModuleNotFoundError" not in result.stdout + result.stderr


def test_validate_script_runs_via_documented_path(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.pptx"

    result = _run_skill_script(VALIDATE_SCRIPT, str(missing_file))

    assert result.returncode == 1
    assert f"Error: {missing_file} does not exist" in result.stderr
    assert "ModuleNotFoundError" not in result.stdout + result.stderr


def test_unpack_pretty_print_warns_for_invalid_xml(tmp_path: Path, capsys) -> None:
    module = _load_module("pptx_unpack", UNPACK_SCRIPT)
    xml_file = tmp_path / "broken.xml"
    xml_file.write_text("<broken", encoding="utf-8")

    module._pretty_print_xml(xml_file)

    captured = capsys.readouterr()
    assert f"Warning: Skipped pretty-printing for {xml_file}" in captured.err


def test_unpack_escape_smart_quotes_warns_for_invalid_utf8(
    tmp_path: Path, capsys
) -> None:
    module = _load_module("pptx_unpack_quotes", UNPACK_SCRIPT)
    xml_file = tmp_path / "broken.xml"
    xml_file.write_bytes(b"\x80")

    module._escape_smart_quotes(xml_file)

    captured = capsys.readouterr()
    assert f"Warning: Skipped smart-quote escaping for {xml_file}" in captured.err


def test_redlining_validator_reports_fast_path_skip_reason(
    tmp_path: Path, capsys
) -> None:
    module = _load_module("pptx_redlining", REDLINING_SCRIPT)
    unpacked_dir = tmp_path / "unpacked"
    word_dir = unpacked_dir / "word"
    word_dir.mkdir(parents=True)
    (word_dir / "document.xml").write_text("<w:document", encoding="utf-8")

    original_docx = tmp_path / "original.docx"
    with zipfile.ZipFile(original_docx, "w") as zf:
        zf.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body/></w:document>',
        )

    validator = module.RedliningValidator(unpacked_dir, original_docx, verbose=True)

    assert validator.validate() is False

    captured = capsys.readouterr()
    assert "WARNING - Skipping fast-path tracked change detection" in captured.out
    assert "FAILED - Error parsing XML files:" in captured.out
