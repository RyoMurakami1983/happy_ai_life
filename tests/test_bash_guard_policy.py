from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import pytest

from _guard_helpers import ensure_guard_engine_for_script


ROOT = Path(__file__).resolve().parents[1]
GUARD_SCRIPT_PATH = ROOT / ".github" / "hooks" / "scripts" / "guard_pre_tool.sh"
GUARD_POLICY_PATH = ROOT / "policy" / "guard-policy.json"


@lru_cache(maxsize=1)
def _bash_executable() -> str:
    candidates = [
        shutil.which("bash"),
        str(Path(r"C:\Program Files\Git\bin\bash.exe")),
        str(Path(r"C:\Program Files\Git\usr\bin\bash.exe")),
        str(Path(r"C:\Program Files (x86)\Git\bin\bash.exe")),
        str(Path(r"C:\Program Files (x86)\Git\usr\bin\bash.exe")),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if "WindowsApps" in candidate:
            continue
        if not Path(candidate).exists():
            continue
        try:
            probe = subprocess.run(
                [candidate, "-lc", "exit 0"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            continue
        if probe.returncode == 0:
            return candidate

    pytest.skip("bash executable not found")


def _invoke_bash_guard_pre_tool(
    payload: dict[str, object],
    cwd: Path,
    *,
    stringify_tool_args: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    bash_payload: dict[str, object] = dict(payload)
    tool_args = bash_payload.get("toolArgs")
    if stringify_tool_args and tool_args is not None and not isinstance(tool_args, str):
        bash_payload["toolArgs"] = json.dumps(tool_args)

    effective_env = None
    if env is not None:
        effective_env = {**os.environ, **env}
    else:
        effective_env = dict(os.environ)
    effective_env.setdefault("HAPPY_AI_LIFE_PYTHON", sys.executable)

    bash_path = _bash_executable()
    ensure_guard_engine_for_script(cwd / ".github" / "hooks" / "scripts" / "guard_pre_tool.sh")
    return subprocess.run(
        [bash_path, "-lc", 'exec "$0" .github/hooks/scripts/guard_pre_tool.sh', bash_path],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        input=json.dumps(bash_payload),
        env=effective_env,
    )


def _init_repo_with_bash_guard(repo: Path) -> None:
    repo.mkdir()

    hooks_dir = repo / ".github" / "hooks" / "scripts"
    hooks_dir.mkdir(parents=True)
    shutil.copy2(GUARD_SCRIPT_PATH, hooks_dir / "guard_pre_tool.sh")
    ensure_guard_engine_for_script(hooks_dir / "guard_pre_tool.sh")


def _write_policy(repo: Path, policy: dict[str, object]) -> None:
    policy_dir = repo / "policy"
    policy_dir.mkdir(exist_ok=True)
    (policy_dir / "guard-policy.json").write_text(json.dumps(policy), encoding="utf-8")


def _write_maintenance_state(home_root: Path) -> Path:
    state_path = home_root / ".copilot" / "maintenance-mode.json"
    state_path.parent.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    state_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "enabled": True,
                "createdAt": now.isoformat(),
                "expiresAt": (now + timedelta(minutes=30)).isoformat(),
                "scopes": ["protectedPathEdit"],
            }
        ),
        encoding="utf-8",
    )
    return state_path


def test_bash_guard_script_avoids_mapfile_for_bash32_compatibility() -> None:
    content = GUARD_SCRIPT_PATH.read_text(encoding="utf-8")

    assert "mapfile" not in content


def test_bash_guard_script_avoids_bash4_lowercase_expansion_for_bash32_compatibility() -> None:
    content = GUARD_SCRIPT_PATH.read_text(encoding="utf-8")

    assert ",," not in content


def test_bash_guard_script_uses_portable_mktemp_template() -> None:
    content = GUARD_SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'mktemp "${TMPDIR:-/tmp}/happy-ai-life-guard.XXXXXX"' in content


def test_bash_guard_script_treats_common_timeout_exit_codes_as_timeout() -> None:
    content = GUARD_SCRIPT_PATH.read_text(encoding="utf-8")

    assert "is_timeout_status" in content
    assert "124|137|143" in content


def test_bash_guard_script_accepts_py_exe_override_as_launcher() -> None:
    content = GUARD_SCRIPT_PATH.read_text(encoding="utf-8")

    assert "[Pp][Yy].[Ee][Xx][Ee]" in content
    assert 'test_python_candidate "${candidate_path}" -3.10' in content


def test_bash_guard_pre_tool_uses_policy_shell_tool_names_cross_platform(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    policy["toolNames"]["shell"] = ["terminal"]
    _write_policy(repo, policy)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "terminal", "toolArgs": {"command": "git reset --hard HEAD"}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Blocked potentially destructive command" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_asks_for_home_managed_path_during_active_maintenance_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home_root = tmp_path / "home"
    _init_repo_with_bash_guard(repo)
    _write_maintenance_state(home_root)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(home_root / ".copilot" / "copilot-instructions.md"),
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
        env={"HOME": str(home_root)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "ask"
    assert "Home-managed Copilot files always require explicit human review" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_denies_when_python_runtime_is_unavailable(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "git status"}},
        cwd=repo,
        env={
            "HAPPY_AI_LIFE_PYTHON": str(repo / "missing-python"),
            "PATH": "",
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Python 3.10+" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_accepts_python_override_command_name(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)
    python_path = Path(sys.executable)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "git status"}},
        cwd=repo,
        env={
            "HAPPY_AI_LIFE_PYTHON": python_path.name,
            "PATH": f"{python_path.parent}{os.pathsep}{os.environ.get('PATH', '')}",
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def test_bash_guard_pre_tool_denies_when_mktemp_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)
    script = repo / ".github" / "hooks" / "scripts" / "guard_pre_tool.sh"
    script.write_text(
        script.read_text(encoding="utf-8").replace(
            """create_temp_file() {
  local temp_path
  if ! temp_path="$(mktemp "${TMPDIR:-/tmp}/happy-ai-life-guard.XXXXXX")"; then
    return 1
  fi
  [[ -n "${temp_path}" ]] || return 1
  printf '%s\\n' "${temp_path}"
}
""",
            """create_temp_file() {
  return 1
}
""",
        ),
        encoding="utf-8",
    )

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "git status"}},
        cwd=repo,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "temporary file" in response["permissionDecisionReason"]


