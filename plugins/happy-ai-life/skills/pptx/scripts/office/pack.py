"""Pack a directory into a DOCX, PPTX, or XLSX file.

Validation with auto-repair currently applies to .docx and .pptx only. .xlsx
files are packed without validator-backed checks.

Usage:
    python scripts/office/pack.py <input_directory> <output_file> [--original <file>] [--validate true|false]

Examples:
    python scripts/office/pack.py unpacked/ output.docx --original input.docx
    python scripts/office/pack.py unpacked/ output.pptx --validate false
"""

import argparse
import os
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

import defusedxml.minidom


def _ensure_safe_input_tree(input_dir: Path) -> None:
    root = input_dir.resolve()
    if input_dir.is_symlink():
        raise ValueError(f"Symlinks are not supported in unpacked Office trees: {input_dir}")

    for path in input_dir.rglob("*"):
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"Unsafe path outside input directory: {path}")
        if path.is_symlink():
            raise ValueError(f"Symlinks are not supported in unpacked Office trees: {path}")


def _ensure_scripts_path() -> None:
    scripts_root = Path(__file__).resolve().parent.parent
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

from office.validators import DOCXSchemaValidator, PPTXSchemaValidator, RedliningValidator  # noqa: E402

def pack(
    input_directory: str,
    output_file: str,
    original_file: str | None = None,
    validate: bool = True,
    infer_author_func=None,
) -> tuple[None, str]:
    input_dir = Path(input_directory)
    output_path = Path(output_file)
    suffix = output_path.suffix.lower()

    if not input_dir.is_dir():
        return None, f"Error: {input_dir} is not a directory"

    if suffix not in {".docx", ".pptx", ".xlsx"}:
        return None, f"Error: {output_file} must be a .docx, .pptx, or .xlsx file"

    try:
        _ensure_safe_input_tree(input_dir)
    except ValueError as exc:
        return None, f"Error: {exc}"

    original_path = Path(original_file) if original_file is not None else None
    if original_path is not None and not original_path.exists():
        return None, f"Error: Original file does not exist: {original_path}"

    if validate:
        success, output = _run_validation(
            input_dir, original_path, suffix, infer_author_func
        )
        if output:
            print(output)
        if not success:
            return None, f"Error: Validation failed for {input_dir}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_content_dir = Path(temp_dir) / "content"
        shutil.copytree(input_dir, temp_content_dir)

        for pattern in ["*.xml", "*.rels"]:
            for xml_file in temp_content_dir.rglob(pattern):
                _condense_xml(xml_file)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in temp_content_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(temp_content_dir))

    return None, f"Successfully packed {input_dir} to {output_file}"


def _run_validation(
    unpacked_dir: Path,
    original_file: Path | None,
    suffix: str,
    infer_author_func=None,
) -> tuple[bool, str | None]:
    output_lines = []
    validators: list[
        DOCXSchemaValidator | PPTXSchemaValidator | RedliningValidator
    ] = []

    if suffix == ".docx":
        author = "Claude"
        if infer_author_func and original_file is not None:
            try:
                author = infer_author_func(unpacked_dir, original_file)
            except ValueError as e:
                print(f"Warning: {e} Using default author 'Claude'.", file=sys.stderr)

        validators = [
            DOCXSchemaValidator(unpacked_dir, original_file),
        ]
        if original_file is not None:
            validators.append(RedliningValidator(unpacked_dir, original_file, author=author))
    elif suffix == ".pptx":
        validators = [PPTXSchemaValidator(unpacked_dir, original_file)]

    if not validators:
        return True, None

    total_repairs = sum(v.repair() for v in validators)
    if total_repairs:
        output_lines.append(f"Auto-repaired {total_repairs} issue(s)")

    success = all(v.validate() for v in validators)

    if success:
        output_lines.append("All validations PASSED!")

    return success, "\n".join(output_lines) if output_lines else None


def _condense_xml(xml_file: Path) -> None:
    try:
        with open(xml_file, encoding="utf-8") as f:
            dom = defusedxml.minidom.parse(f)

        for element in dom.getElementsByTagName("*"):
            if element.tagName.endswith(":t"):
                continue

            for child in list(element.childNodes):
                if (
                    child.nodeType == child.TEXT_NODE
                    and child.nodeValue
                    and child.nodeValue.strip() == ""
                ) or child.nodeType == child.COMMENT_NODE:
                    element.removeChild(child)

        xml_file.write_bytes(dom.toxml(encoding="UTF-8"))
    except Exception as e:
        print(f"ERROR: Failed to parse {xml_file.name}: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Pack a directory into a DOCX, PPTX, or XLSX file "
            "(.docx/.pptx validation only)"
        )
    )
    parser.add_argument("input_directory", help="Unpacked Office document directory")
    parser.add_argument(
        "output_file",
        help="Output Office file (.docx/.pptx/.xlsx; validator-backed checks support .docx/.pptx)",
    )
    parser.add_argument(
        "--original",
        help="Original file for validation comparison",
    )
    parser.add_argument(
        "--validate",
        type=lambda x: x.lower() == "true",
        default=True,
        metavar="true|false",
        help="Run validation with auto-repair (default: true)",
    )
    args = parser.parse_args()

    _, message = pack(
        args.input_directory,
        args.output_file,
        original_file=args.original,
        validate=args.validate,
    )
    print(message)

    if "Error" in message:
        sys.exit(1)
