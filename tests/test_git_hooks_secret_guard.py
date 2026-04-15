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

snapshot_dir=""
config_path=""
redact_seen=0
exit_code_seen=0

if [ "$#" -lt 2 ]; then
  echo "expected: gitleaks dir <snapshot_dir> --config <config_path>" >&2
  exit 2
fi

if [ "$1" != "dir" ]; then
  echo "expected first argument to be 'dir', got: $1" >&2
  exit 2
fi
shift

snapshot_dir="$1"
if [ -z "$snapshot_dir" ]; then
  echo "missing snapshot directory after 'dir'" >&2
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

if [ -z "$config_path" ]; then
  echo "missing required --config argument" >&2
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

if [ -n "$allow_path" ] && [ -f "$snapshot_dir/$allow_path" ]; then
  if grep -R "SECRET_MARKER" "$snapshot_dir" >/dev/null 2>&1; then
    disallowed_hits=$(grep -R -l "SECRET_MARKER" "$snapshot_dir" | grep -F -v "$snapshot_dir/$allow_path" || true)
    if [ -z "$disallowed_hits" ]; then
      exit 0
    fi
  fi
fi

if grep -R "SECRET_MARKER" "$snapshot_dir" >/dev/null 2>&1; then
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


def test_pre_commit_skips_scan_when_config_is_missing_by_default(tmp_path: Path) -> None:
    repo, _env = _prepare_repo(tmp_path)
    (repo / ".gitleaks.toml").unlink()
    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "notes.txt")
    assert add.returncode == 0, add.stdout + add.stderr

    commit = _run_git(repo, "commit", "-m", "missing config skips scan")

    assert commit.returncode == 0, commit.stdout + commit.stderr


def test_pre_commit_fails_when_config_is_required_but_missing(tmp_path: Path) -> None:
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
        "missing config required",
        env={"SECRET_GUARD_REQUIRE_CONFIG": "1"},
    )

    assert commit.returncode != 0
    assert "Missing .gitleaks.toml in the repository root." in commit.stderr


def test_pre_commit_fails_when_gitleaks_is_missing(tmp_path: Path) -> None:
    repo, _env = _prepare_repo(tmp_path)
    tracked_file = repo / "notes.txt"
    tracked_file.write_text("safe\n", encoding="utf-8", newline="\n")

    add = _run_git(repo, "add", "notes.txt")
    assert add.returncode == 0, add.stdout + add.stderr

    missing_env = {"GITLEAKS_BIN": "missing-gitleaks"}
    commit = _run_git(repo, "commit", "-m", "missing gitleaks", env=missing_env)

    assert commit.returncode != 0
    assert "gitleaks is required for the pre-commit secret scan" in commit.stderr
