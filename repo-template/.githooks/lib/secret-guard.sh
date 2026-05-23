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
gitleaks_mode=""

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

detect_mode_supported() {
  "$gitleaks_bin" detect --help >/dev/null 2>&1
}

legacy_mode_supported() {
  "$gitleaks_bin" dir --help >/dev/null 2>&1 && "$gitleaks_bin" git --help >/dev/null 2>&1
}

resolve_gitleaks_mode() {
  if [ -n "$gitleaks_mode" ]; then
    printf '%s\n' "$gitleaks_mode"
    return 0
  fi

  if detect_mode_supported; then
    gitleaks_mode="detect"
  elif legacy_mode_supported; then
    gitleaks_mode="legacy"
  else
    return 2
  fi

  printf '%s\n' "$gitleaks_mode"
}

run_gitleaks_dir() {
  snapshot_dir="$1"
  scan_output="$2"
  current_mode=$(resolve_gitleaks_mode) || return 2

  if [ "$current_mode" = "detect" ]; then
    if [ "$has_config" -eq 1 ]; then
      "$gitleaks_bin" detect --source "$snapshot_dir" --no-git --config "$config_path" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
      return $?
    fi

    "$gitleaks_bin" detect --source "$snapshot_dir" --no-git --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
    return $?
  fi

  if [ "$has_config" -eq 1 ]; then
    "$gitleaks_bin" dir "$snapshot_dir" --config "$config_path" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
    return $?
  fi

  "$gitleaks_bin" dir "$snapshot_dir" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
}

run_gitleaks_git_range() {
  log_opts="$1"
  scan_output="$2"
  current_mode=$(resolve_gitleaks_mode) || return 2

  if [ "$current_mode" = "detect" ]; then
    if [ "$has_config" -eq 1 ]; then
      "$gitleaks_bin" detect --source "$repo_root" --log-opts "$log_opts" --config "$config_path" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
      return $?
    fi

    "$gitleaks_bin" detect --source "$repo_root" --log-opts "$log_opts" --no-banner --redact=100 --exit-code 1 > "$scan_output" 2>&1
    return $?
  fi

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

  if run_gitleaks_dir "$snapshot_dir" "$scan_output"; then
    :
  else
    scan_status=$?
    if [ "$scan_status" -eq 1 ]; then
      printf '%s\n' "Potential secrets were detected in staged changes. Update the staged content or adjust .gitleaks.toml allowlist only for approved placeholders." >&2
    else
      printf '%s\n' "Failed to run gitleaks for the staged secret scan." >&2
    fi
    if [ -s "$scan_output" ]; then
      cat "$scan_output" >&2
    fi
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

  if run_gitleaks_git_range "$range" "$scan_output"; then
    :
  else
    scan_status=$?
    if [ "$scan_status" -eq 1 ]; then
      printf '%s\n' "Potential secrets were detected in commits being pushed. Remove the secret from history or adjust .gitleaks.toml allowlist only for approved placeholders." >&2
    else
      printf '%s\n' "Failed to run gitleaks for the pre-push secret scan." >&2
    fi
    if [ -s "$scan_output" ]; then
      cat "$scan_output" >&2
    fi
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
