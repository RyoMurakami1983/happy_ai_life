#!/usr/bin/env bash
set -euo pipefail

raw="$(cat || true)"
if [[ -z "${raw}" ]]; then
  exit 0
fi

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hook_event="${HAPPY_AI_LIFE_HOOK_EVENT:-preToolUse}"
if [[ "${hook_event}" != "preToolUse" && "${hook_event}" != "permissionRequest" ]]; then
  hook_event="preToolUse"
fi
default_shell_tool_names=(bash powershell)
default_file_write_tool_names=(create edit)
default_path_property_names=(path filePath file_path targetPath target_path)
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
  rm-fr-root
  rm-r-f-root
  rm-f-r-root
  rm-rf-dot
  rm-fr-dot
  rm-r-f-dot
  rm-f-r-dot
  windows-del-force-recursive
  windows-del-force-quiet-recursive
  windows-del-recursive-force-quiet
  windows-del-recursive-quiet-force
  windows-del-quiet-force-recursive
  windows-del-quiet-recursive-force
  format-command
  mkfs-command
  shutdown-command
  reboot-command
  init-zero-command
  poweroff-command
  stop-computer-command
  restart-computer-command
  remove-item-recurse-force
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
  {"id":"rm-rf-root","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*f[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"rm-fr-root","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*r[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"rm-r-f-root","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*f[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"rm-f-r-root","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*r[a-z]*[^;&|]*\\s+\\/(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"rm-rf-dot","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*f[a-z]*[^;&|]*\\s+\\.(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"rm-fr-dot","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*r[a-z]*[^;&|]*\\s+\\.(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"rm-r-f-dot","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*r[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*f[a-z]*[^;&|]*\\s+\\.(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"rm-f-r-dot","pattern":"(^|[;&|]\\s*)(?:(?:sudo|doas)\\s+)?(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?(?:(?:sudo|doas)\\s+)?rm[^;&|]*\\s-[a-z]*f[a-z]*(?=\\s|$|[;&|])[^;&|]*\\s-[a-z]*r[a-z]*[^;&|]*\\s+\\.(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"windows-del-force-recursive","pattern":"(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"windows-del-force-quiet-recursive","pattern":"(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"windows-del-recursive-force-quiet","pattern":"(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"windows-del-recursive-quiet-force","pattern":"(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"windows-del-quiet-force-recursive","pattern":"(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"windows-del-quiet-recursive-force","pattern":"(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?del[^;&|]*\\s\\/q(?=\\s|$|[;&|])[^;&|]*\\s\\/s(?=\\s|$|[;&|])[^;&|]*\\s\\/f(?=\\s|$|[;&|])","matchAgainst":"normalized"},
  {"id":"format-command","pattern":"(^|[;&|]\\s*)(?:(?:cmd|cmd\\.exe)\\s+\\/c\\s+)?format(?:\\.com|\\.exe)?(?:\\s|$)","matchAgainst":"normalized"},
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
default_protected_paths_json="$(cat <<'JSON'
[
  {"id":"repo-hooks","path":".github/hooks/**","scope":"directory","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"repo-githooks","path":".githooks/**","scope":"directory","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"repo-workflows","path":".github/workflows/**","scope":"directory","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"repo-instructions-dir","path":".github/instructions/**","scope":"directory","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"repo-skills-dir","path":".github/skills/**","scope":"directory","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"agents-skills-dir","path":".agents/skills/**","scope":"directory","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"claude-skills-dir","path":".claude/skills/**","scope":"directory","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"repo-copilot-instructions","path":".github/copilot-instructions.md","scope":"file","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"repo-mcp","path":".github/mcp.json","scope":"file","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"root-mcp","path":".mcp.json","scope":"file","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"gitleaks-config","path":".gitleaks.toml","scope":"file","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"guard-policy-json","path":"policy/guard-policy.json","scope":"file","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"guard-policy-schema","path":"policy/guard-policy.schema.json","scope":"file","action":"ask","maintenanceScope":"protectedPathEdit"},
  {"id":"maintenance-mode-state","path":"$HOME/.copilot/maintenance-mode.json","scope":"file","action":"deny","maintenanceScope":null},
  {"id":"home-copilot-root","path":"$HOME/.copilot/**","scope":"directory","action":"ask","maintenanceScope":null}
]
JSON
)"
shell_tool_names=("${default_shell_tool_names[@]}")
file_write_tool_names=("${default_file_write_tool_names[@]}")
protected_path_property_names=("${default_path_property_names[@]}")
active_rule_ids=("${default_active_rule_ids[@]}")
pattern_rules=()
protected_path_rules=()

deny() {
  if [[ "${hook_event}" == "permissionRequest" ]]; then
    jq -nc --arg reason "$1" \
      '{behavior:"deny", message:$reason, interrupt:true}'
    return
  fi

  jq -nc --arg reason "$1" \
    '{permissionDecision:"deny", permissionDecisionReason:$reason}'
}

ask() {
  jq -nc --arg reason "$1" \
    '{permissionDecision:"ask", permissionDecisionReason:$reason}'
}

resolve_policy_path() {
  local candidate
  candidate="${script_dir}/../../../policy/guard-policy.json"
  if [[ -f "${candidate}" ]]; then
    printf '%s\n' "${candidate}"
  fi
}

load_default_pattern_rules() {
  pattern_rules=()
  while IFS= read -r rule_json || [[ -n "${rule_json}" ]]; do
    pattern_rules+=("${rule_json}")
  done < <(jq -cr '.[]' <<<"${default_pattern_rules_json}")
}

load_default_protected_path_rules() {
  protected_path_rules=()
  while IFS= read -r rule_json || [[ -n "${rule_json}" ]]; do
    protected_path_rules+=("${rule_json}")
  done < <(jq -cr '.[]' <<<"${default_protected_paths_json}")
}

load_guard_policy() {
  local policy_path
  shell_tool_names=("${default_shell_tool_names[@]}")
  file_write_tool_names=("${default_file_write_tool_names[@]}")
  protected_path_property_names=("${default_path_property_names[@]}")
  active_rule_ids=("${default_active_rule_ids[@]}")
  load_default_pattern_rules
  load_default_protected_path_rules

  policy_path="$(resolve_policy_path)"
  if [[ -z "${policy_path}" ]]; then
    return 0
  fi

  if ! jq -e '
    def trim: sub("^\\s+"; "") | sub("\\s+$"; "");
    def normalize_policy_path:
      (trim | gsub("\\\\"; "/")) as $path
      | if ($path | endswith("/**")) then ($path | ascii_downcase)
        else ($path | sub("/+$"; "") | ascii_downcase)
        end;
    def unique_values($values): (($values | length) == ($values | unique | length));
    . as $policy
    | .schemaVersion == 1
    and (.pathPropertyNames | type == "array" and length > 0)
    and all(.pathPropertyNames[]; type == "string" and test("\\S"))
    and unique_values([.pathPropertyNames[]])
    and (.toolNames.shell | type == "array" and length > 0)
    and (.toolNames.fileWrite | type == "array" and length > 0)
    and all(.toolNames.shell[]; type == "string" and test("\\S"))
    and all(.toolNames.fileWrite[]; type == "string" and test("\\S"))
    and (.protectedPaths | type == "array" and length > 0)
    and all(.protectedPaths[]; (.id | type == "string" and test("\\S")) and (.path | type == "string" and test("\\S")) and (.scope | IN("file"; "directory")) and (.action | IN("ask"; "deny")) and ((.maintenanceScope | type) | IN("string"; "null")) and (if .action == "deny" then .maintenanceScope == null else true end) and (if .scope == "file" then (.path | test("(?:/|\\\\)\\*\\*$") | not) else true end))
    and unique_values([.protectedPaths[].id])
    and unique_values([.protectedPaths[].path | normalize_policy_path])
    and (.denyCommandRules | type == "array" and length > 0)
    and all(.denyCommandRules[]; (.id | type == "string" and test("\\S")) and (.kind | IN("specialized"; "pattern")) and (if .kind == "pattern" then ((.pattern | type == "string" and test("\\S")) and (.matchAgainst | IN("normalized"; "compact")) and (.pattern as $pattern | try ("" | test($pattern)) catch false)) else ((has("pattern") | not) and (has("matchAgainst") | not)) end))
    and unique_values([.denyCommandRules[].id])
    and (["maintenance-mode-manual-only","git-hooks-no-verify","git-hooks-path-change","git-hooks-update-index-bypass","git-push-force","git-commit-secret-scan","git-push-secret-scan","gh-pr-create-secret-scan"] | all(.[] as $id | any($policy.denyCommandRules[]; .id == $id)))
  ' "${policy_path}" >/dev/null 2>&1; then
    return 0
  fi

  shell_tool_names=()
  while IFS= read -r tool || [[ -n "${tool}" ]]; do
    shell_tool_names+=("${tool}")
  done < <(jq -r '.toolNames.shell[]' "${policy_path}")

  file_write_tool_names=()
  while IFS= read -r tool || [[ -n "${tool}" ]]; do
    file_write_tool_names+=("${tool}")
  done < <(jq -r '.toolNames.fileWrite[]' "${policy_path}")

  protected_path_property_names=()
  while IFS= read -r property_name || [[ -n "${property_name}" ]]; do
    protected_path_property_names+=("${property_name}")
  done < <(jq -r '.pathPropertyNames[]' "${policy_path}")

  active_rule_ids=()
  while IFS= read -r rule_id || [[ -n "${rule_id}" ]]; do
    active_rule_ids+=("${rule_id}")
  done < <(jq -r '.denyCommandRules[].id' "${policy_path}")

  pattern_rules=()
  while IFS= read -r rule_json || [[ -n "${rule_json}" ]]; do
    pattern_rules+=("${rule_json}")
  done < <(jq -cr '.denyCommandRules[] | select(.kind == "pattern") | {id, pattern, matchAgainst}' "${policy_path}")

  protected_path_rules=()
  while IFS= read -r rule_json || [[ -n "${rule_json}" ]]; do
    protected_path_rules+=("${rule_json}")
  done < <(jq -cr '.protectedPaths[] | {id, path, scope, action, maintenanceScope}' "${policy_path}")
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

tool_enabled() {
  local target="$1"
  shift
  local tool
  for tool in "$@"; do
    if [[ "${tool}" == "${target}" ]]; then
      return 0
    fi
  done
  return 1
}

trim_whitespace() {
  printf '%s' "$1" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

normalize_policy_path_text() {
  local value
  value="$(trim_whitespace "$1")"
  value="${value//\\//}"
  printf '%s\n' "${value}"
}

expand_home_path() {
  local value="$1"
  case "${value}" in
    '$HOME') printf '%s\n' "${HOME:-}"; return 0 ;;
    '$HOME/'*) printf '%s\n' "${HOME:-}/${value#'$HOME/'}"; return 0 ;;
    '${HOME}') printf '%s\n' "${HOME:-}"; return 0 ;;
    '${HOME}/'*) printf '%s\n' "${HOME:-}/${value#'${HOME}/'}"; return 0 ;;
    '$env:HOME') printf '%s\n' "${HOME:-}"; return 0 ;;
    '$env:HOME/'*) printf '%s\n' "${HOME:-}/${value#'$env:HOME/'}"; return 0 ;;
    "~") printf '%s\n' "${HOME:-}"; return 0 ;;
    "~/"*) printf '%s\n' "${HOME:-}/${value#'~/'}"; return 0 ;;
  esac
  printf '%s\n' "${value}"
}

is_absolute_path() {
  local value="$1"
  [[ "${value}" == /* || "${value}" == [A-Za-z]:/* || "${value}" == //* ]]
}

normalize_join_path() {
  local raw_path base_path path prefix rest joined result last_index
  local -a parts stack
  raw_path="$(trim_whitespace "$1")"
  base_path="$(trim_whitespace "${2:-}")"
  raw_path="${raw_path//\\//}"
  base_path="${base_path//\\//}"
  path="$(expand_home_path "${raw_path}")"
  path="${path//\\//}"
  if ! is_absolute_path "${path}" && [[ -n "${base_path}" ]]; then
    path="${base_path%/}/${path}"
  fi

  prefix=""
  rest="${path}"
  if [[ "${path}" == [A-Za-z]:/* ]]; then
    prefix="${path:0:2}"
    rest="${path:2}"
  elif [[ "${path}" == //* ]]; then
    prefix="//"
    rest="${path#//}"
  elif [[ "${path}" == /* ]]; then
    prefix="/"
    rest="${path#/}"
  fi

  if [[ "${prefix}" == [A-Za-z]: ]]; then
    rest="${rest#/}"
  fi

  IFS='/' read -r -a parts <<<"${rest}"
  stack=()
  for segment in "${parts[@]}"; do
    case "${segment}" in
      ""|.) continue ;;
      ..)
        if [[ "${#stack[@]}" -gt 0 ]]; then
          last_index=$((${#stack[@]} - 1))
          if [[ "${stack[${last_index}]}" != ".." ]]; then
            unset "stack[${last_index}]"
            continue
          fi
        fi
        if [[ -z "${prefix}" ]]; then
          stack+=("..")
        fi
        ;;
      *)
        stack+=("${segment}")
        ;;
    esac
  done

  joined="$(IFS=/; printf '%s' "${stack[*]}")"
  if [[ "${prefix}" == "/" ]]; then
    result="/${joined}"
  elif [[ "${prefix}" == "//" ]]; then
    result="//${joined}"
  elif [[ -n "${prefix}" ]]; then
    if [[ -n "${joined}" ]]; then
      result="${prefix}/${joined}"
    else
      result="${prefix}/"
    fi
  else
    result="${joined}"
  fi

  if [[ -z "${result}" ]]; then
    result="."
  fi

  printf '%s\n' "$(tr '[:upper:]' '[:lower:]' <<<"${result}")"
}

path_within_root() {
  local candidate root
  candidate="${1%/}"
  root="${2%/}"
  if [[ -z "${candidate}" || -z "${root}" ]]; then
    return 1
  fi
  [[ "${candidate}" == "${root}" || "${candidate}" == "${root}/"* ]]
}

iso_to_epoch() {
  local value="$1"
  local normalized
  if date -u -d "${value}" +%s >/dev/null 2>&1; then
    date -u -d "${value}" +%s
    return 0
  fi

  normalized="$(printf '%s' "${value}" \
    | sed -E 's/\.[0-9]+([+-][0-9]{2}:?[0-9]{2}|Z)$/\1/; s/Z$/+0000/; s/([+-][0-9]{2}):([0-9]{2})$/\1\2/')"
  date -u -j -f "%Y-%m-%dT%H:%M:%S%z" "${normalized}" +%s 2>/dev/null
}

maintenance_mode_active() {
  local scope="$1"
  local state_path created_at expires_at created_epoch expires_epoch now_epoch max_epoch

  if [[ -z "${scope}" || -z "${HOME:-}" ]]; then
    return 1
  fi

  state_path="${HOME}/.copilot/maintenance-mode.json"
  if [[ ! -f "${state_path}" ]]; then
    return 1
  fi

  if ! jq -e --arg scope "${scope}" '
    .schemaVersion == 1
    and .enabled == true
    and (.scopes | type == "array")
    and ((.scopes | index($scope)) != null)
    and (.createdAt | type == "string")
    and (.expiresAt | type == "string")
  ' "${state_path}" >/dev/null 2>&1; then
    return 1
  fi

  created_at="$(jq -r '.createdAt' "${state_path}")"
  expires_at="$(jq -r '.expiresAt' "${state_path}")"
  if ! created_epoch="$(iso_to_epoch "${created_at}")"; then
    return 1
  fi
  if ! expires_epoch="$(iso_to_epoch "${expires_at}")"; then
    return 1
  fi

  now_epoch="$(date -u +%s)"
  max_epoch=$((created_epoch + 7200))
  if (( created_epoch > now_epoch )); then
    return 1
  fi
  if (( expires_epoch <= created_epoch || expires_epoch > max_epoch || expires_epoch > now_epoch + 7200 )); then
    return 1
  fi

  (( expires_epoch > now_epoch ))
}

json_array_from_strings() {
  local first=1 encoded
  printf '['
  for value in "$@"; do
    encoded="$(jq -Rn --arg value "${value}" '$value')"
    if [[ "${first}" -eq 0 ]]; then
      printf ','
    fi
    printf '%s' "${encoded}"
    first=0
  done
  printf ']'
}

extract_path_values() {
  local property_names_json
  property_names_json="$(json_array_from_strings "${protected_path_property_names[@]}")"
  jq -r --argjson propertyNames "${property_names_json}" '
    def selected_args:
      if .toolArgs? != null then .toolArgs
      elif .tool_input? != null then .tool_input
      else empty end;
    def parsed_args:
      selected_args | if type == "string" then (fromjson? // .) else . end;
    def emit_strings($value):
      if $value == null then empty
      elif ($value | type) == "string" then $value
      elif ($value | type) == "array" then $value[] | emit_strings(.)
      elif ($value | type) == "object" then $value[] | emit_strings(.)
      else empty end;
    def collect_paths($value):
      if $value == null then empty
      elif ($value | type) == "array" then $value[] | collect_paths(.)
      elif ($value | type) == "object" then
        $value
        | to_entries[]
        | if ($propertyNames | index(.key)) != null
          then emit_strings(.value)
          else collect_paths(.value)
          end
      else empty end;
    parsed_args as $args
    | if ($args | type) == "object" or ($args | type) == "array"
      then collect_paths($args)
      else empty
      end
  ' <<<"${raw}" 2>/dev/null
}

protected_path_match_for_candidate() {
  local candidate="$1"
  local repo_root_path="$2"
  local current_dir="$3"
  local rule_json display scope action maintenance_scope base_path rule_path resolved_rule

  for rule_json in "${protected_path_rules[@]}"; do
    display="$(normalize_policy_path_text "$(jq -r '.path' <<<"${rule_json}")")"
    scope="$(jq -r '.scope' <<<"${rule_json}")"
    action="$(jq -r '.action' <<<"${rule_json}")"
    maintenance_scope="$(jq -r 'if .maintenanceScope == null then "" else .maintenanceScope end' <<<"${rule_json}")"

    if [[ "${display}" == '$HOME'* || "${display}" == '${HOME}'* || "${display}" == '$env:HOME'* || "${display}" == "~"* ]]; then
      base_path="${HOME:-}"
    elif [[ -n "${repo_root_path}" ]]; then
      base_path="${repo_root_path}"
    else
      base_path="${current_dir}"
    fi

    if [[ -z "${base_path}" ]]; then
      continue
    fi

    rule_path="${display}"
    if [[ "${scope}" == "directory" && "${rule_path}" == *"/**" ]]; then
      rule_path="${rule_path%/**}"
    fi
    resolved_rule="$(normalize_join_path "${rule_path}" "${base_path}")"

    if [[ "${scope}" == "directory" ]]; then
      if path_within_root "${candidate}" "${resolved_rule}"; then
        jq -nc \
          --arg display "${display}" \
          --arg action "${action}" \
          --arg maintenanceScope "${maintenance_scope}" \
          '{display:$display, action:$action, maintenanceScope:($maintenanceScope | if length == 0 then null else . end)}'
        return 0
      fi
      continue
    fi

    if [[ "${candidate}" == "${resolved_rule}" ]]; then
      jq -nc \
        --arg display "${display}" \
        --arg action "${action}" \
        --arg maintenanceScope "${maintenance_scope}" \
        '{display:$display, action:$action, maintenanceScope:($maintenanceScope | if length == 0 then null else . end)}'
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
is_shell_tool=0
is_file_write_tool=0
tool_enabled "${tool_name}" "${shell_tool_names[@]}" && is_shell_tool=1
tool_enabled "${tool_name}" "${file_write_tool_names[@]}" && is_file_write_tool=1
if [[ "${is_shell_tool}" -eq 0 && "${is_file_write_tool}" -eq 0 ]]; then
  exit 0
fi

repo_root_path="$(repo_root)"
current_dir="$(pwd -P)"
resolution_base="$(jq -r '(.cwd // empty) | strings' <<<"${raw}" 2>/dev/null || true)"
if [[ -z "${resolution_base}" ]]; then
  resolution_base="${current_dir}"
fi
resolution_base="$(normalize_join_path "${resolution_base}" "${current_dir}")"

if [[ "${is_file_write_tool}" -eq 1 ]]; then
  candidate_paths=()
  while IFS= read -r path_value || [[ -n "${path_value}" ]]; do
    trimmed_path="$(trim_whitespace "${path_value}")"
    if [[ -z "${trimmed_path}" ]]; then
      continue
    fi

    expanded_path="$(expand_home_path "${trimmed_path}")"
    if [[ -n "${repo_root_path}" ]] && ! is_absolute_path "${expanded_path}"; then
      candidate_paths+=("$(normalize_join_path "${trimmed_path}" "${repo_root_path}")")
    fi
    candidate_paths+=("$(normalize_join_path "${trimmed_path}" "${resolution_base}")")
  done < <(extract_path_values)

  protected_match=""
  for candidate_path in "${candidate_paths[@]}"; do
    match_json="$(protected_path_match_for_candidate "${candidate_path}" "${repo_root_path}" "${current_dir}" || true)"
    if [[ -n "${match_json}" ]]; then
      protected_match="${match_json}"
      break
    fi
  done

  if [[ -n "${protected_match}" ]]; then
    if [[ "${hook_event}" == "permissionRequest" ]]; then
      exit 0
    fi

    protected_display="$(jq -r '.display' <<<"${protected_match}")"
    protected_action="$(jq -r '.action' <<<"${protected_match}")"
    protected_maintenance_scope="$(jq -r 'if .maintenanceScope == null then "" else .maintenanceScope end' <<<"${protected_match}")"
    if [[ "${protected_action}" == "deny" ]]; then
      deny "Protected path change detected for ${protected_display} via ${tool_name}. Maintenance state changes must go through the maintenance scripts and are denied from Copilot tool edits."
      exit 0
    fi
    if [[ "${protected_display}" == '$HOME/.copilot/**' ]]; then
      ask "Protected path change detected for ${protected_display} via ${tool_name}. Home-managed Copilot files always require explicit human review, even during maintenance mode."
      exit 0
    fi

    if maintenance_mode_active "${protected_maintenance_scope}"; then
      exit 0
    fi

    ask "Protected path change detected for ${protected_display} via ${tool_name}. This path requires an atomic issue/PR and explicit human review."
    exit 0
  fi
fi

if [[ "${is_shell_tool}" -eq 0 ]]; then
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
