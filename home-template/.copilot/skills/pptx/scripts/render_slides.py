"""Render PowerPoint slides to images with a background-safe fallback strategy.

Prefer headless LibreOffice + pdftoppm when available. On Windows, fall back to
hidden PowerPoint COM export if LibreOffice is unavailable.

Usage:
    python scripts/render_slides.py input.pptx
    python scripts/render_slides.py input.pptx slide --format jpeg --dpi 150
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal

from PIL import Image


def _ensure_scripts_path() -> None:
    scripts_root = Path(__file__).resolve().parent
    normalized_scripts_root = os.path.normcase(str(scripts_root))
    normalized_entries = {
        os.path.normcase(str(Path(entry).resolve()))
        for entry in sys.path
        if entry
    }
    if normalized_scripts_root not in normalized_entries:
        sys.path.insert(0, str(scripts_root))


if __package__ in {None, ""}:
    _ensure_scripts_path()

from office.soffice import get_soffice_env  # noqa: E402

ImageFormat = Literal["png", "jpeg"]
DEFAULT_DPI = 150
JPEG_QUALITY = 95


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Render PPTX slides to images. Prefers LibreOffice headless mode and "
            "falls back to hidden PowerPoint COM export on Windows."
        )
    )
    parser.add_argument("input", help="Input PowerPoint file (.pptx)")
    parser.add_argument(
        "output_prefix",
        nargs="?",
        default="slide",
        help="Output image prefix (default: slide)",
    )
    parser.add_argument(
        "--format",
        choices=("png", "jpeg"),
        default="png",
        help="Output image format (default: png)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"Render DPI for LibreOffice path (default: {DEFAULT_DPI})",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.exists() or input_path.suffix.lower() != ".pptx":
        print(f"Error: Invalid PowerPoint file: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        rendered_files = render_slides(
            input_path,
            Path(args.output_prefix),
            image_format=args.format,
            dpi=args.dpi,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Created {len(rendered_files)} image(s):")
    for rendered_file in rendered_files:
        print(f"  {rendered_file}")


def render_slides(
    input_path: Path,
    output_prefix: Path,
    *,
    image_format: ImageFormat = "png",
    dpi: int = DEFAULT_DPI,
) -> list[Path]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_output_prefix = Path(temp_dir) / output_prefix.name

        soffice_path = _find_soffice()
        if soffice_path is not None:
            try:
                rendered_files = _render_with_soffice(
                    soffice_path,
                    input_path,
                    temp_output_prefix,
                    image_format,
                    dpi,
                )
            except RuntimeError:
                if os.name != "nt":
                    raise
            else:
                return _publish_rendered_files(
                    rendered_files, output_prefix, image_format
                )

        if os.name == "nt":
            rendered_files = _render_with_powerpoint(
                input_path, temp_output_prefix, image_format
            )
            return _publish_rendered_files(rendered_files, output_prefix, image_format)

    raise RuntimeError(
        "No supported slide renderer found. Install LibreOffice (`soffice`) or "
        "run on Windows with Microsoft PowerPoint installed."
    )


def _find_soffice() -> Path | None:
    command = shutil.which("soffice")
    if command:
        return Path(command)

    if os.name != "nt":
        return None

    candidates = []
    for env_key in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env_key)
        if base:
            candidates.append(Path(base) / "LibreOffice" / "program" / "soffice.exe")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def _render_with_soffice(
    soffice_path: Path,
    input_path: Path,
    output_prefix: Path,
    image_format: ImageFormat,
    dpi: int,
) -> list[Path]:
    if shutil.which("pdftoppm") is None:
        raise RuntimeError(
            "pdftoppm is required for LibreOffice rendering but was not found in PATH."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path = temp_path / f"{input_path.stem}.pdf"

        pdf_result = subprocess.run(
            [
                str(soffice_path),
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temp_path),
                str(input_path),
            ],
            capture_output=True,
            text=True,
            env=get_soffice_env(),
        )
        if pdf_result.returncode != 0 or not pdf_path.exists():
            raise RuntimeError(
                _format_subprocess_error(
                    "LibreOffice PDF conversion failed", pdf_result
                )
            )

        image_flag, extension = _format_details(image_format)
        image_result = subprocess.run(
            [
                "pdftoppm",
                f"-{image_flag}",
                "-r",
                str(dpi),
                str(pdf_path),
                str(output_prefix),
            ],
            capture_output=True,
            text=True,
        )
        if image_result.returncode != 0:
            raise RuntimeError(
                _format_subprocess_error("Slide image conversion failed", image_result)
            )

    rendered_files = sorted(
        output_prefix.parent.glob(f"{output_prefix.name}-*.{extension}"),
        key=_slide_sort_key,
    )
    if not rendered_files:
        raise RuntimeError("Slide image conversion produced no output files.")

    return rendered_files


def _render_with_powerpoint(
    input_path: Path,
    output_prefix: Path,
    image_format: ImageFormat,
) -> list[Path]:
    powershell_path = shutil.which("powershell.exe") or shutil.which("powershell")
    if powershell_path is None:
        raise RuntimeError(
            "PowerPoint fallback requires powershell.exe, but it was not found."
        )

    helper_script = Path(__file__).with_name("export_slides_via_powerpoint.ps1")
    with tempfile.TemporaryDirectory() as temp_dir:
        export_dir = Path(temp_dir)
        result = subprocess.run(
            [
                powershell_path,
                "-Sta",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(helper_script),
                "-InputPath",
                str(input_path),
                "-OutputDir",
                str(export_dir),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                _format_subprocess_error("PowerPoint slide export failed", result)
            )

        exported_files = sorted(
            (path for path in export_dir.iterdir() if path.suffix.lower() == ".png"),
            key=_slide_sort_key,
        )
        if not exported_files:
            raise RuntimeError("PowerPoint fallback produced no PNG slides.")

        return _normalize_powerpoint_exports(
            exported_files, output_prefix, image_format
        )


def _normalize_powerpoint_exports(
    exported_files: list[Path],
    output_prefix: Path,
    image_format: ImageFormat,
) -> list[Path]:
    return _publish_rendered_files(exported_files, output_prefix, image_format)


def _publish_rendered_files(
    rendered_files: list[Path],
    output_prefix: Path,
    image_format: ImageFormat,
) -> list[Path]:
    _, extension = _format_details(image_format)
    normalized_files: list[Path] = []

    for index, exported_file in enumerate(rendered_files, start=1):
        normalized_path = output_prefix.parent / f"{output_prefix.name}-{index:02d}.{extension}"
        if image_format == "png":
            shutil.copyfile(exported_file, normalized_path)
        else:
            with Image.open(exported_file) as image:
                image.convert("RGB").save(
                    normalized_path,
                    "JPEG",
                    quality=JPEG_QUALITY,
                )
        normalized_files.append(normalized_path)

    _remove_stale_outputs(output_prefix, normalized_files)
    return normalized_files


def _remove_existing_outputs(output_prefix: Path) -> None:
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        for existing in output_prefix.parent.glob(f"{output_prefix.name}-{pattern}"):
            existing.unlink()


def _remove_stale_outputs(output_prefix: Path, keep_files: list[Path]) -> None:
    keep_names = {path.name for path in keep_files}
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        for existing in output_prefix.parent.glob(f"{output_prefix.name}-{pattern}"):
            if existing.name not in keep_names:
                existing.unlink()


def _format_details(image_format: ImageFormat) -> tuple[str, str]:
    if image_format == "jpeg":
        return "jpeg", "jpg"
    return "png", "png"


def _slide_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)(?!.*\d)", path.stem)
    if match is None:
        return (sys.maxsize, path.name.lower())
    return (int(match.group(1)), path.name.lower())


def _format_subprocess_error(
    prefix: str, result: subprocess.CompletedProcess[str]
) -> str:
    details = result.stderr.strip() or result.stdout.strip() or "unknown error"
    return f"{prefix}: {details}"


if __name__ == "__main__":
    main()
