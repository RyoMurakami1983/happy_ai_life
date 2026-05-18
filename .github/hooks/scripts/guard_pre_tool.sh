#!/usr/bin/env bash
set -euo pipefail

hook_event="${HAPPY_AI_LIFE_HOOK_EVENT:-preToolUse}"
if [[ "${hook_event}" != "preToolUse" && "${hook_event}" != "permissionRequest" ]]; then
  hook_event="preToolUse"
fi

raw="$(cat || true)"
if [[ -z "${raw//[[:space:]]/}" ]]; then
  exit 0
fi

json_escape() {
  local value="${1:-}"
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '%s' "${value}"
}

write_failure_log() {
  local message="$1"
  if [[ -z "${HOME:-}" ]]; then
    return
  fi
  mkdir -p "${HOME}/.copilot" 2>/dev/null || return
  printf '%s %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "${message}" >> "${HOME}/.copilot/guard-failures.log" 2>/dev/null || true
}

create_temp_file() {
  local temp_path
  if ! temp_path="$(mktemp "${TMPDIR:-/tmp}/happy-ai-life-guard.XXXXXX")"; then
    return 1
  fi
  [[ -n "${temp_path}" ]] || return 1
  printf '%s\n' "${temp_path}"
}

deny() {
  local reason="$1"
  local escaped
  escaped="$(json_escape "${reason}")"
  write_failure_log "${reason}"
  if [[ "${hook_event}" == "permissionRequest" ]]; then
    printf '{"behavior":"deny","message":"%s","interrupt":true}' "${escaped}"
    return
  fi

  printf '{"permissionDecision":"deny","permissionDecisionReason":"%s"}' "${escaped}"
}

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hooks_dir="$(dirname -- "${script_dir}")"
layout_root="$(dirname -- "${hooks_dir}")"
repo_root=""
if [[ "$(basename -- "${layout_root}")" == ".github" ]]; then
  repo_root="$(dirname -- "${layout_root}")"
fi

resolve_engine_path() {
  local candidate
  case "$(basename -- "${layout_root}")" in
    .copilot)
      candidate="${layout_root}/scripts/guard_policy.py"
      ;;
    .github)
      candidate="${repo_root}/scripts/guard_policy.py"
      ;;
    *)
      return 1
      ;;
  esac

  [[ -f "${candidate}" ]] || return 1
  printf '%s\n' "${candidate}"
}

resolve_policy_path() {
  local candidate
  case "$(basename -- "${layout_root}")" in
    .copilot)
      candidate="${layout_root}/policy/guard-policy.json"
      ;;
    .github)
      candidate="${repo_root}/policy/guard-policy.json"
      ;;
    *)
      return 1
      ;;
  esac

  [[ -f "${candidate}" ]] || return 1
  printf '%s\n' "${candidate}"
}

is_windows_apps_path() {
  local candidate="${1:-}"
  [[ "${candidate}" == *[Ww][Ii][Nn][Dd][Oo][Ww][Ss][Aa][Pp][Pp][Ss]* ]]
}

test_python_candidate() {
  local executable="$1"
  shift || true
  [[ -n "${executable}" ]] || return 1
  is_windows_apps_path "${executable}" && return 1
  [[ -f "${executable}" ]] || return 1
  "${executable}" "$@" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 2)' >/dev/null 2>&1
}

