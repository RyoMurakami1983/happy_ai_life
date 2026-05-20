#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_root="$(CDPATH= cd -- "${script_dir}/.." && pwd)"

cd "${source_root}"
exec uv run python -m scripts.sync_to_home_cli "$@"
