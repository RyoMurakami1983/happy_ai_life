#!/usr/bin/env bash
set -euo pipefail

raw="$(cat || true)"
if [[ -z "${raw}" ]]; then
  exit 0
fi

# toolName を取得（例: "bash"）
tool_name="$(jq -r '.toolName // empty' <<<"${raw}")"
if [[ "${tool_name}" != "bash" ]]; then
  exit 0
fi

# toolArgs は JSON 文字列として渡ってくる想定なので fromjson で展開
command="$(jq -r '.toolArgs // empty | fromjson? | .command // empty' <<<"${raw}")"
if [[ -z "${command}" ]]; then
  exit 0
fi

normalized="$(tr '[:upper:]' '[:lower:]' <<<"${command}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

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
  'git push --force'
  'git reset --hard'
)

for p in "${deny_patterns[@]}"; do
  if grep -F -q -- "${p}" <<<"${normalized}"; then
    # deny を返す（JSON）
    jq -nc --arg cmd "${command}" \
      '{permissionDecision:"deny", permissionDecisionReason:("Blocked potentially destructive command: " + $cmd)}'
    exit 0
  fi
done

# allow: 何も返さない
exit 0