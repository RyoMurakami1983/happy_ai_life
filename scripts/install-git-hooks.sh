#!/usr/bin/env bash
set -euo pipefail

write_section() {
  printf '\n=== %s ===\n' "$1"
}

full_path() {
  local target="$1"
  if [[ -d "${target}" ]]; then
    (cd "${target}" && pwd -P)
    return
  fi

  local parent
  parent="$(dirname "${target}")"
  local name
  name="$(basename "${target}")"
  (cd "${parent}" && printf '%s/%s\n' "$(pwd -P)" "${name}")
}

same_path() {
  [[ "$(full_path "$1")" == "$(full_path "$2")" ]]
}

ensure_git_repository() {
  local path="$1"
  if ! git -C "${path}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf 'Not a git repository: %s\n' "${path}" >&2
    exit 1
  fi
}

sync_hooks_dir() {
  local source="$1"
  local destination="$2"
  mkdir -p "${destination}"
  rsync -a --delete "${source}/" "${destination}/"
}

target_repo_path=""
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_root="$(CDPATH= cd -- "${script_dir}/.." && pwd)"
template_relative_path="repo-template/.githooks"
installed_hooks_path=".githooks"

while (($# > 0)); do
  case "$1" in
    -TargetRepoPath)
      target_repo_path="$2"
      shift 2
      ;;
    -SourceRoot)
      source_root="$2"
      shift 2
      ;;
    -TemplateRelativePath)
      template_relative_path="$2"
      shift 2
      ;;
    -InstalledHooksPath)
      installed_hooks_path="$2"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "${target_repo_path}" ]]; then
  target_repo_path="${source_root}"
fi

target_repo_path="$(full_path "${target_repo_path}")"
source_root="$(full_path "${source_root}")"
template_path="$(full_path "${source_root}/${template_relative_path}")"

if [[ ! -d "${target_repo_path}" ]]; then
  printf 'Target repository path not found: %s\n' "${target_repo_path}" >&2
  exit 1
fi

if [[ ! -d "${template_path}" ]]; then
  printf 'Git hook template path not found: %s\n' "${template_path}" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  printf 'rsync is required for install-git-hooks.sh on Linux/WSL2.\n' >&2
  exit 1
fi

ensure_git_repository "${target_repo_path}"

write_section "Install git hooks"
printf 'Target : %s\n' "${target_repo_path}"
printf 'Source : %s\n' "${template_path}"

if same_path "${target_repo_path}" "${source_root}"; then
  git -C "${target_repo_path}" config --local core.hooksPath "${template_relative_path}"
  printf 'Configured core.hooksPath to %s\n' "${template_relative_path}"
  exit 0
fi

destination_path="${target_repo_path}/${installed_hooks_path}"
sync_hooks_dir "${template_path}" "${destination_path}"
git -C "${target_repo_path}" config --local core.hooksPath "${installed_hooks_path}"
printf 'Installed hooks to %s and configured core.hooksPath=%s\n' "${destination_path}" "${installed_hooks_path}"
