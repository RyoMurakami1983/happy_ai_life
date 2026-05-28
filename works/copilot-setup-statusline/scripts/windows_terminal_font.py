from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


KNOWN_FONT_PATTERNS = {
    "MesloLGMNerdFont": "MesloLGM Nerd Font",
    "CaskaydiaMonoNerdFont": "CaskaydiaMono Nerd Font",
    "CaskaydiaCoveNerdFont": "CaskaydiaCove Nerd Font",
    "CascadiaCodeNerdFont": "Cascadia Code Nerd Font",
    "FiraCodeNerdFont": "FiraCode Nerd Font",
}


@dataclass(frozen=True)
class CandidateFace:
    origin: str
    face: str


def looks_like_nerd_font(face: object) -> bool:
    if not isinstance(face, str):
        return False
    lowered = face.casefold().strip()
    return "nerd font" in lowered or lowered.endswith(" nf")


def font_face(section: object) -> str | None:
    if not isinstance(section, dict):
        return None
    font = section.get("font")
    if not isinstance(font, dict):
        return None
    face = font.get("face")
    if isinstance(face, str) and face.strip():
        return face.strip()
    return None


def detect_installed_faces(font_dirs: list[Path]) -> list[str]:
    faces: set[str] = set()
    for directory in font_dirs:
        if not directory.is_dir():
            continue
        for marker, face in KNOWN_FONT_PATTERNS.items():
            try:
                if next(directory.glob(f"{marker}*.ttf"), None) is not None:
                    faces.add(face)
            except OSError:
                continue
    return sorted(faces)


def load_settings(path: Path) -> dict[str, Any]:
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"{path} could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON.") from exc
    if not isinstance(settings, dict):
        raise SystemExit(f"{path} must contain a JSON object.")
    return settings


def collect_candidates(settings: dict[str, Any], distro_name: str | None) -> list[CandidateFace]:
    profiles = settings.get("profiles")
    if not isinstance(profiles, dict):
        return []

    candidates: list[CandidateFace] = []
    defaults_face = font_face(profiles.get("defaults"))
    if defaults_face:
        candidates.append(CandidateFace("profiles.defaults.font.face", defaults_face))

    profile_list = profiles.get("list")
    if not isinstance(profile_list, list):
        return candidates

    wsl_profiles = [
        profile
        for profile in profile_list
        if isinstance(profile, dict) and profile.get("source") == "Microsoft.WSL"
    ]
    if distro_name:
        named_profiles = [profile for profile in wsl_profiles if profile.get("name") == distro_name]
        if named_profiles:
            wsl_profiles = named_profiles

    for profile in wsl_profiles:
        face = font_face(profile)
        if face:
            name = str(profile.get("name") or "<unnamed>")
            candidates.append(CandidateFace(f"WSL profile {name}", face))

    return candidates


def inspect_settings(
    settings_path: Path,
    distro_name: str | None,
    font_dirs: list[Path],
) -> dict[str, Any]:
    if not settings_path.exists():
        return {
            "settings_exists": False,
            "configured": False,
            "installed_faces": detect_installed_faces(font_dirs),
        }

    settings = load_settings(settings_path)
    candidates = collect_candidates(settings, distro_name)
    configured = next((candidate for candidate in candidates if looks_like_nerd_font(candidate.face)), None)
    result: dict[str, Any] = {
        "settings_exists": True,
        "configured": configured is not None,
        "installed_faces": detect_installed_faces(font_dirs),
    }
    if configured is not None:
        result["configured_origin"] = configured.origin
        result["configured_face"] = configured.face
    return result


def _ensure_font_section(section: dict[str, Any]) -> dict[str, Any]:
    font = section.get("font")
    if not isinstance(font, dict):
        font = {}
        section["font"] = font
    return font


def apply_font(settings_path: Path, distro_name: str | None, font_face_value: str) -> dict[str, Any]:
    settings = load_settings(settings_path)
    profiles = settings.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise SystemExit(f"{settings_path} profiles must be a JSON object.")

    defaults = profiles.setdefault("defaults", {})
    if not isinstance(defaults, dict):
        raise SystemExit(f"{settings_path} profiles.defaults must be a JSON object.")
    defaults_font = _ensure_font_section(defaults)
    defaults_font["face"] = font_face_value

    applied_to = ["profiles.defaults.font.face"]

    profile_list = profiles.get("list")
    if not isinstance(profile_list, list):
        profile_list = []
        profiles["list"] = profile_list

    wsl_profiles = [
        profile
        for profile in profile_list
        if isinstance(profile, dict) and profile.get("source") == "Microsoft.WSL"
    ]
    if distro_name:
        named_profiles = [profile for profile in wsl_profiles if profile.get("name") == distro_name]
        if named_profiles:
            wsl_profiles = named_profiles

    for profile in wsl_profiles:
        profile_font = _ensure_font_section(profile)
        profile_font["face"] = font_face_value
        applied_to.append(f"WSL profile {profile.get('name', '<unnamed>')}")

    backup_path = settings_path.with_name(
        f"{settings_path.name}.statusline-backup-{datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')}"
    )
    backup_path.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")
    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"updated": True, "backup_path": str(backup_path), "applied_to": applied_to}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and update Windows Terminal font settings.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--settings", required=True, type=Path)
    inspect_parser.add_argument("--distro")
    inspect_parser.add_argument("--font-dir", action="append", default=[], type=Path)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--settings", required=True, type=Path)
    apply_parser.add_argument("--distro")
    apply_parser.add_argument("--font-face", required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "inspect":
        result = inspect_settings(args.settings, args.distro, args.font_dir)
    else:
        result = apply_font(args.settings, args.distro, args.font_face)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
