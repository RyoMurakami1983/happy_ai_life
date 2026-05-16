#!/usr/bin/env bash
set -euo pipefail

raw="$(cat || true)"
if [[ -z "${raw}" ]]; then
  exit 0
fi

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
default_shell_tool_names=(bash powershell)
default_active_rule_ids=(
  maintenance-mode-manual-only
  git-hooks-no-verify
  git-hooks-path-change
  git-hooks-update-index-bypass
  git-push-force
  git-commit-secret-scan
  git-push-secret-scan
  gh-pr-create-secret-scan
  rm-rf-root
  rm-rf-dot
  windows-del-force-recursive
  format-command
  mkfs-command
  shutdown-command
  reboot-command
  init-zero-command
  poweroff-command
  stop-computer-command
  restart-computer-command
  git-reset-hard
  powershell-encoded-command
  invoke-expression
  powershell-command-invoke-expression
  curl-pipe-sh
  wget-pipe-sh
)
required_specialized_rule_ids=(
  maintenance-mode-manual-only
  git-hooks-no-verify
  git-hooks-path-change
  git-hooks-update-index-bypass
  git-push-force
  git-commit-secret-scan
  git-push-secret-scan
  gh-pr-create-secret-scan
)
default_pattern_rules_json="$(cat <<'JSON'
[
  {"id":"rm-rf-root","pattern":"\\brm\\s+-rf\\s+\\/","matchAgainst":"normalized"},
  {"id":"rm-rf-dot","pattern":"\\brm\\s+-rf\\s+\\.(?:\\s|$)","matchAgainst":"normalized"},
  {"id":"windows-del-force-recursive","pattern":"\\bdel\\s+\\/f\\s+\\/s\\s+\\/q\\b","matchAgainst":"normalized"},
  {"id":"format-command","pattern":"\\bformat\\b","matchAgainst":"normalized"},
  {"id":"mkfs-command","pattern":"\\bmkfs\\b","matchAgainst":"normalized"},
  {"id":"shutdown-command","pattern":"\\bshutdown\\b","matchAgainst":"normalized"},
  {"id":"reboot-command","pattern":"\\breboot\\b","matchAgainst":"normalized"},
  {"id":"init-zero-command","pattern":"\\binit\\s+0\\b","matchAgainst":"normalized"},
  {"id":"poweroff-command","pattern":"\\bpoweroff\\b","matchAgainst":"normalized"},
  {"id":"stop-computer-command","pattern":"\\bstop-computer\\b","matchAgainst":"normalized"},
  {"id":"restart-computer-command","pattern":"\\brestart-computer\\b","matchAgainst":"normalized"},
  {"id":"remove-item-recurse-force","pattern":"(?=.*\\bremove-item\\b)(?=.*(?:^|\\s)-recurse(?:\\s|$))(?=.*(?:^|\\s)-force(?:\\s|$))","matchAgainst":"normalized"},
  {"id":"git-reset-hard","pattern":"\\bgit\\s+reset\\s+--hard\\b","matchAgainst":"normalized"},
  {"id":"powershell-encoded-command","pattern":"(^|[;&|]\\s*)(?:powershell|pwsh)(?:\\.exe)?(?:\\s+[^;&|]+)*\\s+-(?:encodedcommand|enc|ec)(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"invoke-expression","pattern":"(^|[;&|]\\s*)(?:(?:[\\w.\\\\]+\\\\)?invoke-expression|iex)(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"powershell-command-invoke-expression","pattern":"(^|[;&|]\\s*)(?:powershell|pwsh)(?:\\.exe)?(?:\\s+[^;&|]+)*\\s+-(?:command|c)\\s+(?:\"|')?(?:&\\s*\\{\\s*)?(?:(?:[\\w.\\\\]+\\\\)?invoke-expression|iex)\\b","matchAgainst":"normalized"},
  {"id":"curl-pipe-sh","pattern":"\\bcurl(?:\\.exe)?\\b[^;&|]*\\|\\s*sh\\b","matchAgainst":"normalized"},
  {"id":"wget-pipe-sh","pattern":"\\bwget(?:\\.exe)?\\b[^;&|]*\\|\\s*sh\\b","matchAgainst":"normalized"}
]
JSON
)"
shell_tool_names=("${default_shell_tool_names[@]}")
active_rule_ids=("${default_active_rule_ids[@]}")
pattern_rules=()

