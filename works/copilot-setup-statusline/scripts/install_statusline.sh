#!/usr/bin/env bash
set -euo pipefail

copilot_dir="${1:-"$HOME/.copilot"}"
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
skill_dir="$(CDPATH= cd -- "$script_dir/.." && pwd)"
assets_dir="$skill_dir/assets"
settings_path="$copilot_dir/settings.json"

is_truthy() {
  local normalized
  normalized="$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')"
  case "$normalized" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

is_wsl() {
  if is_truthy "${COPILOT_STATUSLINE_FORCE_WSL:-0}"; then
    return 0
  fi
  if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    return 0
  fi
  grep -qi microsoft /proc/version 2>/dev/null
}

normalize_wsl_path() {
  local raw_path="$1"
  if [[ -z "$raw_path" ]]; then
    return 1
  fi
  if [[ -e "$raw_path" ]]; then
    printf '%s\n' "$raw_path"
    return 0
  fi
  if command -v wslpath >/dev/null 2>&1; then
    local converted
    converted="$(wslpath -u "$raw_path" 2>/dev/null || true)"
    if [[ -n "$converted" ]]; then
      printf '%s\n' "$converted"
      return 0
    fi
  fi
  return 1
}

show_oh_my_posh_status() {
  if command -v oh-my-posh >/dev/null 2>&1; then
    local version
    version="$(oh-my-posh version 2>/dev/null | head -n 1 || true)"
    printf 'Found oh-my-posh %s\n' "${version:-unknown version}"
    return
  fi

  printf '%s\n' 'Warning: oh-my-posh is not installed yet. The statusline files were installed, but icon rendering needs oh-my-posh.' >&2
  printf '%s\n' 'Install it with the official command after ensuring curl, unzip, realpath, and dirname are available:' >&2
  printf '%s\n' '  curl -s https://ohmyposh.dev/install.sh | bash -s' >&2
}

resolve_windows_terminal_settings_path() {
  if [[ -n "${COPILOT_STATUSLINE_WINDOWS_TERMINAL_SETTINGS:-}" ]]; then
    local converted_override
    converted_override="$(normalize_wsl_path "${COPILOT_STATUSLINE_WINDOWS_TERMINAL_SETTINGS}" || true)"
    if [[ -n "$converted_override" && -f "$converted_override" ]]; then
      printf '%s\n' "$converted_override"
      return 0
    fi
    return 1
  fi

  if ! command -v powershell.exe >/dev/null 2>&1; then
    return 1
  fi

  local ps_script
  ps_script="$(cat <<'PS'
$paths = @(
  (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'),
  (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json'),
  (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json')
)

$match = $paths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($match) {
  Write-Output $match
}
PS
)"

  local raw_path converted_path
  while IFS= read -r raw_path; do
    converted_path="$(normalize_wsl_path "$raw_path" || true)"
    if [[ -n "$converted_path" && -f "$converted_path" ]]; then
      printf '%s\n' "$converted_path"
      return 0
    fi
  done < <(powershell.exe -NoProfile -Command "$ps_script" | tr -d '\r')

  return 1
}

resolve_windows_font_dirs() {
  local found_any=1
  if [[ -n "${COPILOT_STATUSLINE_WINDOWS_FONT_DIRS:-}" ]]; then
    local raw_path converted_path
    local separated_paths
    if [[ "${COPILOT_STATUSLINE_WINDOWS_FONT_DIRS}" == *$'\n'* ]]; then
      separated_paths="${COPILOT_STATUSLINE_WINDOWS_FONT_DIRS}"
    else
      separated_paths="$(tr ';' '\n' <<<"${COPILOT_STATUSLINE_WINDOWS_FONT_DIRS}")"
    fi
    while IFS= read -r raw_path; do
      converted_path="$(normalize_wsl_path "$raw_path" || true)"
      if [[ -n "$converted_path" && -d "$converted_path" ]]; then
        printf '%s\n' "$converted_path"
        found_any=0
      fi
    done <<<"$separated_paths"
    return "$found_any"
  fi

  if ! command -v powershell.exe >/dev/null 2>&1; then
    return 1
  fi

  local ps_script
  ps_script="$(cat <<'PS'
$dirs = @(
  (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'),
  (Join-Path $env:WINDIR 'Fonts')
)

foreach ($dir in $dirs) {
  if (Test-Path -LiteralPath $dir) {
    Write-Output $dir
  }
}
PS
)"

  local raw_path converted_path
  while IFS= read -r raw_path; do
    converted_path="$(normalize_wsl_path "$raw_path" || true)"
    if [[ -n "$converted_path" && -d "$converted_path" ]]; then
      printf '%s\n' "$converted_path"
      found_any=0
    fi
  done < <(powershell.exe -NoProfile -Command "$ps_script" | tr -d '\r')
  return "$found_any"
}

show_wsl_host_font_status() {
  if ! is_wsl; then
    return
  fi

  printf '%s\n' 'WSL note: icon rendering depends on the host terminal font on Windows, not a font installed inside WSL.'

  local settings_file
  settings_file="$(resolve_windows_terminal_settings_path || true)"
  if [[ -z "$settings_file" ]]; then
    printf '%s\n' 'Warning: Windows Terminal settings.json was not found from WSL. If you use Windows Terminal, set its font.face to a Nerd Font on the host.' >&2
    return
  fi

  local font_dirs
  font_dirs="$(resolve_windows_font_dirs || true)"
  if [[ -z "$font_dirs" ]]; then
    printf '%s\n' 'Warning: Windows font directories could not be inspected from WSL. Check the host terminal font manually.' >&2
    return
  fi

  COPILOT_STATUSLINE_WINDOWS_FONT_DIRS="${font_dirs}" python3 - "$settings_file" "${WSL_DISTRO_NAME:-}" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def looks_like_nerd_font(face: object) -> bool:
    if not isinstance(face, str):
        return False
    lower = face.casefold()
    return "nerd font" in lower or lower.endswith(" nf")


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


def detect_installed_faces(font_dirs: list[str]) -> list[str]:
    known_patterns = {
        "MesloLGMNerdFont": "MesloLGM Nerd Font",
        "CaskaydiaMonoNerdFont": "CaskaydiaMono Nerd Font",
        "CaskaydiaCoveNerdFont": "CaskaydiaCove Nerd Font",
        "CascadiaCodeNerdFont": "Cascadia Code Nerd Font",
        "FiraCodeNerdFont": "FiraCode Nerd Font",
    }
    faces: set[str] = set()
    for raw_dir in font_dirs:
        if not raw_dir:
            continue
        directory = Path(raw_dir)
        if not directory.is_dir():
            continue
        for marker, face in known_patterns.items():
            try:
                if next(directory.glob(f"{marker}*.ttf"), None) is not None:
                    faces.add(face)
            except OSError:
                continue
    return sorted(faces)


settings_path = Path(sys.argv[1])
distro_name = sys.argv[2]
font_dirs = [entry for entry in os.environ.get("COPILOT_STATUSLINE_WINDOWS_FONT_DIRS", "").splitlines() if entry]

try:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    print(f"Warning: {settings_path} could not be read as JSON. Check the host terminal font manually.", file=sys.stderr)
    raise SystemExit(0)

profiles = settings.get("profiles")
if not isinstance(profiles, dict):
    print(f"Warning: {settings_path} has no profiles object. Check the host terminal font manually.", file=sys.stderr)
    raise SystemExit(0)

defaults_face = font_face(profiles.get("defaults"))
profile_list = profiles.get("list")
if not isinstance(profile_list, list):
    profile_list = []

wsl_profiles = [profile for profile in profile_list if isinstance(profile, dict) and profile.get("source") == "Microsoft.WSL"]
if distro_name:
    matched = [profile for profile in wsl_profiles if profile.get("name") == distro_name]
    if matched:
        wsl_profiles = matched

candidates: list[tuple[str, str]] = []
if defaults_face:
    candidates.append(("profiles.defaults.font.face", defaults_face))
for profile in wsl_profiles:
    face = font_face(profile)
    if face:
        candidates.append((f"WSL profile {profile.get('name', '<unnamed>')}", face))

configured = next(((origin, face) for origin, face in candidates if looks_like_nerd_font(face)), None)
if configured:
    print(f"Windows Terminal font check: OK ({configured[1]} via {configured[0]}).")
    raise SystemExit(0)

installed_faces = detect_installed_faces(font_dirs)
if installed_faces:
    print("Warning: host Nerd Fonts were detected, but the Windows Terminal defaults/WSL profile do not appear to use one.", file=sys.stderr)
    print(f"Detected host Nerd Fonts: {', '.join(installed_faces[:3])}", file=sys.stderr)
    print(f"Set profiles.defaults.font.face or the WSL profile font.face in {settings_path}.", file=sys.stderr)
    raise SystemExit(0)

if not font_dirs:
    print("Warning: Windows font directories could not be inspected from WSL. Check the host terminal font manually.", file=sys.stderr)
    raise SystemExit(0)

print("Warning: no host Nerd Font was detected in the Windows font directories that were inspected.", file=sys.stderr)
print("Install one on Windows first (recommended: run 'oh-my-posh.exe font install meslo' in PowerShell), then set Windows Terminal font.face.", file=sys.stderr)
PY
}

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'python3 3.10+ is required to install Copilot statusline.' >&2
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  printf '%s\n' 'python3 3.10+ is required to install Copilot statusline.' >&2
  exit 1
fi

mkdir -p "$copilot_dir"

cp -f "$assets_dir/statusline.sh" "$copilot_dir/statusline.sh"
cp -f "$assets_dir/statusline.omp.json" "$copilot_dir/statusline.omp.json"
chmod +x "$copilot_dir/statusline.sh"

if [[ -f "$settings_path" ]]; then
  backup="$settings_path.statusline-backup-$(date +%Y%m%dT%H%M%S%z)"
  cp -f "$settings_path" "$backup"
fi

python3 - "$settings_path" "$copilot_dir/statusline.sh" <<'PY'
from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
import sys


settings_path = Path(sys.argv[1])
command_path = sys.argv[2]

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise SystemExit(f"{settings_path} is not valid JSON. Fix or restore it before re-running.") from exc
else:
    settings = {}

if not isinstance(settings, dict):
    raise SystemExit(f"{settings_path} must contain a JSON object.")

status_line = settings.setdefault("statusLine", {})
if not isinstance(status_line, dict):
    raise SystemExit(f"{settings_path} statusLine must be a JSON object.")

status_line["type"] = "command"
status_line["command"] = command_path
status_line["padding"] = 1

feature_flags = settings.setdefault("feature_flags", {})
if not isinstance(feature_flags, dict):
    raise SystemExit(f"{settings_path} feature_flags must be a JSON object.")

enabled = feature_flags.setdefault("enabled", [])
if not isinstance(enabled, list):
    raise SystemExit(f"{settings_path} feature_flags.enabled must be a JSON array.")

if "STATUS_LINE" not in enabled:
    enabled.append("STATUS_LINE")

settings["experimental"] = True
settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

printf 'Installed Copilot statusline to %s\n' "$copilot_dir"
show_oh_my_posh_status
show_wsl_host_font_status
printf 'Run /restart in Copilot CLI if it is already open.\n'