def test_bash_guard_pre_tool_denies_when_engine_times_out(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_bash_guard(repo)
    script = repo / ".github" / "hooks" / "scripts" / "guard_pre_tool.sh"
    script.write_text(
        script.read_text(encoding="utf-8")
        .replace("if command -v timeout >/dev/null 2>&1; then", "if false; then")
        .replace("local remaining_ticks=150", "local remaining_ticks=2")
        .replace("sleep 0.1", "sleep 0.01"),
        encoding="utf-8",
    )

    shim = tmp_path / "slow-python.sh"
    shim.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            for arg in "$@"; do
              if [[ "$arg" == "-c" ]]; then
                exit 0
              fi
            done
            sleep 20
            """
        ),
        encoding="utf-8",
    )
    shim.chmod(0o755)

    result = _invoke_bash_guard_pre_tool(
        {"toolName": "powershell", "toolArgs": {"command": "git status"}},
        cwd=repo,
        env={"HAPPY_AI_LIFE_PYTHON": shim.as_posix()},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["permissionDecision"] == "deny"
    assert "Timed out while running the shared guard policy engine" in response["permissionDecisionReason"]


def test_bash_guard_permission_request_denies_maintenance_state_edit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home_root = tmp_path / "home"
    _init_repo_with_bash_guard(repo)
    state_path = _write_maintenance_state(home_root)

    result = _invoke_bash_guard_pre_tool(
        {
            "toolName": "edit",
            "toolArgs": {
                "path": str(state_path),
                "oldString": "old",
                "newString": "new",
            },
        },
        cwd=repo,
        env={"HOME": str(home_root), "HAPPY_AI_LIFE_HOOK_EVENT": "permissionRequest"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["behavior"] == "deny"
    assert response["interrupt"] is True
    assert "Maintenance state changes must go through the maintenance scripts" in response["message"]
