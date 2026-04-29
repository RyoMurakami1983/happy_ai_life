from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "happy-ai-life" / "skills" / "pptx" / "scripts" / "office" / "zip_utils.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pptx_zip_utils", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_safe_extractall_blocks_path_traversal(tmp_path: Path) -> None:
    module = _load_module()
    archive_path = tmp_path / "malicious.pptx"
    destination = tmp_path / "output"
    destination.mkdir()

    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("../evil.txt", "boom")

    with zipfile.ZipFile(archive_path, "r") as zf:
        try:
            module.safe_extractall(zf, destination)
        except ValueError as exc:
            assert "Unsafe archive member" in str(exc)
        else:
            raise AssertionError("expected path traversal to be rejected")

    assert not (tmp_path / "evil.txt").exists()
    assert list(destination.rglob("*")) == []