deny() {
  jq -nc --arg reason "$1" \
    '{permissionDecision:"deny", permissionDecisionReason:$reason}'
}

resolve_policy_path() {
  local candidate
  candidate="${script_dir}/../../../policy/guard-policy.json"
  if [[ -f "${candidate}" ]]; then
    printf '%s\n' "${candidate}"
  fi
}

load_default_pattern_rules() {
  mapfile -t pattern_rules < <(jq -cr '.[]' <<<"${default_pattern_rules_json}")
}

load_guard_policy() {
  local policy_path
  shell_tool_names=("${default_shell_tool_names[@]}")
  active_rule_ids=("${default_active_rule_ids[@]}")
  load_default_pattern_rules

  policy_path="$(resolve_policy_path)"
  if [[ -z "${policy_path}" ]]; then
    return 0
  fi

  if ! jq -e '
    . as $policy
    | .schemaVersion == 1
    and (.toolNames.shell | type == "array" and length > 0)
    and (.toolNames.fileWrite | type == "array" and length > 0)
    and all(.toolNames.shell[]; type == "string" and test("\\S"))
    and all(.toolNames.fileWrite[]; type == "string" and test("\\S"))
    and (.denyCommandRules | type == "array" and length > 0)
    and all(.denyCommandRules[]; (.id | type == "string" and test("\\S")) and (.kind | IN("specialized"; "pattern")) and (if .kind == "pattern" then ((.pattern | type == "string" and test("\\S")) and (.matchAgainst | IN("normalized"; "compact")) and (.pattern as $pattern | try ("" | test($pattern)) catch false)) else ((has("pattern") | not) and (has("matchAgainst") | not)) end))
    and (["maintenance-mode-manual-only","git-hooks-no-verify","git-hooks-path-change","git-hooks-update-index-bypass","git-push-force","git-commit-secret-scan","git-push-secret-scan","gh-pr-create-secret-scan"] | all(.[] as $id | any($policy.denyCommandRules[]; .id == $id)))
  ' "${policy_path}" >/dev/null 2>&1; then
    return 0
  fi

  mapfile -t shell_tool_names < <(jq -r '.toolNames.shell[]' "${policy_path}")
  mapfile -t active_rule_ids < <(jq -r '.denyCommandRules[].id' "${policy_path}")
  mapfile -t pattern_rules < <(jq -cr '.denyCommandRules[] | select(.kind == "pattern") | {id, pattern, matchAgainst}' "${policy_path}")
}

rule_enabled() {
  local target="$1"
  local rule
  for rule in "${active_rule_ids[@]}"; do
    if [[ "${rule}" == "${target}" ]]; then
      return 0
    fi
  done
  return 1
}

resolve_gitleaks() {
  if [[ -n "${GITLEAKS_BIN:-}" ]]; then
    if [[ -x "${GITLEAKS_BIN}" ]]; then
      printf '%s\n' "${GITLEAKS_BIN}"
      return 0
    fi
    command -v "${GITLEAKS_BIN}" 2>/dev/null || return 1
    return 0
  fi

  command -v gitleaks 2>/dev/null || return 1
}

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || true
}

