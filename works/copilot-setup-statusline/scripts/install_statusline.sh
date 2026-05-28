#!/usr/bin/env bash
set -euo pipefail

copilot_dir="${1:-"$HOME/.copilot"}"
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
skill_dir="$(CDPATH= cd -- "$script_dir/.." && pwd)"
assets_dir="$skill_dir/assets"
settings_path="$copilot_dir/settings.json"
windows_terminal_helper="$script_dir/windows_terminal_font.py"
recommended_font_face="MesloLGM Nerd Font"
recommended_font_slug="meslo"
oh_my_posh_install_dir="${COPILOT_STATUSLINE_OH_MY_POSH_INSTALL_DIR:-$HOME/.local/bin}"

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

has_command() {
  command -v "$1" >/dev/null 2>&1
}

detect_arch() {
  local arch
  arch="$(uname -m | tr '[:upper:]' '[:lower:]')"
  case "$arch" in
    x86_64) arch="amd64" ;;
    armv*) arch="arm" ;;
    arm64|aarch64) arch="arm64" ;;
  esac
  printf '%s\n' "$arch"
}

detect_platform() {
  local platform
  platform="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$platform" in
    linux|darwin) ;;
    *) return 1 ;;
  esac
  printf '%s\n' "$platform"
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
  if has_command oh-my-posh; then
    local version
    version="$(oh-my-posh version 2>/dev/null | head -n 1 || true)"
    printf 'Found oh-my-posh %s\n' "${version:-unknown version}"
    return
  fi

  printf '%s\n' 'Warning: oh-my-posh is not installed yet. The statusline files were installed, but icon rendering needs oh-my-posh.' >&2
  printf '%s\n' 'Install it with either the official installer or a direct binary download:' >&2
  printf '%s\n' '  curl -s https://ohmyposh.dev/install.sh | bash -s' >&2
  printf '%s\n' '  curl -fsSL https://cdn.ohmyposh.dev/releases/latest/posh-linux-amd64 -o "$HOME/.local/bin/oh-my-posh" && chmod +x "$HOME/.local/bin/oh-my-posh"' >&2
}

install_oh_my_posh_binary_fallback() {
  local platform arch target url installed_path
  platform="$(detect_platform || true)"
  arch="$(detect_arch)"
  if [[ -z "$platform" ]]; then
    printf '%s\n' 'Warning: this platform is not supported by the direct oh-my-posh fallback installer.' >&2
    return 1
  fi

  target="${platform}-${arch}"
  url="https://cdn.ohmyposh.dev/releases/latest/posh-${target}"
  installed_path="$oh_my_posh_install_dir/oh-my-posh"

  printf 'Falling back to direct oh-my-posh binary download for %s\n' "$target"
  if curl -fsSL "$url" -o "$installed_path"; then
    chmod +x "$installed_path"
    PATH="$oh_my_posh_install_dir:$PATH"
    export PATH
    printf '%s\n' "$installed_path"
    return 0
  fi

  return 1
}

ensure_oh_my_posh() {
  if has_command oh-my-posh; then
    command -v oh-my-posh
    return 0
  fi

  if ! has_command curl; then
    printf '%s\n' 'Warning: curl was not found, so oh-my-posh could not be installed automatically.' >&2
    return 1
  fi

  mkdir -p "$oh_my_posh_install_dir"

  if has_command unzip && has_command realpath && has_command dirname; then
    printf 'Installing oh-my-posh into %s with the official installer\n' "$oh_my_posh_install_dir"
    if curl -fsSL https://ohmyposh.dev/install.sh | bash -s -- -d "$oh_my_posh_install_dir"; then
      local installed_path="$oh_my_posh_install_dir/oh-my-posh"
      if [[ -x "$installed_path" ]]; then
        PATH="$oh_my_posh_install_dir:$PATH"
        export PATH
        printf '%s\n' "$installed_path"
        return 0
      fi
    fi
    printf '%s\n' 'Warning: the official oh-my-posh installer failed, so a direct binary fallback will be tried.' >&2
  else
    printf '%s\n' 'Info: unzip/realpath/dirname is incomplete, so a direct oh-my-posh binary fallback will be used.' >&2
  fi

  if install_oh_my_posh_binary_fallback >/dev/null; then
    command -v oh-my-posh
    return 0
  fi

  printf '%s\n' 'Warning: oh-my-posh auto-install failed. Install it manually if icon rendering is still unavailable.' >&2
  return 1
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

  local inspect_args=("$windows_terminal_helper" "inspect" "--settings" "$settings_file")
  while IFS= read -r font_dir; do
    inspect_args+=("--font-dir" "$font_dir")
  done <<<"$font_dirs"
  if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    inspect_args+=("--distro" "$WSL_DISTRO_NAME")
  fi

  local inspect_json
  inspect_json="$(python3 "${inspect_args[@]}")"
  local configured installed_faces_count configured_face configured_origin target_font_face
  configured="$(python3 -c 'import json,sys; print("1" if json.load(sys.stdin).get("configured") else "0")' <<<"$inspect_json")"
  if [[ "$configured" == "1" ]]; then
    configured_face="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("configured_face",""))' <<<"$inspect_json")"
    configured_origin="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("configured_origin",""))' <<<"$inspect_json")"
    printf 'Windows Terminal font check: OK (%s via %s).\n' "$configured_face" "$configured_origin"
    return
  fi

  installed_faces_count="$(python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("installed_faces", [])))' <<<"$inspect_json")"
  if [[ "$installed_faces_count" == "0" ]]; then
    if command -v oh-my-posh.exe >/dev/null 2>&1; then
      printf 'Installing %s on the Windows host via oh-my-posh.exe...\n' "$recommended_font_face"
      if ! oh-my-posh.exe font install "$recommended_font_slug"; then
        printf '%s\n' 'Warning: host Nerd Font installation failed. Check Windows permissions and retry manually.' >&2
        return
      fi
    else
      printf '%s\n' 'Warning: oh-my-posh.exe was not found from WSL, so the host Nerd Font could not be installed automatically.' >&2
      return
    fi
    target_font_face="$recommended_font_face"
  else
    target_font_face="$(python3 -c 'import json,sys; print((json.load(sys.stdin).get("installed_faces") or [""])[0])' <<<"$inspect_json")"
  fi

  local apply_args=("$windows_terminal_helper" "apply" "--settings" "$settings_file" "--font-face" "$target_font_face")
  if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    apply_args+=("--distro" "$WSL_DISTRO_NAME")
  fi

  local apply_json
  apply_json="$(python3 "${apply_args[@]}")"
  local backup_path
  backup_path="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("backup_path",""))' <<<"$apply_json")"
  printf 'Updated Windows Terminal font settings to %s (backup: %s).\n' "$target_font_face" "$backup_path"
}

show_linux_host_font_note() {
  if is_wsl; then
    return
  fi

  if [[ -n "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ]]; then
    printf '%s\n' 'Linux/SSH note: icon rendering depends on the client terminal font. This server installer cannot change your local Windows Terminal or terminal emulator settings.'
    return
  fi

  printf '%s\n' 'Linux note: icon rendering depends on the terminal font on this machine. If icons look broken, configure your local terminal to use a Nerd Font.'
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
ensure_oh_my_posh >/dev/null || true
show_oh_my_posh_status
show_linux_host_font_note
show_wsl_host_font_status
printf 'Run /restart in Copilot CLI if it is already open.\n'
