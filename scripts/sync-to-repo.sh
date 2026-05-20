#!/usr/bin/env bash
set -euo pipefail

write_section() {
  printf '\n=== %s ===\n' "$1"
}

warn_if_path_exists() {
  local path="$1"
  local message="$2"
  if [[ -e "${path}" ]]; then
    printf 'WARNING: %s\n' "${message}" >&2
  fi
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

resolve_policy_profile() {
  case "$1" in
    Default) printf 'HappyDefault\n' ;;
    Enterprise) printf 'EnterpriseStrict\n' ;;
    *) printf '%s\n' "$1" ;;
  esac
}

resolve_hooks_source_path() {
  local source_root="$1"
  local hooks_relative_path="$2"
  local primary_path="${source_root}/${hooks_relative_path}"
  if [[ -d "${primary_path}" ]]; then
    full_path "${primary_path}"
    return
  fi

  local fallback_path="${source_root}/hooks"
  if [[ "${hooks_relative_path}" == ".github/hooks" && -d "${fallback_path}" ]]; then
    full_path "${fallback_path}"
    return
  fi

  full_path "${primary_path}"
}

merge_append_only_file() {
  local source="$1"
  local destination="$2"
  local dry_run="$3"

  if [[ ! -f "${source}" ]]; then
    printf 'Source file not found: %s\n' "${source}" >&2
    exit 1
  fi

  if [[ "${dry_run}" -eq 1 ]]; then
    if [[ ! -f "${destination}" ]]; then
      printf 'Would create %s from %s\n' "${destination}" "${source}"
      return
    fi

    local missing_count=0
    while IFS= read -r line || [[ -n "${line}" ]]; do
      [[ -z "${line//[[:space:]]/}" ]] && continue
      if ! grep -Fqx -- "${line}" "${destination}"; then
        missing_count=$((missing_count + 1))
      fi
    done <"${source}"

    if [[ "${missing_count}" -eq 0 ]]; then
      printf 'No append-only changes needed for %s\n' "${destination}"
    else
      printf 'Would merge %s missing line(s) into %s\n' "${missing_count}" "${destination}"
    fi
    return
  fi

  mkdir -p "$(dirname "${destination}")"
  if [[ ! -f "${destination}" ]]; then
    cp "${source}" "${destination}"
    return
  fi

  local to_append=()
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line//[[:space:]]/}" ]] && continue
    if ! grep -Fqx -- "${line}" "${destination}"; then
      to_append+=("${line}")
    fi
  done <"${source}"

  if ((${#to_append[@]} == 0)); then
    return
  fi

  if [[ -s "${destination}" ]] && [[ "$(tail -c 1 "${destination}" 2>/dev/null || true)" != "" ]]; then
    printf '\n' >>"${destination}"
  fi
  printf '%s\n' "${to_append[@]}" >>"${destination}"
}

remove_sealed_session_continuity_artifacts() {
  local target_repo_root="$1"
  local dry_run="$2"
  local path
  for path in \
    "${target_repo_root}/.github/hooks/session-continuity.json" \
    "${target_repo_root}/.github/instructions/session-context.instructions.md"; do
    [[ -f "${path}" ]] || continue
    if [[ "${dry_run}" -eq 1 ]]; then
      printf 'Would remove sealed session continuity artifact: %s\n' "${path}"
    else
      rm -f "${path}"
      printf 'Removed sealed session continuity artifact: %s\n' "${path}"
    fi
  done
}

remove_excluded_policy_profile_artifacts() {
  local target_repo_root="$1"
  local policy_profile="$2"
  local dry_run="$3"
  [[ "${policy_profile}" == "EnterpriseStrict" ]] && return

  local path="${target_repo_root}/.github/instructions/enterprise.instructions.md"
  if [[ ! -f "${path}" ]]; then
    return 0
  fi
  if [[ "${dry_run}" -eq 1 ]]; then
    printf 'Would remove excluded policy profile artifact: %s\n' "${path}"
  else
    rm -f "${path}"
    printf 'Removed excluded policy profile artifact: %s\n' "${path}"
  fi
}

sync_directory() {
  local source="$1"
  local destination="$2"
  local mirror_mode="$3"
  local dry_run="$4"
  local verbose_log="$5"
  shift 5
  local -a extra_args=("$@")

  if [[ ! -d "${source}" ]]; then
    printf 'Source path not found: %s\n' "${source}" >&2
    exit 1
  fi

  mkdir -p "${destination}"

  local -a rsync_args=(-a --itemize-changes)
  if [[ "${mirror_mode}" -eq 1 ]]; then
    rsync_args+=(--delete)
  fi
  if [[ "${dry_run}" -eq 1 ]]; then
    rsync_args+=(-n)
  fi
  rsync_args+=("${extra_args[@]}")
  rsync_args+=("${source}/" "${destination}/")

  if [[ "${verbose_log}" -eq 1 ]]; then
    printf 'rsync'
    printf ' %q' "${rsync_args[@]}"
    printf '\n'
  fi

  rsync "${rsync_args[@]}"
}

target_repo_path=""
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_root="$(CDPATH= cd -- "${script_dir}/.." && pwd)"
template_relative_path="repo-template/.github"
docs_furikaeri_relative_path="repo-template/docs/furikaeri"
hooks_relative_path=".github/hooks"
hooks_mode="SafetyOnly"
policy_profile="HappyDefault"
git_hooks_relative_path="repo-template/.githooks"
policy_relative_path="policy"
mirror=0
dry_run=0
verbose_log=0

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
    -DocsFurikaeriRelativePath|-DocsSessionsRelativePath)
      docs_furikaeri_relative_path="$2"
      shift 2
      ;;
    -HooksRelativePath)
      hooks_relative_path="$2"
      shift 2
      ;;
    -HooksMode)
      hooks_mode="$2"
      shift 2
      ;;
    -PolicyProfile)
      policy_profile="$2"
      shift 2
      ;;
    -GitHooksRelativePath)
      git_hooks_relative_path="$2"
      shift 2
      ;;
    -PolicyRelativePath)
      policy_relative_path="$2"
      shift 2
      ;;
    -Mirror)
      mirror=1
      shift
      ;;
    -DryRun)
      dry_run=1
      shift
      ;;
    -VerboseLog)
      verbose_log=1
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "${target_repo_path}" ]]; then
  printf 'Target repository path is required.\n' >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  printf 'rsync is required for sync-to-repo.sh on Linux/WSL2.\n' >&2
  exit 1
