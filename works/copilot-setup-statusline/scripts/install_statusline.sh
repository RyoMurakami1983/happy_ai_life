#!/usr/bin/env bash
set -euo pipefail

copilot_dir="${1:-"$HOME/.copilot"}"
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
skill_dir="$(CDPATH= cd -- "$script_dir/.." && pwd)"
assets_dir="$skill_dir/assets"
settings_path="$copilot_dir/settings.json"

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
    status_line = {}
    settings["statusLine"] = status_line

status_line["type"] = "command"
status_line["command"] = command_path
status_line["padding"] = 1

feature_flags = settings.setdefault("feature_flags", {})
if not isinstance(feature_flags, dict):
    feature_flags = {}
    settings["feature_flags"] = feature_flags

enabled = feature_flags.setdefault("enabled", [])
if not isinstance(enabled, list):
    enabled = []
    feature_flags["enabled"] = enabled

if "STATUS_LINE" not in enabled:
    enabled.append("STATUS_LINE")

settings["experimental"] = True
settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

printf 'Installed Copilot statusline to %s\n' "$copilot_dir"
printf 'Run /restart in Copilot CLI if it is already open.\n'
