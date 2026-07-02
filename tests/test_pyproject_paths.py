from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"


def test_ty_extra_paths_point_to_existing_directories() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    environment = pyproject["tool"]["ty"]["environment"]
    extra_paths = environment.get("extra-paths", [])

    assert isinstance(extra_paths, list)

    for relative_path in extra_paths:
        assert isinstance(relative_path, str)
        assert (ROOT / relative_path).is_dir(), (
            f"Missing ty extra-path directory: {relative_path}"
        )