fi

target_repo_path="$(full_path "${target_repo_path}")"
source_root="$(full_path "${source_root}")"
source_path="$(full_path "${source_root}/${template_relative_path}")"
effective_policy_profile="$(resolve_policy_profile "${policy_profile}")"

if [[ ! -d "${target_repo_path}" ]]; then
  printf 'Target repository path not found: %s\n' "${target_repo_path}" >&2
  exit 1
fi

if [[ ! -d "${source_path}" ]]; then
  printf 'Template source path not found: %s\n' "${source_path}" >&2
  exit 1
fi

policy_source_path=""
if [[ -n "${policy_relative_path}" ]]; then
  policy_source_path="$(full_path "${source_root}/${policy_relative_path}")"
  if [[ ! -d "${policy_source_path}" ]]; then
    printf 'Guard policy source path not found: %s. Pass -PolicyRelativePath '"'"''"'"' only when intentionally skipping policy sync.\n' "${policy_source_path}" >&2
    exit 1
  fi
  for required_policy_file in guard-policy.json guard-policy.schema.json; do
    if [[ ! -f "${policy_source_path}/${required_policy_file}" ]]; then
      printf 'Guard policy source file not found: %s. Pass -PolicyRelativePath '"'"''"'"' only when intentionally skipping policy sync.\n' "${policy_source_path}/${required_policy_file}" >&2
      exit 1
    fi
  done
fi

if [[ "${hooks_mode}" != "SafetyOnly" && "${hooks_mode}" != "All" && "${hooks_mode}" != "None" ]]; then
  printf 'Unsupported HooksMode: %s\n' "${hooks_mode}" >&2
  exit 1
fi

duplicate_hooks_path="${source_path}/hooks"
warn_if_path_exists "${duplicate_hooks_path}" "repo-template/.github/hooks is ignored. Use .github/hooks as the single source of truth for repository hooks."

exclude_args=(--exclude='.git/' --exclude='.vs/' --exclude='hooks/' --exclude='*.local.json' --exclude='*.local.ps1' --exclude='.gitignore')
if [[ "${effective_policy_profile}" != "EnterpriseStrict" ]]; then
  exclude_args+=(--exclude='enterprise.instructions.md')
fi

write_section "Sync repo-template to target repository (.github)"
destination_path="${target_repo_path}/.github"
printf 'Source      : %s\n' "${source_path}"
printf 'Destination : %s\n' "${destination_path}"
printf 'Mirror      : %s\n' "${mirror}"
printf 'DryRun      : %s\n' "${dry_run}"
printf 'HooksMode   : %s\n' "${hooks_mode}"
printf 'PolicyProfile : %s\n' "${effective_policy_profile}"
if [[ "${policy_profile}" != "${effective_policy_profile}" ]]; then
  printf 'ProfileAlias : %s -> %s\n' "${policy_profile}" "${effective_policy_profile}"
