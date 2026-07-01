#!/usr/bin/env bash
set -euo pipefail

write_section() {
  printf '\n=== %s ===\n' "$1"
}

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/ }"
  value="${value//$'\r'/ }"
  value="${value//$'\t'/ }"
  printf '%s' "${value}"
}

json_string() {
  printf '"%s"' "$(json_escape "$1")"
}

json_bool() {
  if [[ "$1" -eq 1 ]]; then
    printf 'true'
  else
    printf 'false'
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

same_path() {
  [[ "$(full_path "$1")" == "$(full_path "$2")" ]]
}

test_git_repository() {
  git -C "$1" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

test_directory_has_entries() {
  [[ -d "$1" ]] && find "$1" -mindepth 1 -maxdepth 1 | read -r _
}

get_required_git_hook_issues() {
  local path="$1"
  local -a issues=()
  local required
  for required in pre-commit pre-push lib/secret-guard.sh lib/commit-safety-guard.sh; do
    [[ -f "${path}/${required}" ]] || issues+=("${required}")
  done

  if [[ -f "${path}/pre-commit" ]]; then
    if ! grep -q 'commit-safety-guard\.sh' "${path}/pre-commit"; then
      issues+=("pre-commit does not call commit-safety-guard.sh")
    fi
    if ! grep -q 'secret-guard\.sh' "${path}/pre-commit"; then
      issues+=("pre-commit does not call secret-guard.sh")
    fi
  fi

  if [[ -f "${path}/pre-push" ]]; then
    if ! grep -q 'secret-guard\.sh' "${path}/pre-push" || ! grep -q -- '--range' "${path}/pre-push"; then
      issues+=("pre-push does not call secret-guard.sh --range")
    fi
  fi

  printf '%s\n' "${issues[@]}"
}

get_git_hook_line_ending_issues() {
  local hooks_path="$1"
  local hooks_label="$2"
  local repo_hook_scripts_path="$3"
  local repo_hook_scripts_label="$4"
  local gitattributes_path="$5"
  local gitattributes_label="$6"
  local -a required_rules=(".githooks/**" ".github/hooks/scripts/*.sh")
  local -a issues=()

  effective_eol_for_rule() {
    local path_rule="$1"
    local effective=""
    while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
      local line="${raw_line#"${raw_line%%[![:space:]]*}"}"
      [[ -n "${line}" ]] || continue
      [[ "${line}" == \#* ]] && continue

      read -r -a parts <<<"${line}"
      [[ "${#parts[@]}" -ge 2 ]] || continue

      local pattern="${parts[0]}"
      if [[ "${pattern}" != "*" && "${pattern}" != "${path_rule}" ]]; then
        continue
      fi

      local token
      for token in "${parts[@]:1}"; do
        if [[ "${token}" == eol=* ]]; then
          effective="${token#eol=}"
        fi
      done
    done <"${gitattributes_path}"
    printf '%s\n' "${effective}"
  }

  if [[ ! -f "${gitattributes_path}" ]]; then
    issues+=("${gitattributes_label} is missing.")
  else
    local required_rule
    for required_rule in "${required_rules[@]}"; do
      local effective_eol
      effective_eol="$(effective_eol_for_rule "${required_rule}")"
      if [[ "${effective_eol}" != "lf" ]]; then
        issues+=("${gitattributes_label} does not resolve '${required_rule}' to eol=lf.")
      fi
    done
  fi

  collect_crlf_issues() {
    local root_path="$1"
    local root_label="$2"
    [[ -d "${root_path}" ]] || return
    local hook_file relative_path
    while IFS= read -r hook_file; do
      [[ -n "${hook_file}" ]] || continue
      if grep -q $'\r' "${hook_file}"; then
        relative_path="${hook_file#${root_path}/}"
        issues+=("CRLF line ending found in ${root_label}/${relative_path}.")
      fi
    done < <(find "${root_path}" -type f \( -name '*.sh' -o -name 'pre-*' -o -name 'post-*' \) -print)
  }

  collect_crlf_issues "${hooks_path}" "${hooks_label}"
  collect_crlf_issues "${repo_hook_scripts_path}" "${repo_hook_scripts_label}"

  printf '%s\n' "${issues[@]}"
}

test_required_copilot_safety_hook() {
  [[ -f "$1/safety-guard.json" ]]
}

has_workflow_files() {
  find "$1" -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) | read -r _
}

list_workflow_names() {
  find "$1" -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) -printf '%f\n' | sort
}

test_dotnet_project() {
  find "$1" \
    \( -path '*/.git' -o -path '*/node_modules' -o -path '*/bin' -o -path '*/obj' \) -prune \
    -o -type f \( -name '*.csproj' -o -name '*.vbproj' -o -name '*.fsproj' -o -name '*.sln' -o -name '*.slnx' \) -print -quit \
    | read -r _
}

test_command_available() {
  local name
  for name in "$@"; do
    [[ -n "${name}" ]] || continue
    if command -v "${name}" >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

available_int() {
  if test_command_available "$@"; then
    printf '1'
  else
    printf '0'
  fi
}

tool_dependency_state_json() {
  local hooks_path="$1"
  local -a required=()
  local -a missing=()
  local -a reasons=()
  local tool_name available reason

  while IFS=$'\t' read -r tool_name available reason; do
    [[ -n "${tool_name}" ]] || continue
    required+=("${tool_name}")
    reasons+=("${tool_name}"$'\t'"${reason}")
    if [[ "${available}" -eq 0 ]]; then
      missing+=("${tool_name}")
    fi
  done < <(collect_tool_dependencies "${hooks_path}")

  printf '{"required":['
  local first=1 value
  for value in "${required[@]}"; do
    [[ "${first}" -eq 1 ]] || printf ','
    json_string "${value}"
    first=0
  done
  printf '],"missing":['
  first=1
  for value in "${missing[@]}"; do
    [[ "${first}" -eq 1 ]] || printf ','
    json_string "${value}"
    first=0
  done
  printf '],"reasons":{'
  first=1
  local entry key
  for entry in "${reasons[@]}"; do
    key="${entry%%$'\t'*}"
    reason="${entry#*$'\t'}"
    [[ "${first}" -eq 1 ]] || printf ','
    json_string "${key}"
    printf ':'
    json_string "${reason}"
    first=0
  done
  printf '}}'
}

collect_tool_dependencies() {
  local hooks_path="$1"
  local safety_guard_path="${hooks_path}/safety-guard.json"
  local session_continuity_path="${hooks_path}/session-continuity.json"
  local -a required=()
  local -a reasons=()
  local -a available_values=()

  add_required_tool() {
    local tool_name="$1"
    local reason="$2"
    local available="$3"
    local index
    for index in "${!required[@]}"; do
      if [[ "${required[$index]}" == "${tool_name}" ]]; then
        if [[ "${available}" -eq 0 ]]; then
          available_values[$index]=0
        fi
        return
      fi
    done
    required+=("${tool_name}")
    reasons+=("${tool_name}"$'\t'"${reason}")
    available_values+=("${available}")
  }

  add_required_tool "git" "repo-secure-check と git hooks の基盤として常に必要です。" "$(available_int git)"
  add_required_tool "gitleaks" "secret scan を実行する safety guard / git hooks に必要です。" "$(available_int gitleaks)"
  add_required_tool "rsync" "Linux/WSL2 の bootstrap script は rsync で template を同期します。" "$(available_int rsync)"

  if [[ -f "${safety_guard_path}" ]] && grep -q '"bash"' "${safety_guard_path}" && grep -q 'guard_pre_tool\.sh' "${safety_guard_path}"; then
    add_required_tool "jq" "現在の host では safety-guard.json の bash variant が有効で、guard_pre_tool.sh が jq を使います。" "$(available_int jq)"
  fi

  if [[ -f "${session_continuity_path}" ]] && grep -q 'session-start\.js\|session-end\.js' "${session_continuity_path}"; then
    add_required_tool "node" "session-continuity.json が有効で、session hook script は node runtime で動きます。" "$(available_int node)"
    if grep -q 'session-start\.js' "${session_continuity_path}"; then
      add_required_tool "gh" "session-start hook は open issue 取得で GitHub CLI を使います。" "$(available_int gh)"
    fi
  fi

  local index
  for index in "${!required[@]}"; do
    printf '%s\t%s\t%s\n' "${required[$index]}" "${available_values[$index]}" "${reasons[$index]#*$'\t'}"
  done
}

tool_dependency_details_text() {
  local hooks_path="$1"
  local -a missing_details=()
  local tool_name available reason

  while IFS=$'\t' read -r tool_name available reason; do
    [[ -n "${tool_name}" ]] || continue
    if [[ "${available}" -eq 0 ]]; then
      missing_details+=("${tool_name}（${reason}）")
    fi
  done < <(collect_tool_dependencies "${hooks_path}")

  if ((${#missing_details[@]} == 0)); then
    printf '必要な依存は現在の host で利用可能です。'
    return
  fi

  printf '不足しているツール: %s PATH に追加するかインストールしてから、repo-secure-check を再実行してください。' \
    "$(IFS=' / '; printf '%s' "${missing_details[*]}")"
}

target_repo_path=""
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_root="$(CDPATH= cd -- "${script_dir}/.." && pwd)"
strict=0
as_json=0

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
    -Strict)
      strict=1
      shift
      ;;
    -AsJson)
      as_json=1
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

target_repo_path="$(full_path "${target_repo_path}")"
source_root="$(full_path "${source_root}")"

if [[ ! -d "${target_repo_path}" ]]; then
  printf 'Target repository path not found: %s\n' "${target_repo_path}" >&2
  exit 1
fi

instructions_path="${target_repo_path}/.github/copilot-instructions.md"
copilot_hooks_path="${target_repo_path}/.github/hooks"
github_workflows_path="${target_repo_path}/.github/workflows"
is_source_repository=0
if same_path "${target_repo_path}" "${source_root}"; then
  is_source_repository=1
fi

if [[ "${is_source_repository}" -eq 1 ]]; then
  git_hooks_path="${target_repo_path}/repo-template/.githooks"
  git_hooks_label="repo-template/.githooks"
  gitattributes_path="${target_repo_path}/repo-template/.gitattributes"
  gitattributes_label="repo-template/.gitattributes"
else
  git_hooks_path="${target_repo_path}/.githooks"
  git_hooks_label=".githooks"
  gitattributes_path="${target_repo_path}/.gitattributes"
  gitattributes_label=".gitattributes"
fi
repo_hook_scripts_path="${target_repo_path}/.github/hooks/scripts"
repo_hook_scripts_label=".github/hooks/scripts"

is_git_repo=0
if test_git_repository "${target_repo_path}"; then
  is_git_repo=1
fi

core_hooks_configured=""
core_hooks_resolved_path=""
if [[ "${is_git_repo}" -eq 1 ]]; then
  core_hooks_configured="$(git -C "${target_repo_path}" config --local --get core.hooksPath 2>/dev/null || true)"
  if [[ -n "${core_hooks_configured}" ]]; then
    if [[ "${core_hooks_configured}" = /* ]]; then
      core_hooks_resolved_path="$(full_path "${core_hooks_configured}")"
    else
      core_hooks_resolved_path="$(full_path "${target_repo_path}/${core_hooks_configured}")"
    fi
  fi
fi

instructions_ok=0
[[ -f "${instructions_path}" ]] && instructions_ok=1

copilot_hooks_ok=0
if test_required_copilot_safety_hook "${copilot_hooks_path}"; then
  copilot_hooks_ok=1
fi

github_workflows_ok=0
github_workflows_details=""
mapfile -t github_workflow_names < <(list_workflow_names "${github_workflows_path}" 2>/dev/null || true)
if ((${#github_workflow_names[@]} == 0)); then
  github_workflows_details=".github/workflows/*.yml または *.yaml がありません。repo-onboarding で repo の技術スタックに合う workflow template を明示的に導入してください。"
else
  should_check_dotnet_template_compatibility=0
  if ((${#github_workflow_names[@]} == 1)) && [[ "${github_workflow_names[0]}" == "dotnet-quality.yml" ]]; then
    should_check_dotnet_template_compatibility=1
  fi
  if [[ "${should_check_dotnet_template_compatibility}" -eq 1 ]] && ! test_dotnet_project "${target_repo_path}"; then
    github_workflows_details=".github/workflows/dotnet-quality.yml は存在しますが、.NET project が検出されません。repo の技術スタックに合う workflow template を明示的に選んでください。"
  else
    github_workflows_ok=1
    github_workflows_details=".github/workflows に YAML workflow が存在します。repo の技術スタックと runtime に合う内容かは onboarding で確認してください。"
  fi
fi

mapfile -t git_hook_issues < <(get_required_git_hook_issues "${git_hooks_path}" 2>/dev/null || true)
git_hook_issues=("${git_hook_issues[@]}")
if ((${#git_hook_issues[@]} == 1)) && [[ -z "${git_hook_issues[0]}" ]]; then
  git_hook_issues=()
fi
git_hooks_ok=0
if ((${#git_hook_issues[@]} == 0)) && [[ -d "${git_hooks_path}" ]]; then
  git_hooks_ok=1
fi

mapfile -t git_hook_line_ending_issues < <(get_git_hook_line_ending_issues "${git_hooks_path}" "${git_hooks_label}" "${repo_hook_scripts_path}" "${repo_hook_scripts_label}" "${gitattributes_path}" "${gitattributes_label}" 2>/dev/null || true)
git_hook_line_ending_issues=("${git_hook_line_ending_issues[@]}")
if ((${#git_hook_line_ending_issues[@]} == 1)) && [[ -z "${git_hook_line_ending_issues[0]}" ]]; then
  git_hook_line_ending_issues=()
fi
git_hook_line_endings_ok=0
if ((${#git_hook_line_ending_issues[@]} == 0)); then
  git_hook_line_endings_ok=1
fi

tool_dependency_state="$(tool_dependency_state_json "${copilot_hooks_path}")"
tool_dependencies_ok=1
if grep -q '"missing":\[[^]]' <<<"${tool_dependency_state}"; then
  tool_dependencies_ok=0
fi

core_hooks_ok=0
core_hooks_details=""
install_hooks_command="bash \"${source_root}/scripts/install-git-hooks.sh\" -TargetRepoPath \"${target_repo_path}\""
if [[ "${is_git_repo}" -eq 0 ]]; then
  core_hooks_details="Git repository として初期化されていません。"
elif [[ -z "${core_hooks_configured}" ]]; then
  core_hooks_details="core.hooksPath が設定されていません。${install_hooks_command} を実行して git hooks を有効化してください。"
elif [[ -n "${core_hooks_resolved_path}" && "${core_hooks_resolved_path}" == "$(full_path "${git_hooks_path}")" ]]; then
  core_hooks_ok=1
  core_hooks_details="core.hooksPath は許可された git hooks path を指しています。"
else
  core_hooks_details="core.hooksPath は '${core_hooks_configured}' を指しており、許可された git hooks path と一致しません。${install_hooks_command} を実行して修正してください。"
fi

missing=()
[[ "${instructions_ok}" -eq 1 ]] || missing+=("repoInstructions")
[[ "${copilot_hooks_ok}" -eq 1 ]] || missing+=("copilotHooks")
[[ "${git_hooks_ok}" -eq 1 ]] || missing+=("gitHooksDirectory")
[[ "${git_hook_line_endings_ok}" -eq 1 ]] || missing+=("gitHookLineEndings")
[[ "${github_workflows_ok}" -eq 1 ]] || missing+=("githubWorkflows")
[[ "${core_hooks_ok}" -eq 1 ]] || missing+=("coreHooksPath")
[[ "${tool_dependencies_ok}" -eq 1 ]] || missing+=("toolDependencies")

warnings=("Branch Protection / Ruleset はローカルでは確認できません。")
if [[ "${is_git_repo}" -eq 0 ]]; then
  warnings+=("Git repository として初期化されていないため、core.hooksPath は不足として扱います。")
fi

tool_dependency_details="$(tool_dependency_details_text "${copilot_hooks_path}")"

if [[ "${as_json}" -eq 1 ]]; then
  printf '{'
  printf '"targetRepoPath":'
  json_string "${target_repo_path}"
  printf ',"isGitRepo":'
  json_bool "${is_git_repo}"
  printf ',"missing":['
  first=1
  for value in "${missing[@]}"; do
    [[ "${first}" -eq 1 ]] || printf ','
    json_string "${value}"
    first=0
  done
  printf '],"warnings":['
  first=1
  for value in "${warnings[@]}"; do
    [[ "${first}" -eq 1 ]] || printf ','
    json_string "${value}"
    first=0
  done
  printf '],"toolDependencies":%s' "${tool_dependency_state}"
  printf ',"checks":['
  checks_first=1
  append_check() {
    local key="$1" label="$2" ok="$3" path="$4" details="$5"
    [[ "${checks_first}" -eq 1 ]] || printf ','
    printf '{'
    printf '"key":'; json_string "${key}"
    printf ',"label":'; json_string "${label}"
    printf ',"ok":'; json_bool "${ok}"
    printf ',"path":'; json_string "${path}"
    printf ',"details":'; json_string "${details}"
    printf '}'
    checks_first=0
  }
  append_check "repoInstructions" "repo instructions" "${instructions_ok}" "${instructions_path}" "$([[ "${instructions_ok}" -eq 1 ]] && printf 'repo-wide instructions が存在します。' || printf 'repo-wide instructions がありません。')"
  append_check "copilotHooks" "Copilot hooks" "${copilot_hooks_ok}" "${copilot_hooks_path}" "$([[ "${copilot_hooks_ok}" -eq 1 ]] && printf 'Copilot safety hook safety-guard.json が存在します。session continuity hooks は標準運用から封印済みで、必要な repo だけ明示 opt-in します。' || printf 'Copilot safety hook safety-guard.json がありません。')"
  append_check "gitHooksDirectory" "${git_hooks_label}" "${git_hooks_ok}" "${git_hooks_path}" "$([[ "${git_hooks_ok}" -eq 1 ]] && printf '%s に pre-commit / pre-push / secret-guard / commit-safety-guard が存在し、pre-commit / pre-push から呼び出されています。' "${git_hooks_label}" || printf '%s の必須 hook が不足または未接続です: %s' "${git_hooks_label}" "$(IFS=', '; printf '%s' "${git_hook_issues[*]}")")"
  append_check "gitHookLineEndings" "git hook line endings" "${git_hook_line_endings_ok}" "${gitattributes_path}" "$([[ "${git_hook_line_endings_ok}" -eq 1 ]] && printf '%s に LF 固定ルールがあり、%s の shell hook は CRLF を含みません。' "${gitattributes_label}" "${git_hooks_label}" || printf 'Git hook line ending policy issue(s): %s' "$(IFS=' '; printf '%s' "${git_hook_line_ending_issues[*]}")")"
  append_check "githubWorkflows" "GitHub Actions workflows" "${github_workflows_ok}" "${github_workflows_path}" "${github_workflows_details}"
  append_check "coreHooksPath" "core.hooksPath" "${core_hooks_ok}" "${core_hooks_resolved_path:-${git_hooks_path}}" "${core_hooks_details}"
  append_check "toolDependencies" "hook tool dependencies" "${tool_dependencies_ok}" "${copilot_hooks_path}" "${tool_dependency_details}"
  printf ']}'
  printf '\n'
else
  write_section "Repo secure check"
  printf 'Target : %s\n' "${target_repo_path}"
  printf 'Git    : %s\n' "${is_git_repo}"
  report_check() {
    local ok="$1" label="$2" path="$3" details="$4"
    if [[ "${ok}" -eq 1 ]]; then
      printf '[OK] %s\n' "${label}"
    else
      printf '[MISSING] %s\n' "${label}"
    fi
    printf '  Path    : %s\n' "${path}"
    printf '  Details : %s\n' "${details}"
  }
  report_check "${instructions_ok}" "repo instructions" "${instructions_path}" "$([[ "${instructions_ok}" -eq 1 ]] && printf 'repo-wide instructions が存在します。' || printf 'repo-wide instructions がありません。')"
  report_check "${copilot_hooks_ok}" "Copilot hooks" "${copilot_hooks_path}" "$([[ "${copilot_hooks_ok}" -eq 1 ]] && printf 'Copilot safety hook safety-guard.json が存在します。session continuity hooks は標準運用から封印済みで、必要な repo だけ明示 opt-in します。' || printf 'Copilot safety hook safety-guard.json がありません。')"
  report_check "${git_hooks_ok}" "${git_hooks_label}" "${git_hooks_path}" "$([[ "${git_hooks_ok}" -eq 1 ]] && printf '%s に pre-commit / pre-push / secret-guard / commit-safety-guard が存在し、pre-commit / pre-push から呼び出されています。' "${git_hooks_label}" || printf '%s の必須 hook が不足または未接続です: %s' "${git_hooks_label}" "$(IFS=', '; printf '%s' "${git_hook_issues[*]}")")"
  report_check "${git_hook_line_endings_ok}" "git hook line endings" "${gitattributes_path}" "$([[ "${git_hook_line_endings_ok}" -eq 1 ]] && printf '%s に LF 固定ルールがあり、%s の shell hook は CRLF を含みません。' "${gitattributes_label}" "${git_hooks_label}" || printf 'Git hook line ending policy issue(s): %s' "$(IFS=' '; printf '%s' "${git_hook_line_ending_issues[*]}")")"
  report_check "${github_workflows_ok}" "GitHub Actions workflows" "${github_workflows_path}" "${github_workflows_details}"
  report_check "${core_hooks_ok}" "core.hooksPath" "${core_hooks_resolved_path:-${git_hooks_path}}" "${core_hooks_details}"
  report_check "${tool_dependencies_ok}" "hook tool dependencies" "${copilot_hooks_path}" "${tool_dependency_details}"
  if ((${#missing[@]} == 0)); then
    printf 'All local safety valves are present.\n'
  else
    printf 'WARNING: Missing local safety valves: %s\n' "$(IFS=', '; printf '%s' "${missing[*]}")" >&2
  fi
  for value in "${warnings[@]}"; do
    printf 'WARNING: %s\n' "${value}" >&2
  done
fi

if [[ "${strict}" -eq 1 && ${#missing[@]} -gt 0 ]]; then
  exit 1
fi
