#!/usr/bin/env sh

set -eu

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$repo_root" ]; then
  printf '%s\n' "Failed to resolve the repository root for secret detection." >&2
  exit 1
fi

config_path="$repo_root/.gitleaks.toml"
if [ ! -f "$config_path" ]; then
  printf '%s\n%s\n' "Missing .gitleaks.toml in the repository root." "Secret detection policy must be configured before committing." >&2
  exit 1
fi

gitleaks_bin="${GITLEAKS_BIN:-gitleaks}"
if [ -x "$gitleaks_bin" ]; then
  :
elif resolved_gitleaks_bin=$(command -v "$gitleaks_bin" 2>/dev/null); then
  gitleaks_bin="$resolved_gitleaks_bin"
else
  printf '%s\n' "gitleaks is required for the pre-commit secret scan, but it was not found." >&2
  printf '%s\n' "Install gitleaks and retry, or set GITLEAKS_BIN to the executable path." >&2
  exit 1
fi

scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/gitleaks-pre-commit.XXXXXX")
snapshot_dir="$scratch_dir/snapshot"
staged_paths="$scratch_dir/staged-paths.txt"
scan_output="$scratch_dir/gitleaks-output.txt"

cleanup() {
  rm -rf "$scratch_dir"
}

trap cleanup EXIT HUP INT TERM

mkdir -p "$snapshot_dir"
git diff --cached --name-only --diff-filter=ACMR -- > "$staged_paths"

if [ ! -s "$staged_paths" ]; then
  exit 0
fi

while IFS= read -r relative_path; do
  [ -n "$relative_path" ] || continue

  destination_path="$snapshot_dir/$relative_path"
  destination_dir=$(dirname -- "$destination_path")
  mkdir -p "$destination_dir"

  if ! git show ":$relative_path" > "$destination_path"; then
    printf '%s\n%s\n' "Failed to read staged content for secret scanning." "$relative_path" >&2
    exit 1
  fi
done < "$staged_paths"

if ! "$gitleaks_bin" dir "$snapshot_dir" --config "$config_path" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1; then
  printf '%s\n' "Potential secrets were detected in staged changes. Update the staged content or adjust .gitleaks.toml allowlist only for approved placeholders." >&2
  cat "$scan_output" >&2
  exit 1
fi

exit 0