fi

case "${effective_policy_profile}" in
  EnterpriseStrict)
    printf 'Note        : EnterpriseStrict は enterprise.instructions.md を含む重い governance guidance を opt-in で同期します。\n'
    ;;
  Secure)
    printf 'Note        : Secure は安全弁を維持しつつ、enterprise 固有 instructions は同期しません。\n'
    ;;
  WindowsDesktop)
    printf 'Note        : WindowsDesktop は Windows desktop / Tauri / proxy 前提の profile ですが、EnterpriseStrict governance は同期しません。\n'
    ;;
  *)
    printf 'Note        : HappyDefault では enterprise 固有 instructions を同期しません。\n'
    ;;
esac

sync_directory "${source_path}" "${destination_path}" "${mirror}" "${dry_run}" "${verbose_log}" "${exclude_args[@]}"
merge_append_only_file "${source_path}/.gitignore" "${destination_path}/.gitignore" "${dry_run}"
remove_excluded_policy_profile_artifacts "${target_repo_path}" "${effective_policy_profile}" "${dry_run}"

should_sync_hooks=0
if [[ -n "${hooks_relative_path}" && "${hooks_mode}" != "None" ]]; then
  should_sync_hooks=1
fi

if [[ "${should_sync_hooks}" -eq 1 ]]; then
  write_section "Sync hooks to target repository (.github/hooks)"
  hooks_source_path="$(resolve_hooks_source_path "${source_root}" "${hooks_relative_path}")"
  hooks_destination_path="${target_repo_path}/.github/hooks"
  hooks_exclude_args=(--exclude='*.local.json' --exclude='*.local.ps1')
  if [[ "${hooks_mode}" == "SafetyOnly" ]]; then
    hooks_exclude_args+=(--exclude='session-continuity.json')
  fi

  printf 'Source      : %s\n' "${hooks_source_path}"
  printf 'Destination : %s\n' "${hooks_destination_path}"
  printf 'HooksMode   : %s\n' "${hooks_mode}"
  if [[ "${hooks_mode}" == "SafetyOnly" ]]; then
    printf 'Note        : sessionStart/sessionEnd continuity hooks are sealed and excluded by default.\n'
  fi

  sync_directory "${hooks_source_path}" "${hooks_destination_path}" "${mirror}" "${dry_run}" "${verbose_log}" "${hooks_exclude_args[@]}"
fi

if [[ "${should_sync_hooks}" -eq 1 && "${hooks_mode}" == "SafetyOnly" ]]; then
  remove_sealed_session_continuity_artifacts "${target_repo_path}" "${dry_run}"
fi

if [[ -n "${git_hooks_relative_path}" ]]; then
  write_section "Sync git hooks to target repository (.githooks)"
  git_hooks_source_path="$(full_path "${source_root}/${git_hooks_relative_path}")"
  git_hooks_destination_path="${target_repo_path}/.githooks"
  printf 'Source      : %s\n' "${git_hooks_source_path}"
  printf 'Destination : %s\n' "${git_hooks_destination_path}"
  sync_directory "${git_hooks_source_path}" "${git_hooks_destination_path}" "${mirror}" "${dry_run}" "${verbose_log}"
fi

if [[ -n "${policy_relative_path}" ]]; then
  write_section "Sync guard policy to target repository (policy)"
  policy_destination_path="${target_repo_path}/policy"
  printf 'Source      : %s\n' "${policy_source_path}"
  printf 'Destination : %s\n' "${policy_destination_path}"
  sync_directory "${policy_source_path}" "${policy_destination_path}" "${mirror}" "${dry_run}" "${verbose_log}"
fi

if [[ -n "${docs_furikaeri_relative_path}" ]]; then
  docs_furikaeri_source_path="${source_root}/${docs_furikaeri_relative_path}"
  if [[ -d "${docs_furikaeri_source_path}" ]]; then
    write_section "Sync furikaeri docs scaffold to target repository (docs/furikaeri)"
    docs_furikaeri_destination_path="${target_repo_path}/docs/furikaeri"
    printf 'Source      : %s\n' "$(full_path "${docs_furikaeri_source_path}")"
    printf 'Destination : %s\n' "${docs_furikaeri_destination_path}"
    if [[ "${mirror}" -eq 1 ]]; then
      printf 'WARNING: docs/furikaeri sync is always non-mirror (append-only). -Mirror switch is ignored for this step.\n' >&2
    fi
    sync_directory "$(full_path "${docs_furikaeri_source_path}")" "${docs_furikaeri_destination_path}" 0 "${dry_run}" "${verbose_log}"
  fi
fi
