from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HOOKS_SOURCE = ROOT / "repo-template" / ".githooks"
GIT = shutil.which("git")

pytestmark = pytest.mark.skipif(GIT is None, reason="git is required for hook tests")


def _git_executable() -> str:
    assert GIT is not None
    return GIT


def _run_git(
    repo: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    if env is not None:
        command_env.update(env)

    return subprocess.run(
        [_git_executable(), *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=command_env,
    )


def _write_executable(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path


def _create_gitleaks_shim(path: Path) -> Path:
    return _write_executable(
        path,
        """#!/usr/bin/env sh
set -eu

scan_mode=""
scan_target=""
config_path=""
redact_seen=0
exit_code_seen=0
log_opts=""

if [ "$#" -lt 2 ]; then
  echo "expected: gitleaks dir <snapshot_dir> or gitleaks git <repo_root>" >&2
  exit 2
fi

if [ "$1" != "dir" ] && [ "$1" != "git" ]; then
  echo "expected first argument to be 'dir' or 'git', got: $1" >&2
  exit 2
fi
scan_mode="$1"
shift

scan_target="$1"
if [ -z "$scan_target" ]; then
  echo "missing scan target after '$scan_mode'" >&2
  exit 2
fi
shift

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config)
      if [ -n "$config_path" ]; then
        echo "duplicate --config argument" >&2
        exit 2
      fi
      shift
      if [ "$#" -eq 0 ]; then
        echo "missing value for --config" >&2
        exit 2
      fi
      config_path="$1"
      ;;
    --log-opts)
      shift
      if [ "$#" -eq 0 ]; then
        echo "missing value for --log-opts" >&2
        exit 2
      fi
      log_opts="$1"
      ;;
    --no-banner)
      ;;
    --redact=100)
      redact_seen=1
      ;;
    --exit-code)
      exit_code_seen=1
      shift
      if [ "$#" -eq 0 ] || [ "$1" != "1" ]; then
        echo "expected --exit-code 1" >&2
        exit 2
      fi
      ;;
    *)
      echo "unexpected gitleaks argument: $1" >&2
      exit 2
      ;;
  esac
  shift
done

if [ "$scan_mode" = "git" ] && [ -z "$log_opts" ]; then
  echo "missing required --log-opts argument for git scan" >&2
  exit 2
fi

if [ "$redact_seen" -ne 1 ] || [ "$exit_code_seen" -ne 1 ]; then
  echo "missing expected gitleaks flags" >&2
  exit 2
fi

allow_path=""
if [ -n "$config_path" ] && [ -f "$config_path" ]; then
  allow_path=$(sed -n 's/^# TEST_ALLOW_PATH=//p' "$config_path")
fi

if [ "$scan_mode" = "git" ]; then
  commits=$(git -C "$scan_target" rev-list $log_opts 2>/dev/null || true)
  for commit in $commits; do
    if git -C "$scan_target" grep -I "SECRET_MARKER" "$commit" -- >/dev/null 2>&1; then
      printf '%s\\n' 'Finding: redacted-secret'
      exit 1
    fi
  done
  exit 0
fi

if [ -n "$allow_path" ] && [ -f "$scan_target/$allow_path" ]; then
  if grep -R "SECRET_MARKER" "$scan_target" >/dev/null 2>&1; then
    disallowed_hits=$(grep -R -l "SECRET_MARKER" "$scan_target" | grep -F -v "$scan_target/$allow_path" || true)
    if [ -z "$disallowed_hits" ]; then
      exit 0
    fi
  fi
fi

if grep -R "SECRET_MARKER" "$scan_target" >/dev/null 2>&1; then
  printf '%s\\n' 'Finding: redacted-secret'
  exit 1
fi

exit 0
""",
    )


def _prepare_repo(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    repo = tmp_path / "repo"
    repo.mkdir()

    init = _run_git(repo, "init")
    assert init.returncode == 0, init.stdout + init.stderr

    checkout = _run_git(repo, "checkout", "-b", "feature/test-hooks")
    assert checkout.returncode == 0, checkout.stdout + checkout.stderr

    config_name = _run_git(repo, "config", "user.name", "Test User")
    assert config_name.returncode == 0, config_name.stdout + config_name.stderr

    config_email = _run_git(repo, "config", "user.email", "test@example.com")
    assert config_email.returncode == 0, config_email.stdout + config_email.stderr

    hooks_dir = repo / ".githooks"
    shutil.copytree(HOOKS_SOURCE, hooks_dir)
    for path in hooks_dir.rglob("*"):
        if path.is_file():
            path.chmod(0o755)

    config_hooks_path = _run_git(repo, "config", "core.hooksPath", ".githooks")
    assert config_hooks_path.returncode == 0, config_hooks_path.stdout + config_hooks_path.stderr

    (repo / ".gitleaks.toml").write_text(
        'title = "test-gitleaks-config"\n',
        encoding="utf-8",
        newline="\n",
    )

    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    _create_gitleaks_shim(shim_dir / "gitleaks-shim")
    env = {
        "GITLEAKS_BIN": "gitleaks-shim",
        "PATH": f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    return repo, env


def test_pre_commit_allows_clean_staged_changes(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "notes.txt", env=env)
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(repo, "commit", "-m", "safe commit", env=env)

    assert commit.returncode == 0, commit.stdout + commit.stderr


def test_pre_commit_handles_repo_path_with_spaces(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo parent with spaces"
    repo_root.mkdir()
    repo, env = _prepare_repo(repo_root)
    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "notes.txt", env=env)
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(repo, "commit", "-m", "safe commit in spaced path", env=env)

    assert commit.returncode == 0, commit.stdout + commit.stderr


def test_pre_commit_blocks_secret_like_staged_changes(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    tracked_file = repo / "secrets.env"
    tracked_file.write_text("API_KEY=SECRET_MARKER\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "secrets.env", env=env)
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(repo, "commit", "-m", "blocked commit", env=env)

    assert commit.returncode != 0
    assert "Potential secrets were detected in staged changes." in commit.stderr
    assert "Finding: redacted-secret" in commit.stderr


def test_pre_commit_respects_allowlisted_paths_via_gitleaks_config(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    (repo / ".gitleaks.toml").write_text(
        'title = "test-gitleaks-config"\n# TEST_ALLOW_PATH=docs/example.env\n',
        encoding="utf-8",
        newline="\n",
    )

    allowed_file = repo / "docs" / "example.env"
    allowed_file.parent.mkdir(parents=True)
    allowed_file.write_text("API_KEY=SECRET_MARKER\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "docs/example.env", env=env)
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(repo, "commit", "-m", "allowlisted placeholder", env=env)

    assert commit.returncode == 0, commit.stdout + commit.stderr


def test_pre_commit_scans_staged_content_not_working_tree(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    tracked_file = repo / "partial.txt"
    tracked_file.write_text("SAFE_VALUE\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "partial.txt", env=env)
    assert add.returncode == 0, add.stdout + add.stderr

    tracked_file.write_text("SAFE_VALUE\nAPI_KEY=SECRET_MARKER\n", encoding="utf-8", newline="\n")

    commit = _run_git(repo, "commit", "-m", "staged content only", env=env)

    assert commit.returncode == 0, commit.stdout + commit.stderr


def test_pre_commit_handles_non_ascii_staged_paths(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    tracked_file = repo / "docs" / "ふりかえり.txt"
    tracked_file.parent.mkdir(parents=True)
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "docs/ふりかえり.txt", env=env)
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(repo, "commit", "-m", "non ascii path", env=env)

    assert commit.returncode == 0, commit.stdout + commit.stderr


def test_pre_commit_uses_default_gitleaks_rules_when_config_is_missing(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    (repo / ".gitleaks.toml").unlink()
    tracked_file = repo / "secrets.env"
    tracked_file.write_text("API_KEY=SECRET_MARKER\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "secrets.env", env=env)
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(repo, "commit", "-m", "missing config still scans", env=env)

    assert commit.returncode != 0
    assert "Potential secrets were detected in staged changes." in commit.stderr
    assert "Finding: redacted-secret" in commit.stderr


def test_pre_commit_fails_when_gitleaks_is_missing_even_without_config(tmp_path: Path) -> None:
    repo, _env = _prepare_repo(tmp_path)
    (repo / ".gitleaks.toml").unlink()
    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "notes.txt")
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(
        repo,
        "commit",
        "-m",
        "missing gitleaks without config",
        env={"GITLEAKS_BIN": "missing-gitleaks"},
    )

    assert commit.returncode != 0
    assert "gitleaks is required for the Git secret scan" in commit.stderr


def test_pre_commit_fails_when_gitleaks_is_missing(tmp_path: Path) -> None:
    repo, _env = _prepare_repo(tmp_path)
    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "notes.txt")
    assert add.returncode == 0, add.stdout + add.stderr

    missing_env = {"GITLEAKS_BIN": "missing-gitleaks"}
    commit = _run_git(repo, "commit", "-m", "missing gitleaks", env=missing_env)

    assert commit.returncode != 0
    assert "gitleaks is required for the Git secret scan" in commit.stderr


def test_pre_push_blocks_secret_like_commits(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    remote = tmp_path / "remote.git"
    init_remote = subprocess.run(
        [_git_executable(), "init", "--bare", str(remote)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert init_remote.returncode == 0, init_remote.stdout + init_remote.stderr
    add_remote = _run_git(repo, "remote", "add", "origin", str(remote), env=env)
    assert add_remote.returncode == 0, add_remote.stdout + add_remote.stderr

    tracked_file = repo / "secrets.env"
    tracked_file.write_text("API_KEY=SECRET_MARKER\n", encoding="utf-8", newline="\n")
    add = _run_git(repo, "add", "secrets.env", env=env)
    assert add.returncode == 0, add.stdout + add.stderr
    commit = _run_git(repo, "commit", "--no-verify", "-m", "secret commit for push", env=env)
    assert commit.returncode == 0, commit.stdout + commit.stderr

    push = _run_git(repo, "push", "origin", "HEAD:refs/heads/feature/test-hooks", env=env)

    assert push.returncode != 0
    assert "Potential secrets were detected in commits being pushed." in push.stderr
    assert "Finding: redacted-secret" in push.stderr


def test_pre_push_allows_clean_commits(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    remote = tmp_path / "remote.git"
    init_remote = subprocess.run(
        [_git_executable(), "init", "--bare", str(remote)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert init_remote.returncode == 0, init_remote.stdout + init_remote.stderr
    add_remote = _run_git(repo, "remote", "add", "origin", str(remote), env=env)
    assert add_remote.returncode == 0, add_remote.stdout + add_remote.stderr

    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")
    add = _run_git(repo, "add", "notes.txt", env=env)
    assert add.returncode == 0, add.stdout + add.stderr
    commit = _run_git(repo, "commit", "-m", "safe push", env=env)
    assert commit.returncode == 0, commit.stdout + commit.stderr

    push = _run_git(repo, "push", "origin", "HEAD:refs/heads/feature/test-hooks", env=env)

    assert push.returncode == 0, push.stdout + push.stderr


def test_pre_push_skips_branch_deletions_without_scanning(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    remote = tmp_path / "remote.git"
    init_remote = subprocess.run(
        [_git_executable(), "init", "--bare", str(remote)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert init_remote.returncode == 0, init_remote.stdout + init_remote.stderr
    add_remote = _run_git(repo, "remote", "add", "origin", str(remote), env=env)
    assert add_remote.returncode == 0, add_remote.stdout + add_remote.stderr

    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")
    add = _run_git(repo, "add", "notes.txt", env=env)
    assert add.returncode == 0, add.stdout + add.stderr
    commit = _run_git(repo, "commit", "-m", "safe push before delete", env=env)
    assert commit.returncode == 0, commit.stdout + commit.stderr
    push = _run_git(repo, "push", "origin", "HEAD:refs/heads/feature/delete-me", env=env)
    assert push.returncode == 0, push.stdout + push.stderr

    delete_env = {**env, "GITLEAKS_BIN": "missing-gitleaks"}
    delete = _run_git(repo, "push", "origin", ":refs/heads/feature/delete-me", env=delete_env)

    assert delete.returncode == 0, delete.stdout + delete.stderr


def test_pre_push_skips_new_branch_names_with_no_new_commits(tmp_path: Path) -> None:
    repo, env = _prepare_repo(tmp_path)
    remote = tmp_path / "remote.git"
    init_remote = subprocess.run(
        [_git_executable(), "init", "--bare", str(remote)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert init_remote.returncode == 0, init_remote.stdout + init_remote.stderr
    add_remote = _run_git(repo, "remote", "add", "origin", str(remote), env=env)
    assert add_remote.returncode == 0, add_remote.stdout + add_remote.stderr

    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")
    add = _run_git(repo, "add", "notes.txt", env=env)
    assert add.returncode == 0, add.stdout + add.stderr
    commit = _run_git(repo, "commit", "-m", "safe pushed commit", env=env)
    assert commit.returncode == 0, commit.stdout + commit.stderr
    first_push = _run_git(repo, "push", "origin", "HEAD:refs/heads/feature/already-known", env=env)
    assert first_push.returncode == 0, first_push.stdout + first_push.stderr
    fetch = _run_git(repo, "fetch", "origin", env=env)
    assert fetch.returncode == 0, fetch.stdout + fetch.stderr

    missing_gitleaks_env = {**env, "GITLEAKS_BIN": "missing-gitleaks"}
    second_push = _run_git(
        repo,
        "push",
        "origin",
        "HEAD:refs/heads/feature/new-name-same-commit",
        env=missing_gitleaks_env,
    )

    assert second_push.returncode == 0, second_push.stdout + second_push.stderr
