"""Safe ZIP extraction helpers for Office documents."""

from __future__ import annotations

import zipfile
from pathlib import Path


def safe_extractall(archive: zipfile.ZipFile, destination: Path) -> None:
    """Extract all members while rejecting path traversal attempts."""
    destination = destination.resolve()

    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if not target.is_relative_to(destination):
            raise ValueError(f"Unsafe archive member: {member.filename}")
        archive.extract(member, destination)
