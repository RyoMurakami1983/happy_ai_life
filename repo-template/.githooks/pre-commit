#!/usr/bin/env sh

set -eu

protected_branch="${GIT_MAIN_GUARD_BRANCH:-main}"
current_branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)

changed_shared_docs=$(git diff --cached --name-only --diff-filter=MDRT -- docs/sessions 2>/dev/null || true)
if [ -n "$changed_shared_docs" ]; then
  printf '%s\n' "Shared session docs are append-only. Do not modify, delete, or rename existing files under docs/sessions/**." >&2
  printf '%s\n' "$changed_shared_docs" >&2
  exit 1
fi

if [ -n "$current_branch" ] && [ "$current_branch" = "$protected_branch" ]; then
  printf '%s\n%s\n' "Direct commits on '$protected_branch' are blocked by the repository hook." "Create a feature branch and commit there instead." >&2
  exit 1
fi

exit 0