resolve_python_override() {
  local override="$1"
  local candidate_path override_basename
  [[ -n "${override}" ]] || return 1

  case "${override}" in
    */*|*\\*)
      if test_python_candidate "${override}"; then
        python_command=("${override}")
        return 0
      fi
      return 1
      ;;
  esac

  if ! command -v "${override}" >/dev/null 2>&1; then
    return 1
  fi
  candidate_path="$(command -v "${override}")"
  override_basename="$(basename -- "${override}")"
  case "${override_basename}" in
    [Pp][Yy]|[Pp][Yy].[Ee][Xx][Ee])
      if test_python_candidate "${candidate_path}" -3.10; then
        python_command=("${candidate_path}" "-3.10")
        return 0
      fi
      if test_python_candidate "${candidate_path}" -3; then
        python_command=("${candidate_path}" "-3")
        return 0
      fi
      ;;
    *)
      if test_python_candidate "${candidate_path}"; then
        python_command=("${candidate_path}")
        return 0
      fi
      ;;
  esac

  return 1
}

declare -a python_command=()

resolve_python_command() {
  local override candidate_path py_path
  override="${HAPPY_AI_LIFE_PYTHON:-}"
  if [[ -n "${override}" ]] && resolve_python_override "${override}"; then
    return 0
  fi

  local -a candidate_paths=()
  if [[ -n "${repo_root}" ]]; then
    candidate_paths+=("${repo_root}/.venv/Scripts/python.exe" "${repo_root}/.venv/bin/python" "${repo_root}/.venv/bin/python3")
  fi
  if [[ "$(basename -- "${layout_root}")" == ".copilot" ]]; then
    candidate_paths+=("${layout_root}/.venv/Scripts/python.exe" "${layout_root}/.venv/bin/python" "${layout_root}/.venv/bin/python3")
  fi

  for candidate_path in "${candidate_paths[@]}"; do
    if test_python_candidate "${candidate_path}"; then
      python_command=("${candidate_path}")
      return 0
    fi
  done

  for candidate_name in python python3; do
    if ! command -v "${candidate_name}" >/dev/null 2>&1; then
      continue
    fi
    candidate_path="$(command -v "${candidate_name}")"
    if test_python_candidate "${candidate_path}"; then
      python_command=("${candidate_path}")
      return 0
    fi
  done

  if command -v py >/dev/null 2>&1; then
    py_path="$(command -v py)"
    if test_python_candidate "${py_path}" -3.10; then
      python_command=("${py_path}" "-3.10")
      return 0
    fi
    if test_python_candidate "${py_path}" -3; then
      python_command=("${py_path}" "-3")
      return 0
    fi
  fi

  return 1
}

is_timeout_status() {
  local status="$1"
  case "${status}" in
    124|137|143)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_engine_with_timeout() {
  local stdout_file="$1"
  shift

  if command -v timeout >/dev/null 2>&1; then
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 timeout 15s "$@" <<<"${raw}" >"${stdout_file}" 2>"${stderr_file}"
    return $?
  fi

  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "$@" <<<"${raw}" >"${stdout_file}" 2>"${stderr_file}" &
  local engine_pid=$!
  local remaining_ticks=150

  while kill -0 "${engine_pid}" 2>/dev/null; do
    if (( remaining_ticks <= 0 )); then
      kill "${engine_pid}" 2>/dev/null || true
      sleep 0.5
      if kill -0 "${engine_pid}" 2>/dev/null; then
        kill -9 "${engine_pid}" 2>/dev/null || true
      fi
      wait "${engine_pid}" 2>/dev/null || true
      return 124
    fi

    sleep 0.1
    remaining_ticks=$((remaining_ticks - 1))
  done

  wait "${engine_pid}"
}

engine_path="$(resolve_engine_path || true)"
if [[ -z "${engine_path}" ]]; then
  deny "Failed to locate the shared guard policy engine (scripts/guard_policy.py). Restore the synchronized guard runtime or sync again."
  exit 0
fi

if ! resolve_python_command; then
  deny "Python 3.10+ is required to run the shared guard policy engine (scripts/guard_policy.py). Install Python 3.10+ or set HAPPY_AI_LIFE_PYTHON to a valid interpreter."
  exit 0
fi

policy_path="$(resolve_policy_path || true)"
if ! stderr_file="$(create_temp_file)"; then
  deny "Failed to create a temporary file while running the shared guard policy engine. Restore the synchronized guard runtime or sync again."
  exit 0
fi
if ! stdout_file="$(create_temp_file)"; then
  rm -f "${stderr_file}"
  deny "Failed to create a temporary file while running the shared guard policy engine. Restore the synchronized guard runtime or sync again."
  exit 0
fi
trap 'rm -f "${stderr_file}" "${stdout_file}"' EXIT

declare -a engine_args=("${python_command[@]}" -X utf8 "${engine_path}" --hook-event "${hook_event}" --cwd "$(pwd -P)")
if [[ -n "${HOME:-}" ]]; then
  engine_args+=(--home "${HOME}")
fi
if [[ -n "${repo_root}" ]]; then
  engine_args+=(--repo-root "${repo_root}")
fi
if [[ -n "${policy_path}" ]]; then
  engine_args+=(--policy-path "${policy_path}")
fi

if run_engine_with_timeout "${stdout_file}" "${engine_args[@]}"; then
  engine_status=0
else
  engine_status=$?
fi
if [[ ${engine_status} -ne 0 ]]; then
  if is_timeout_status "${engine_status}"; then
    deny "Timed out while running the shared guard policy engine (scripts/guard_policy.py). Install Python 3.10+ or set HAPPY_AI_LIFE_PYTHON to a valid interpreter."
    exit 0
  fi

  stderr_text="$(<"${stderr_file}")"
  if [[ -n "${stderr_text}" ]]; then
    stderr_text="${stderr_text:0:500}"
    deny "Failed to run the shared guard policy engine (scripts/guard_policy.py). Install Python 3.10+ or set HAPPY_AI_LIFE_PYTHON to a valid interpreter. stderr: ${stderr_text}"
  else
    deny "Failed to run the shared guard policy engine (scripts/guard_policy.py). Install Python 3.10+ or set HAPPY_AI_LIFE_PYTHON to a valid interpreter."
  fi
  exit 0
fi
output="$(<"${stdout_file}")"

if [[ -z "${output//[[:space:]]/}" ]]; then
  exit 0
fi

if ! printf '%s' "${output}" | PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "${python_command[@]}" -c 'import json, sys; json.load(sys.stdin)' >/dev/null 2>&1; then
  deny "The shared guard policy engine returned invalid JSON. Restore the synchronized guard runtime or sync again."
  exit 0
fi

printf '%s' "${output}"
