from __future__ import annotations

import io

import happy_env


def test_app_home_dry_run_uses_safe_non_interactive_defaults(monkeypatch) -> None:
    captured: dict[str, bool] = {}
    output = io.StringIO()

    def fake_run_home_sync(*, mirror: bool, dry_run: bool, verbose_log: bool) -> happy_env.CommandResult:
        captured.update({"mirror": mirror, "dry_run": dry_run, "verbose_log": verbose_log})
        return happy_env.CommandResult(
            label="home",
            command=("sync-to-home.ps1",),
            returncode=0,
            stdout="SYNC_STATS:ADDED=0,UPDATED=0,DELETED=0",
            stderr="",
        )

    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)
    monkeypatch.setattr(happy_env.sys, "stdout", output)

    exit_code = happy_env.main(["home", "--dry-run", "--no-interactive"])

    assert exit_code == 0
    assert captured == {"mirror": False, "dry_run": True, "verbose_log": False}
    assert "ドライラン確認" in output.getvalue()


def test_app_home_verbose_failure_shows_captured_script_output(monkeypatch) -> None:
    output = io.StringIO()

    def fake_run_home_sync(*, mirror: bool, dry_run: bool, verbose_log: bool) -> happy_env.CommandResult:
        return happy_env.CommandResult(
            label="home",
            command=("sync-to-home.ps1",),
            returncode=1,
            stdout="ConvertTo-NormalizedJsonValue: Cannot bind argument to parameter 'Value'",
            stderr="",
        )

    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)
    monkeypatch.setattr(happy_env.sys, "stdout", output)

    exit_code = happy_env.main(["home", "--dry-run", "--no-interactive", "--verbose-log"])

    assert exit_code == 1
    assert "同期失敗" in output.getvalue()
    assert "ConvertTo-NormalizedJsonValue" in output.getvalue()


def test_build_script_command_prefers_shell_script_on_linux(monkeypatch) -> None:
    monkeypatch.setattr(happy_env.os, "name", "posix", raising=False)
    monkeypatch.setattr(happy_env.shutil, "which", lambda name: "/usr/bin/bash" if name == "bash" else None)

    command = happy_env.build_script_command("sync-to-home", ("--DryRun",))

    assert command[0] == "/usr/bin/bash"
    assert command[1].endswith("scripts/sync-to-home.sh")
    assert command[2] == "--DryRun"
    assert command[3] == "--SourceRoot"
    assert command[4].endswith("happy_ai_life")


def test_build_script_command_normalizes_powershell_style_flags_for_shell(monkeypatch) -> None:
    monkeypatch.setattr(happy_env, "resolve_script_path", lambda _: happy_env.SCRIPTS_DIR / "sync-to-home.sh")
    monkeypatch.setattr(happy_env, "resolve_bash_executable", lambda: "/usr/bin/bash")

    command = happy_env.build_script_command("sync-to-home", ("-DryRun", "-VerboseLog"))

    assert command == (
        "/usr/bin/bash",
        str(happy_env.SCRIPTS_DIR / "sync-to-home.sh"),
        "--DryRun",
        "--VerboseLog",
        "--SourceRoot",
        str(happy_env.ROOT_DIR),
    )


def test_app_without_args_runs_live_home_sync_by_default(monkeypatch) -> None:
    captured: dict[str, bool] = {}
    output = io.StringIO()

    def fake_run_home_sync(*, mirror: bool, dry_run: bool, verbose_log: bool) -> happy_env.CommandResult:
        captured.update({"mirror": mirror, "dry_run": dry_run, "verbose_log": verbose_log})
        return happy_env.CommandResult(
            label="home",
            command=("sync-to-home.sh",),
            returncode=0,
            stdout="SYNC_STATS:ADDED=1,UPDATED=0,DELETED=0",
            stderr="",
        )

    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)
    monkeypatch.setattr(happy_env, "stdin_is_interactive", lambda stream=None: False)
    monkeypatch.setattr(happy_env.sys, "stdout", output)

    exit_code = happy_env.main([])

    assert exit_code == 0
    assert captured == {"mirror": False, "dry_run": False, "verbose_log": False}
    assert "同期完了" in output.getvalue()


def test_run_home_sync_omits_python_executable_for_shell_script(monkeypatch) -> None:
    monkeypatch.setattr(happy_env, "resolve_script_path", lambda _: happy_env.SCRIPTS_DIR / "sync-to-home.sh")
    monkeypatch.setattr(happy_env, "resolve_bash_executable", lambda: "/usr/bin/bash")

    def fake_run(command: tuple[str, ...], **_: object) -> object:
        assert "-PythonExecutable" not in command

        class Completed:
            returncode = 0
            stdout = b"SYNC_STATS:ADDED=0,UPDATED=0,DELETED=0"
            stderr = b""

        return Completed()

    monkeypatch.setattr(happy_env.subprocess, "run", fake_run)

    result = happy_env.run_home_sync()

    assert result.succeeded


def test_run_home_sync_normalizes_shell_flags(monkeypatch) -> None:
    monkeypatch.setattr(happy_env, "resolve_script_path", lambda _: happy_env.SCRIPTS_DIR / "sync-to-home.sh")
    monkeypatch.setattr(happy_env, "resolve_bash_executable", lambda: "/usr/bin/bash")

    def fake_run(command: tuple[str, ...], **_: object) -> object:
        assert "--DryRun" in command
        assert "--VerboseLog" in command
        assert "-DryRun" not in command
        assert "-VerboseLog" not in command

        class Completed:
            returncode = 0
            stdout = b"SYNC_STATS:ADDED=0,UPDATED=0,DELETED=0"
            stderr = b""

        return Completed()

    monkeypatch.setattr(happy_env.subprocess, "run", fake_run)

    result = happy_env.run_home_sync(dry_run=True, verbose_log=True)

    assert result.succeeded
