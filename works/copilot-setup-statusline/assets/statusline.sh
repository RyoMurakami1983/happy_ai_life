#!/usr/bin/env bash
set -u

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
theme="$script_dir/statusline.omp.json"
payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT

cat > "$payload_file"

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s' 'Copilot status unavailable'
  exit 0
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  printf '%s' 'Copilot status unavailable'
  exit 0
fi

python3 - "$theme" "$payload_file" <<'PY'
from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Optional


def format_token_count(value: object) -> str:
    if value is None:
        return "?"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "?"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}m"
    if number >= 1_000:
        return f"{number / 1_000:.1f}k"
    return str(int(number))


def format_duration(milliseconds: object) -> str:
    try:
        total_seconds = int(float(milliseconds) / 1000)
    except (TypeError, ValueError):
        total_seconds = 0
    if total_seconds <= 0:
        return "00:00:00"
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def new_gauge(percent: object) -> str:
    try:
        bounded = max(0, min(100, round(float(percent))))
    except (TypeError, ValueError):
        return ".........."
    filled = int(bounded // 10)
    return ("#" * filled) + ("." * (10 - filled))


def find_project_marker(
    start_path: str,
    names: tuple[str, ...] = (),
    patterns: tuple[str, ...] = (),
    max_depth: int = 6,
) -> bool:
    current = Path(start_path).expanduser()
    if not current.exists():
        return False
    if not current.is_dir():
        current = current.parent

    for _ in range(max_depth + 1):
        for name in names:
            if (current / name).exists():
                return True
        if patterns:
            try:
                for child in current.iterdir():
                    if child.is_file() and any(fnmatch.fnmatch(child.name, pattern) for pattern in patterns):
                        return True
            except OSError:
                pass
        if current.parent == current:
            break
        current = current.parent
    return False


def should_skip_tool_versions() -> bool:
    return os.environ.get("COPILOT_STATUS_SKIP_TOOL_VERSIONS", "").lower() in {"1", "true", "yes", "on"}


def invoke_version_command(command: str, *arguments: str) -> Optional[str]:
    if shutil.which(command) is None:
        return None
    try:
        result = subprocess.run(
            [command, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    first_line = result.stdout.splitlines()[0].strip() if result.stdout.splitlines() else ""
    return first_line or None


def get_tooling_status(path: str) -> str:
    items: list[str] = []
    skip_versions = should_skip_tool_versions()

    if find_project_marker(
        path,
        names=("global.json", "Directory.Build.props"),
        patterns=("*.csproj", "*.fsproj", "*.sln"),
    ):
        version = None if skip_versions else invoke_version_command("dotnet", "--version")
        items.append(f".NET {version}" if version else ".NET")

    if find_project_marker(
        path,
        names=("tsconfig.json", "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"),
    ):
        version = None if skip_versions else invoke_version_command("node", "--version")
        if version:
            version = version.removeprefix("v")
        items.append(f"TS/Node {version}" if version else "TS/Node")

    if find_project_marker(
        path,
        names=("pyproject.toml", "requirements.txt", "uv.lock", ".python-version", "Pipfile"),
    ):
        uv_version = None if skip_versions else invoke_version_command("uv", "--version")
        if uv_version:
            parts = uv_version.removeprefix("uv ").split()
            items.append(f"Python/uv {parts[0]}")
        else:
            version = None
            if not skip_versions:
                version = invoke_version_command("python3", "--version") or invoke_version_command("python", "--version")
            if version:
                items.append(f"Python {version.removeprefix('Python ')}")
            else:
                items.append("Python")

    if find_project_marker(path, names=("Cargo.toml", "Cargo.lock")):
        version = None if skip_versions else invoke_version_command("rustc", "--version")
        if version:
            parts = version.removeprefix("rustc ").split()
            items.append(f"Rust {parts[0]}")
        else:
            items.append("Rust")

    return " ".join(items)


def fallback(env: dict[str, str]) -> str:
    tooling = f"{env['COPILOT_STATUS_TOOLING']} " if env.get("COPILOT_STATUS_TOOLING") else ""
    changes = f" {env['COPILOT_STATUS_CHANGES']}" if env.get("COPILOT_STATUS_CHANGES") else ""
    return (
        f"{tooling}ctx {env['COPILOT_STATUS_CONTEXT']} "
        f"{env['COPILOT_STATUS_GAUGE']} time {env['COPILOT_STATUS_DURATION']}{changes}"
    )


theme = sys.argv[1]
payload_file = sys.argv[2]

try:
    payload = json.loads(Path(payload_file).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    print("Copilot status unavailable", end="")
    raise SystemExit(0)

context = payload.get("context_window") or {}
cost = payload.get("cost") or {}
current_tokens = context.get("current_context_tokens")
context_limit = context.get("displayed_context_limit")
context_percent = context.get("current_context_used_percentage", context.get("used_percentage"))
lines_added = int(cost.get("total_lines_added") or 0)
lines_removed = int(cost.get("total_lines_removed") or 0)
cwd = str(payload.get("cwd") or os.getcwd())

env = os.environ.copy()
env["COPILOT_STATUS_CONTEXT"] = f"{format_token_count(current_tokens)}/{format_token_count(context_limit)}"
env["COPILOT_STATUS_GAUGE"] = new_gauge(context_percent)
env["COPILOT_STATUS_DURATION"] = format_duration(cost.get("total_duration_ms"))
env["COPILOT_STATUS_CHANGES"] = f"+{lines_added}/-{lines_removed}" if lines_added or lines_removed else ""
env["COPILOT_STATUS_TOOLING"] = get_tooling_status(cwd)

if shutil.which("oh-my-posh") and Path(theme).exists():
    try:
        result = subprocess.run(
            [
                "oh-my-posh",
                "print",
                "primary",
                "--config",
                theme,
                "--pwd",
                cwd,
                "--force",
                "--escape=false",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
            env=env,
        )
        output = result.stdout.rstrip()
        if output:
            print(output, end="")
            raise SystemExit(0)
    except (OSError, subprocess.SubprocessError):
        pass

print(fallback(env), end="")
PY