scratch_dir() {
  local root="$1"
  local git_dir
  git_dir="$(git -C "${root}" rev-parse --git-dir 2>/dev/null || true)"
  if [[ -z "${git_dir}" ]]; then
    return 1
  fi
  case "${git_dir}" in
    /*) ;;
    *) git_dir="${root}/${git_dir}" ;;
  esac
  mkdir -p "${git_dir}/happy-secret-scan"
  mktemp -d "${git_dir}/happy-secret-scan/copilot.XXXXXX"
}

gitleaks_config_args=()
set_gitleaks_config_args() {
  local root="$1"
  gitleaks_config_args=()
  if [[ -f "${root}/.gitleaks.toml" ]]; then
    gitleaks_config_args=(--config "${root}/.gitleaks.toml")
  fi
}

scan_staged_for_secrets() {
  local root gitleaks scratch snapshot
  root="$(repo_root)"
  if [[ -z "${root}" ]]; then
    return 0
  fi
  if ! gitleaks="$(resolve_gitleaks)"; then
    deny "gitleaks is required before AI can run git commit."
    return 1
  fi
  if git -C "${root}" diff --cached --quiet --exit-code 2>/dev/null; then
    return 0
  fi

  scratch="$(scratch_dir "${root}")" || {
    deny "Failed to prepare staged content for AI pre-commit secret scan."
    return 1
  }
  trap 'rm -rf "${scratch}"' RETURN
  snapshot="${scratch}/snapshot"
  mkdir -p "${snapshot}"

  git -C "${root}" -c core.quotepath=false diff --cached --name-only -z --diff-filter=ACMR \
    | git -C "${root}" checkout-index --prefix="${snapshot}/" --stdin -z >/dev/null 2>&1 || {
      deny "Failed to prepare staged content for AI pre-commit secret scan."
      return 1
    }

  set_gitleaks_config_args "${root}"
  if ! "${gitleaks}" dir "${snapshot}" "${gitleaks_config_args[@]}" --no-banner --redact=100 --exit-code 1 >/dev/null 2>&1; then
    deny "Potential secrets were detected in staged changes. Commit was blocked before secrets entered Git history."
    return 1
  fi
}

unpushed_log_opts() {
  local root="$1"
  local upstream range
  upstream="$(git -C "${root}" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  if [[ -n "${upstream}" ]]; then
    range="${upstream}..HEAD"
  else
    range="HEAD --not --remotes"
  fi

  if ! git -C "${root}" rev-list ${range} >/dev/null 2>&1; then
    return 1
  fi
  if [[ -z "$(git -C "${root}" rev-list ${range} 2>/dev/null || true)" ]]; then
    return 1
  fi
  printf '%s\n' "${range}"
}

scan_unpushed_for_secrets() {
  local action_name="$1"
  local root gitleaks log_opts
  root="$(repo_root)"
  if [[ -z "${root}" ]]; then
    return 0
  fi
  if ! gitleaks="$(resolve_gitleaks)"; then
    deny "gitleaks is required before AI can run ${action_name}."
    return 1
  fi
  if ! log_opts="$(unpushed_log_opts "${root}")"; then
    return 0
  fi

  set_gitleaks_config_args "${root}"
  if ! "${gitleaks}" git "${root}" --log-opts "${log_opts}" "${gitleaks_config_args[@]}" --no-banner --redact=100 --exit-code 1 >/dev/null 2>&1; then
    deny "Potential secrets were detected in commits that may be published. ${action_name} was blocked."
    return 1
  fi
}

# toolName を取得（例: "bash", "powershell"）
if ! tool_name="$(jq -r '(.toolName // .tool_name // empty) | strings' <<<"${raw}" 2>/dev/null)"; then
  exit 0
fi
load_guard_policy
if [[ ! " ${shell_tool_names[*]} " =~ (^|[[:space:]])"${tool_name}"($|[[:space:]]) ]]; then
  exit 0
fi

# toolArgs / tool_input は JSON 文字列または object の両方を受ける
if ! command="$(jq -r '
  def selected_args:
    if .toolArgs? != null then .toolArgs
    elif .tool_input? != null then .tool_input
    else empty end;
  def parsed_args:
    selected_args | if type == "string" then (fromjson? // .) else . end;
  parsed_args as $args
  | if ($args | type) == "object" then ($args.command // empty)
    elif ($args | type) == "string" then $args
    else empty
    end
' <<<"${raw}" 2>/dev/null)"; then
  exit 0
fi
if [[ -z "${command}" ]]; then
  exit 0
fi

normalized="$(tr '[:upper:]' '[:lower:]' <<<"${command}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
compact="$(tr -s '[:space:]' ' ' <<<"${normalized}")"
normalized_for_path="${normalized//\//\\}"
maintenance_state_path=""
if [[ -n "${HOME:-}" ]]; then
  maintenance_state_path="$(tr '[:upper:]' '[:lower:]' <<<"${HOME//\//\\}\\.copilot\\maintenance-mode.json")"
fi

is_git_commit=0
is_git_push=0
is_gh_pr_create=0
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+commit([[:space:]]|$)' <<<"${compact}" && is_git_commit=1
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+push([[:space:]]|$)' <<<"${compact}" && is_git_push=1
grep -E -q '(^|[;&|][[:space:]]*)gh[[:space:]]+pr[[:space:]]+create([[:space:]]|$)' <<<"${compact}" && is_gh_pr_create=1

has_no_verify=0
grep -E -q '(^|[[:space:]])--no-verify([[:space:]]|$)' <<<"${compact}" && has_no_verify=1
has_commit_n=0
if [[ "${is_git_commit}" -eq 1 ]] && grep -E -q '(^|[[:space:]])-[a-z]*n[a-z]*([[:space:]]|$)' <<<"${compact}"; then
  has_commit_n=1
fi

touches_maintenance_mode_script=0
touches_maintenance_state_file=0
grep -E -q '(^|[;&|][[:space:]]*)(\.?[[:space:]]+)?(&[[:space:]]+)?[^;&|]*(enter|exit)-copilot-maintenance-mode(\.ps1)?([[:space:]]|$|[;&|])' <<<"${compact}" && touches_maintenance_mode_script=1
if [[ -n "${maintenance_state_path}" && "${normalized_for_path}" == *"${maintenance_state_path}"* ]]; then
  touches_maintenance_state_file=1
elif grep -E -q 'maintenance-mode\.json|(\$home|\$env:home|\$\{home\}|~)[\\/]\.copilot[\\/].*maintenance-mode\.json' <<<"${compact}"; then
  touches_maintenance_state_file=1
fi

if rule_enabled "maintenance-mode-manual-only" && { [[ "${touches_maintenance_mode_script}" -eq 1 ]] || [[ "${touches_maintenance_state_file}" -eq 1 ]]; }; then
  deny "AI is not allowed to enter or exit maintenance mode, or modify the maintenance state file. Ask a human to run the maintenance scripts manually."
  exit 0
fi

has_git_hooks_no_verify_violation=0
if { [[ "${is_git_commit}" -eq 1 ]] && { [[ "${has_no_verify}" -eq 1 ]] || [[ "${has_commit_n}" -eq 1 ]]; }; } || { [[ "${is_git_push}" -eq 1 ]] && [[ "${has_no_verify}" -eq 1 ]]; }; then
  has_git_hooks_no_verify_violation=1
fi

if rule_enabled "git-hooks-no-verify" && [[ "${has_git_hooks_no_verify_violation}" -eq 1 ]]; then
  deny "AI is not allowed to bypass Git hooks with --no-verify or git commit -n."
  exit 0
fi

is_git_config_hooks_path_write=0
is_git_config_hooks_path_unset=0
is_git_config_remove_core_section=0
has_inline_git_hooks_path_config=0
is_git_update_index_skip_worktree=0
is_git_update_index_assume_unchanged=0
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+config([[:space:]]|$)' <<<"${compact}" &&
  grep -E -q '(^|[[:space:]])core\.hookspath([[:space:]]*=|[[:space:]])[^;&|]+' <<<"${compact}" &&
  is_git_config_hooks_path_write=1
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+config([[:space:]]+[^;&|]+)*[[:space:]]+--unset(-all)?([[:space:]]+[^;&|]+)*[[:space:]]+core\.hookspath([[:space:]]*($|[;&|]))' <<<"${compact}" && is_git_config_hooks_path_unset=1
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+config([[:space:]]+[^;&|]+)*[[:space:]]+--remove-section([[:space:]]+[^;&|]+)*[[:space:]]+core([[:space:]]*($|[;&|]))' <<<"${compact}" && is_git_config_remove_core_section=1
grep -E -q '(^|[;&|][[:space:]]*)git([[:space:]]+[^;&|]+)*[[:space:]]+-c[[:space:]]+core\.hookspath([[:space:]]*=|[[:space:]])[^;&|]+' <<<"${compact}" && has_inline_git_hooks_path_config=1
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+update-index([[:space:]]|$)' <<<"${compact}" &&
  grep -E -q '(^|[[:space:]])--skip-worktree([[:space:]]|$)' <<<"${compact}" &&
  is_git_update_index_skip_worktree=1
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+update-index([[:space:]]|$)' <<<"${compact}" &&
  grep -E -q '(^|[[:space:]])--assume-unchanged([[:space:]]|$)' <<<"${compact}" &&
  is_git_update_index_assume_unchanged=1

if rule_enabled "git-hooks-path-change" && { [[ "${is_git_config_hooks_path_write}" -eq 1 ]] || [[ "${is_git_config_hooks_path_unset}" -eq 1 ]] || [[ "${is_git_config_remove_core_section}" -eq 1 ]] || [[ "${has_inline_git_hooks_path_config}" -eq 1 ]]; }; then
  deny "AI is not allowed to disable or bypass Git hooks via core.hooksPath changes, git -c core.hooksPath, or git update-index skip-worktree/assume-unchanged."
  exit 0
fi

if rule_enabled "git-hooks-update-index-bypass" && { [[ "${is_git_update_index_skip_worktree}" -eq 1 ]] || [[ "${is_git_update_index_assume_unchanged}" -eq 1 ]]; }; then
  deny "AI is not allowed to disable or bypass Git hooks via core.hooksPath changes, git -c core.hooksPath, or git update-index skip-worktree/assume-unchanged."
  exit 0
fi

if rule_enabled "git-push-force" && grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+push([[:space:]]+[^;&|]+)*[[:space:]]+(-f|--force|--force-with-lease(=[^;&|]+)?)([[:space:]]|$|[;&|])' <<<"${compact}"; then
  deny "Blocked potentially destructive command: ${command}"
  exit 0
fi

if rule_enabled "git-commit-secret-scan" && [[ "${is_git_commit}" -eq 1 ]]; then
  scan_staged_for_secrets || exit 0
fi

if rule_enabled "git-push-secret-scan" && [[ "${is_git_push}" -eq 1 ]]; then
  scan_unpushed_for_secrets "git push" || exit 0
fi

if rule_enabled "gh-pr-create-secret-scan" && [[ "${is_gh_pr_create}" -eq 1 ]]; then
  scan_unpushed_for_secrets "gh pr create" || exit 0
fi

for rule_json in "${pattern_rules[@]}"; do
  rule_id="$(jq -r '.id' <<<"${rule_json}")"
  if ! rule_enabled "${rule_id}"; then
    continue
  fi

  match_against="$(jq -r '.matchAgainst' <<<"${rule_json}")"
  candidate="${normalized}"
  if [[ "${match_against}" == "compact" ]]; then
    candidate="${compact}"
  fi

  pattern="$(jq -r '.pattern' <<<"${rule_json}")"
  if [[ "$(jq -nr --arg candidate "${candidate}" --arg pattern "${pattern}" '$candidate | test($pattern)')" == "true" ]]; then
    deny "Blocked potentially destructive command: ${command}"
    exit 0
  fi
done

# allow: 何も返さない
exit 0
