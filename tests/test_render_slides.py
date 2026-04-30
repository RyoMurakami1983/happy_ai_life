from __future__ import annotations

import importlib.util
import sys
import subprocess
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "plugins"
    / "happy-core"
    / "skills"
    / "pptx"
    / "scripts"
    / "render_slides.py"
)
SCRIPTS_ROOT = SCRIPT.parent


def _load_module(module_name: str):
    original_sys_path = sys.path.copy()
    try:
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        spec = importlib.util.spec_from_file_location(module_name, SCRIPT)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = original_sys_path


def test_render_slides_prefers_soffice(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("pptx_render_soffice")
    input_file = tmp_path / "deck.pptx"
    input_file.write_bytes(b"pptx")
    source_dir = tmp_path / "rendered"
    source_dir.mkdir()
    source = [source_dir / "slide-01.png"]
    source[0].write_bytes(b"png")
    expected = [tmp_path / "slide-01.png"]

    monkeypatch.setattr(
        module,
        "_find_soffice",
        lambda: Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    )
    monkeypatch.setattr(
        module,
        "_render_with_soffice",
        lambda soffice_path, input_path, output_prefix, image_format, dpi: source,
    )

    result = module.render_slides(input_file, tmp_path / "slide")

    assert result == expected


@pytest.mark.skipif(sys.platform != "win32", reason="PowerPoint fallback is Windows-only")
def test_render_slides_falls_back_to_powerpoint_on_windows(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_module("pptx_render_powerpoint")
    input_file = tmp_path / "deck.pptx"
    input_file.write_bytes(b"pptx")
    source_dir = tmp_path / "rendered"
    source_dir.mkdir()
    source = [source_dir / "slide-01.png"]
    source[0].write_bytes(b"png")
    expected = [tmp_path / "slide-01.png"]

    monkeypatch.setattr(module, "_find_soffice", lambda: None)
    monkeypatch.setattr(
        module,
        "_render_with_powerpoint",
        lambda input_path, output_prefix, image_format: source,
    )

    result = module.render_slides(input_file, tmp_path / "slide")

    assert result == expected


@pytest.mark.skipif(sys.platform != "win32", reason="PowerPoint fallback is Windows-only")
def test_render_slides_errors_when_no_renderer(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("pptx_render_missing")
    input_file = tmp_path / "deck.pptx"
    input_file.write_bytes(b"pptx")
    existing = tmp_path / "slide-01.png"
    existing.write_bytes(b"keep")

    monkeypatch.setattr(module, "_find_soffice", lambda: None)
    monkeypatch.setattr(
        module,
        "_render_with_powerpoint",
        lambda input_path, output_prefix, image_format: (_ for _ in ()).throw(
            RuntimeError("PowerPoint fallback requires powershell.exe, but it was not found.")
        ),
    )

    with pytest.raises(RuntimeError, match="PowerPoint fallback requires powershell.exe"):
        module.render_slides(input_file, tmp_path / "slide")

    assert existing.read_bytes() == b"keep"


@pytest.mark.skipif(sys.platform != "win32", reason="PowerPoint fallback is Windows-only")
def test_render_slides_falls_back_to_powerpoint_if_soffice_fails_on_windows(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_module("pptx_render_soffice_fallback")
    input_file = tmp_path / "deck.pptx"
    input_file.write_bytes(b"pptx")
    source_dir = tmp_path / "rendered"
    source_dir.mkdir()
    source = [source_dir / "slide-01.png"]
    source[0].write_bytes(b"png")
    expected = [tmp_path / "slide-01.png"]

    monkeypatch.setattr(
        module,
        "_find_soffice",
        lambda: Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    )
    monkeypatch.setattr(
        module,
        "_render_with_soffice",
        lambda soffice_path, input_path, output_prefix, image_format, dpi: (_ for _ in ()).throw(
            RuntimeError("LibreOffice PDF conversion failed: missing pdftoppm")
        ),
    )
    monkeypatch.setattr(
        module,
        "_render_with_powerpoint",
        lambda input_path, output_prefix, image_format: source,
    )

    result = module.render_slides(input_file, tmp_path / "slide")

    assert result == expected


def test_render_with_soffice_uses_timeout(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("pptx_render_timeout_soffice")
    input_file = tmp_path / "deck.pptx"
    input_file.write_bytes(b"pptx")
    output_prefix = tmp_path / "slide"
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(module.shutil, "which", lambda name: "pdftoppm" if name == "pdftoppm" else None)

    def fake_run(cmd, **kwargs):
        calls.append((list(cmd), kwargs))
        if cmd[0] == "pdftoppm":
            prefix = Path(cmd[-1])
            (prefix.parent / f"{prefix.name}-01.jpg").write_bytes(b"jpg")
        else:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            pdf_path = outdir / f"{input_file.stem}.pdf"
            pdf_path.write_bytes(b"%PDF")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module._render_with_soffice(
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        input_file,
        output_prefix,
        "jpeg",
        module.DEFAULT_DPI,
    )

    assert result == [tmp_path / "slide-01.jpg"]
    assert all(call_kwargs["timeout"] == module.SUBPROCESS_TIMEOUT_SECONDS for _, call_kwargs in calls)


@pytest.mark.skipif(sys.platform != "win32", reason="PowerPoint fallback is Windows-only")
def test_render_with_powerpoint_uses_timeout(monkeypatch, tmp_path: Path) -> None:
    module = _load_module("pptx_render_timeout_powerpoint")
    input_file = tmp_path / "deck.pptx"
    input_file.write_bytes(b"pptx")
    output_prefix = tmp_path / "slide"
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(module.shutil, "which", lambda name: r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")

    def fake_run(cmd, **kwargs):
        calls.append((list(cmd), kwargs))
        export_dir = Path(cmd[cmd.index("-OutputDir") + 1])
        (export_dir / "スライド1.png").write_bytes(b"png")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module._render_with_powerpoint(input_file, output_prefix, "png")

    assert result == [tmp_path / "slide-01.png"]
    assert calls and calls[0][1]["timeout"] == module.SUBPROCESS_TIMEOUT_SECONDS


def test_normalize_powerpoint_exports_sorts_and_renames(tmp_path: Path) -> None:
    module = _load_module("pptx_render_normalize")
    export_dir = tmp_path / "exported"
    export_dir.mkdir()
    for name in ("スライド2.PNG", "スライド1.PNG"):
        Image.new("RGB", (4, 4), color="white").save(export_dir / name)

    normalized = module._normalize_powerpoint_exports(
        sorted(export_dir.iterdir(), key=module._slide_sort_key),
        tmp_path / "slide",
        "png",
    )

    assert [path.name for path in normalized] == ["slide-01.png", "slide-02.png"]
    assert all(path.exists() for path in normalized)
