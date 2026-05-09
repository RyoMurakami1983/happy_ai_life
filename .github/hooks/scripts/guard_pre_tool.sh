#!/usr/bin/env bash
set -euo pipefail

raw="$(cat || true)"
if [[ -z "${raw}" ]]; then
  exit 0
fi

deny() {
  jq -nc --arg reason "$1" \
    '{permissionDecision:"deny", permissionDecisionReason:$reason}'
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
if [[ "${tool_name}" != "bash" && "${tool_name}" != "powershell" ]]; then
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
normalized="$(tr -s '[:space:]' ' ' <<<"${normalized}")"

is_git_commit=0
is_git_push=0
is_gh_pr_create=0
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+commit([[:space:]]|$)' <<<"${normalized}" && is_git_commit=1
grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+push([[:space:]]|$)' <<<"${normalized}" && is_git_push=1
grep -E -q '(^|[;&|][[:space:]]*)gh[[:space:]]+pr[[:space:]]+create([[:space:]]|$)' <<<"${normalized}" && is_gh_pr_create=1

has_no_verify=0
grep -E -q '(^|[[:space:]])--no-verify([[:space:]]|$)' <<<"${normalized}" && has_no_verify=1
has_commit_n=0
if [[ "${is_git_commit}" -eq 1 ]] && grep -E -q '(^|[[:space:]])-[a-z]*n[a-z]*([[:space:]]|$)' <<<"${normalized}"; then
  has_commit_n=1
fi

if { [[ "${is_git_commit}" -eq 1 ]] && { [[ "${has_no_verify}" -eq 1 ]] || [[ "${has_commit_n}" -eq 1 ]]; }; } ||
   { [[ "${is_git_push}" -eq 1 ]] && [[ "${has_no_verify}" -eq 1 ]]; }; then
  deny "AI is not allowed to bypass Git hooks with --no-verify or git commit -n."
  exit 0
fi

if grep -E -q '(^|[;&|][[:space:]]*)git[[:space:]]+push([[:space:]]+[^;&|]+)*[[:space:]]+(-f|--force|--force-with-lease(=[^;&|]+)?)([[:space:]]|$|[;&|])' <<<"${normalized}"; then
  deny "Blocked potentially destructive command: ${command}"
  exit 0
fi

if [[ "${is_git_commit}" -eq 1 ]]; then
  scan_staged_for_secrets || exit 0
fi

if [[ "${is_git_push}" -eq 1 ]]; then
  scan_unpushed_for_secrets "git push" || exit 0
fi

if [[ "${is_gh_pr_create}" -eq 1 ]]; then
  scan_unpushed_for_secrets "gh pr create" || exit 0
fi

if grep -E -q '(^|[;&|][[:space:]]*)(powershell|pwsh)(\.exe)?([[:space:]]+[^;&|]+)*[[:space:]]+-(encodedcommand|enc|ec)([[:space:]]|$|[;&|])' <<<"${normalized}" ||
   grep -E -q '(^|[;&|][[:space:]]*)((([[:alnum:]_.\\]+\\)?invoke-expression)|iex)([[:space:]]|$|[;&|])' <<<"${normalized}" ||
   grep -E -q '(^|[;&|][[:space:]]*)(powershell|pwsh)(\.exe)?([[:space:]]+[^;&|]+)*[[:space:]]+-(command|c)[[:space:]]+["'\'']?(&[[:space:]]*\{[[:space:]]*)?((([[:alnum:]_.\\]+\\)?invoke-expression)|iex)([[:space:]]|$|["'\'']|[;&|])' <<<"${normalized}" ||
   grep -E -q '(^|[;&|][[:space:]]*)curl(\.exe)?[^;&|]*\|[[:space:]]*sh([[:space:]]|$)' <<<"${normalized}" ||
   grep -E -q '(^|[;&|][[:space:]]*)wget(\.exe)?[^;&|]*\|[[:space:]]*sh([[:space:]]|$)' <<<"${normalized}"; then
  deny "Blocked potentially destructive command: ${command}"
  exit 0
fi

# まずは破壊系だけを最小ブロック
# 必要になってから増やす（誤ブロックで作業が止まるのを避ける）
deny_patterns=(
  'rm -rf /'
  'rm -rf .'
  'mkfs'
  'format '
  'shutdown'
  'reboot'
  'poweroff'
  'init 0'
  'stop-computer'
  'restart-computer'
  'git push --force'
  'git reset --hard'
)

for p in "${deny_patterns[@]}"; do
  if grep -F -q -- "${p}" <<<"${normalized}"; then
    # deny を返す（JSON）
    deny "Blocked potentially destructive command: ${command}"
    exit 0
  fi
done

# allow: 何も返さない
exit 0
