#!/usr/bin/env sh

set -eu

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$repo_root" ]; then
  printf '%s\n' "Failed to resolve the repository root for secret detection." >&2
  exit 1
fi

config_path="$repo_root/.gitleaks.toml"
require_config="${SECRET_GUARD_REQUIRE_CONFIG:-0}"
if [ ! -f "$config_path" ]; then
  if [ "$require_config" = "1" ] || [ "$require_config" = "true" ] || [ "$require_config" = "yes" ]; then
    printf '%s\n%s\n%s\n' \
      "Missing .gitleaks.toml in the repository root." \
      "Secret detection is configured to require a gitleaks policy before committing." \
      "Add .gitleaks.toml to the repository root, or unset SECRET_GUARD_REQUIRE_CONFIG to skip scanning until the repository opts in." >&2
    exit 1
  fi
  printf '%s\n%s\n%s\n' \
    "Skipping pre-commit secret scan because .gitleaks.toml was not found in the repository root." \
    "To enable gitleaks scanning, add .gitleaks.toml to the repository root." \
    "To make missing configuration a hard failure, set SECRET_GUARD_REQUIRE_CONFIG=1." >&2
  exit 0
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
git -c core.quotepath=false diff --cached --name-only -z --diff-filter=ACMR -- > "$staged_paths"

if [ ! -s "$staged_paths" ]; then
  exit 0
fi

if ! git checkout-index --prefix="$snapshot_dir/" --stdin -z < "$staged_paths"; then
  printf '%s\n' "Failed to read staged content for secret scanning." >&2
  exit 1
fi

if ! "$gitleaks_bin" dir "$snapshot_dir" --config "$config_path" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1; then
  printf '%s\n' "Potential secrets were detected in staged changes. Update the staged content or adjust .gitleaks.toml allowlist only for approved placeholders." >&2
  cat "$scan_output" >&2
  exit 1
fi

exit 0
