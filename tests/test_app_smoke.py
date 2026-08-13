from __future__ import annotations

import io
from pathlib import Path

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
    assert command[1].replace("\\", "/").endswith("scripts/sync-to-home.sh")
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

    def fake_run(command: tuple[str, ...], **kwargs: object) -> object:
        assert "-PythonExecutable" not in command
        assert kwargs["stdin"] is happy_env.subprocess.DEVNULL

        class Completed:
            returncode = 0
            stdout = b"SYNC_STATS:ADDED=0,UPDATED=0,DELETED=0"
            stderr = b""

        return Completed()

    monkeypatch.setattr(happy_env.subprocess, "run", fake_run)

    result = happy_env.run_home_sync()

    assert result.succeeded


def test_run_home_sync_closes_child_stdin(monkeypatch) -> None:
    monkeypatch.setattr(happy_env, "resolve_script_path", lambda _: happy_env.SCRIPTS_DIR / "sync-to-home.ps1")
    monkeypatch.setattr(happy_env, "resolve_powershell_executable", lambda: "powershell")

    def fake_run(command: tuple[str, ...], **kwargs: object) -> object:
        assert kwargs["stdin"] is happy_env.subprocess.DEVNULL

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


def test_app_plugin_repair_dry_run_shows_default_targets(monkeypatch) -> None:
    output = io.StringIO()

    monkeypatch.setattr(happy_env, "resolve_user_home", lambda: Path(r"C:\Users\tester"))
    monkeypatch.setattr(happy_env.sys, "stdout", output)

    exit_code = happy_env.main(["plugin-repair", "--dry-run", "--no-interactive"])

    assert exit_code == 0
    assert "plugin-repair ドライラン" in output.getvalue()
    assert "happy-core@happy-ai-life-marketplace" in output.getvalue()
    assert "happy-coding@happy-ai-life-marketplace" in output.getvalue()


def test_app_plugin_repair_dry_run_preserves_subset_followup_command(monkeypatch) -> None:
    output = io.StringIO()

    monkeypatch.setattr(happy_env, "resolve_user_home", lambda: Path(r"C:\Users\tester"))
    monkeypatch.setattr(happy_env.sys, "stdout", output)

    exit_code = happy_env.main(
        ["plugin-repair", "--plugin", "happy-core", "--dry-run", "--no-interactive"]
    )

    assert exit_code == 0
    assert "uv run app.py plugin-repair --plugin happy-core --yes --no-interactive" in output.getvalue()


def test_app_plugin_repair_requires_yes_when_non_interactive(monkeypatch) -> None:
    output = io.StringIO()

    monkeypatch.setattr(happy_env, "resolve_user_home", lambda: Path(r"C:\Users\tester"))
    monkeypatch.setattr(happy_env.sys, "stdout", output)

    exit_code = happy_env.main(["plugin-repair", "--no-interactive"])

    assert exit_code == 1
    assert "確認が必要です" in output.getvalue()


def test_app_plugin_repair_restores_backup_on_install_failure(monkeypatch, tmp_path) -> None:
    installed_dir = (
        tmp_path
        / ".copilot"
        / "installed-plugins"
        / "happy-ai-life-marketplace"
        / "happy-core"
    )
    installed_dir.mkdir(parents=True)
    original_file = installed_dir / "plugin.json"
    original_file.write_text("old", encoding="utf-8")

    output = io.StringIO()

    monkeypatch.setattr(happy_env, "resolve_user_home", lambda: tmp_path)
    monkeypatch.setattr(happy_env, "resolve_copilot_executable", lambda: "copilot")
    monkeypatch.setattr(happy_env.sys, "stdout", output)

    def fake_run(command: tuple[str, ...], **_: object) -> object:
        assert command == ("copilot", "plugin", "install", "happy-core@happy-ai-life-marketplace")

        class Completed:
            returncode = 1
            stdout = b""
            stderr = b"install failed"

        return Completed()

    monkeypatch.setattr(happy_env.subprocess, "run", fake_run)

    exit_code = happy_env.main(
        ["plugin-repair", "--plugin", "happy-core", "--yes", "--no-interactive"]
    )

    assert exit_code == 1
    assert original_file.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".copilot/plugin-backups/happy-ai-life-marketplace-*/happy-core/plugin.json"))
    assert "復元: 成功" in output.getvalue()


def test_app_plugin_repair_delete_failure_returns_controlled_message(monkeypatch, tmp_path) -> None:
    installed_dir = (
        tmp_path
        / ".copilot"
        / "installed-plugins"
        / "happy-ai-life-marketplace"
        / "happy-core"
    )
    installed_dir.mkdir(parents=True)
    (installed_dir / "plugin.json").write_text("old", encoding="utf-8")

    output = io.StringIO()

    monkeypatch.setattr(happy_env, "resolve_user_home", lambda: tmp_path)
    monkeypatch.setattr(happy_env.sys, "stdout", output)
    monkeypatch.setattr(happy_env, "remove_directory", lambda _: (_ for _ in ()).throw(OSError("locked")))

    exit_code = happy_env.main(
        ["plugin-repair", "--plugin", "happy-core", "--yes", "--no-interactive"]
    )

    assert exit_code == 1
    assert "失敗した step: delete" in output.getvalue()
    assert "locked" in output.getvalue()


def test_app_plugin_repair_eof_during_confirmation_cancels_cleanly(monkeypatch) -> None:
    output = io.StringIO()

    monkeypatch.setattr(happy_env, "resolve_user_home", lambda: Path(r"C:\Users\tester"))
    monkeypatch.setattr(happy_env, "stdin_is_interactive", lambda stream=None: True)
    monkeypatch.setattr(happy_env.sys, "stdout", output)
    monkeypatch.setattr("builtins.input", lambda prompt="": (_ for _ in ()).throw(EOFError()))

    exit_code = happy_env.main(["plugin-repair"])

    assert exit_code == 1
    assert "plugin-repair を中止しました。" in output.getvalue()
