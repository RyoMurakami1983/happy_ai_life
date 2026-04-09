from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "home-template" / ".copilot" / "skills" / "pptx" / "scripts" / "office" / "pack.py"
SCRIPTS_ROOT = SCRIPT.parents[1]


def _load_module():
    original_sys_path = sys.path.copy()
    try:
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        spec = importlib.util.spec_from_file_location("pptx_pack", SCRIPT)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = original_sys_path


def test_pack_returns_error_for_missing_original_file(tmp_path: Path) -> None:
    module = _load_module()
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "[Content_Types].xml").write_text("<Types/>", encoding="utf-8")

    _, message = module.pack(
        str(input_dir),
        str(tmp_path / "output.pptx"),
        original_file=str(tmp_path / "missing.pptx"),
        validate=True,
    )

    assert message == f"Error: Original file does not exist: {tmp_path / 'missing.pptx'}"


def test_pack_runs_validation_without_original_file(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "[Content_Types].xml").write_text("<Types/>", encoding="utf-8")

    calls: list[tuple[Path, Path | None, str]] = []

    def fake_run_validation(unpacked_dir: Path, original_file: Path | None, suffix: str, infer_author_func=None):
        calls.append((unpacked_dir, original_file, suffix))
        return True, None

    monkeypatch.setattr(module, "_run_validation", fake_run_validation)

    _, message = module.pack(
        str(input_dir),
        str(tmp_path / "output.pptx"),
        validate=True,
    )

    assert message == f"Successfully packed {input_dir} to {tmp_path / 'output.pptx'}"
    assert calls == [(input_dir, None, ".pptx")]


def test_load_module_restores_sys_path() -> None:
    original_sys_path = sys.path.copy()

    _load_module()

    assert sys.path == original_sys_path
