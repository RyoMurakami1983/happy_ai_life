#!/usr/bin/env sh

set -eu

mode="${1:---staged}"
range="${2:-}"

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$repo_root" ]; then
  printf '%s\n' "Failed to resolve the repository root for secret detection." >&2
  exit 1
fi

gitleaks_bin="${GITLEAKS_BIN:-gitleaks}"
if [ -x "$gitleaks_bin" ]; then
  :
elif resolved_gitleaks_bin=$(command -v "$gitleaks_bin" 2>/dev/null); then
  gitleaks_bin="$resolved_gitleaks_bin"
else
  printf '%s\n' "gitleaks is required for the Git secret scan, but it was not found." >&2
  printf '%s\n' "Install gitleaks and retry, or set GITLEAKS_BIN to the executable path." >&2
  exit 1
fi

config_path="$repo_root/.gitleaks.toml"
has_config=0
[ -f "$config_path" ] && has_config=1

git_dir=$(git rev-parse --git-dir 2>/dev/null || true)
if [ -z "$git_dir" ]; then
  printf '%s\n' "Failed to resolve the repository .git directory for secret detection." >&2
  exit 1
fi
case "$git_dir" in
  /*) ;;
  *) git_dir="$repo_root/$git_dir" ;;
esac

scratch_parent="$git_dir/happy-secret-scan"
mkdir -p "$scratch_parent"

run_gitleaks_dir() {
  snapshot_dir="$1"
  scan_output="$2"

  if [ "$has_config" -eq 1 ]; then
    "$gitleaks_bin" dir "$snapshot_dir" --config "$config_path" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
    return $?
  fi

  "$gitleaks_bin" dir "$snapshot_dir" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
}

run_gitleaks_git_range() {
  log_opts="$1"
  scan_output="$2"

  if [ "$has_config" -eq 1 ]; then
    "$gitleaks_bin" git "$repo_root" --log-opts "$log_opts" --config "$config_path" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
    return $?
  fi

  "$gitleaks_bin" git "$repo_root" --log-opts "$log_opts" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
}

scan_staged() {
  scratch_dir=$(mktemp -d "$scratch_parent/pre-commit.XXXXXX")
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

  if ! run_gitleaks_dir "$snapshot_dir" "$scan_output"; then
    printf '%s\n' "Potential secrets were detected in staged changes. Update the staged content or adjust .gitleaks.toml allowlist only for approved placeholders." >&2
    cat "$scan_output" >&2
    exit 1
  fi
}

scan_range() {
  if [ -z "$range" ]; then
    printf '%s\n' "Missing commit range for pre-push secret scan." >&2
    exit 1
  fi

  scratch_dir=$(mktemp -d "$scratch_parent/pre-push.XXXXXX")
  scan_output="$scratch_dir/gitleaks-output.txt"

  cleanup() {
    rm -rf "$scratch_dir"
  }
  trap cleanup EXIT HUP INT TERM

  if ! run_gitleaks_git_range "$range" "$scan_output"; then
    printf '%s\n' "Potential secrets were detected in commits being pushed. Remove the secret from history or adjust .gitleaks.toml allowlist only for approved placeholders." >&2
    cat "$scan_output" >&2
    exit 1
  fi
}

case "$mode" in
  --staged)
    scan_staged
    ;;
  --range)
    scan_range
    ;;
  *)
    printf '%s\n' "Unsupported secret guard mode: $mode" >&2
    exit 2
    ;;
esac

exit 0
