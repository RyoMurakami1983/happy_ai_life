from __future__ import annotations

import subprocess
import tkinter as tk
from pathlib import Path

import pytest

import happy_env


def _create_tk_root_or_skip() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk root is unavailable in this environment: {exc}")
    root.withdraw()
    return root


def test_build_home_sync_arguments_include_requested_flags() -> None:
    arguments = happy_env.build_home_sync_arguments(mirror=True, dry_run=True, verbose_log=True)

    assert arguments == ("-Mirror", "-DryRun", "-VerboseLog")


def test_build_option_summary_for_dry_run() -> None:
    summary = happy_env.build_option_summary(dry_run=True, verbose_log=False)

    assert "現在はドライランです。" in summary
    assert "通常同期です。" in summary
    assert "ホーム同期は skills/、agents/、repo-template/、.github/hooks/" in summary


def test_build_option_summary_for_live_normal_sync_with_verbose_log() -> None:
    summary = happy_env.build_option_summary(dry_run=False, verbose_log=True)

    assert "現在は実行モードです。" in summary
    assert "通常同期です。" in summary
    assert "ホーム同期は skills/、agents/、repo-template/、.github/hooks/" in summary
    assert "詳細ログを表示します。" in summary


def test_build_mcp_config_notes_when_live_file_missing(tmp_path: Path) -> None:
    sample_path = tmp_path / happy_env.MCP_CONFIG_SAMPLE_FILENAME
    sample_path.write_text("{}", encoding="utf-8")

    notes = happy_env.build_mcp_config_notes(tmp_path)

    assert notes[0] == "MCP 設定はまだ初期化されていません。"
    assert f"'{happy_env.MCP_CONFIG_FILENAME}'" in notes[1]


def test_build_mcp_config_notes_is_empty_when_live_file_exists(tmp_path: Path) -> None:
    (tmp_path / happy_env.MCP_CONFIG_SAMPLE_FILENAME).write_text("{}", encoding="utf-8")
    (tmp_path / happy_env.MCP_CONFIG_FILENAME).write_text("{}", encoding="utf-8")

    notes = happy_env.build_mcp_config_notes(tmp_path)

    assert notes == ()


def test_build_script_command_respects_execution_policy_by_default(monkeypatch) -> None:
    monkeypatch.setattr(happy_env, "resolve_powershell_executable", lambda: "pwsh")
    monkeypatch.delenv(happy_env.ALLOW_POLICY_BYPASS_ENV, raising=False)

    command = happy_env.build_script_command("sync-to-home.ps1", ("-DryRun",))

    assert "-ExecutionPolicy" not in command


def test_build_script_command_allows_explicit_policy_bypass(monkeypatch) -> None:
    monkeypatch.setattr(happy_env, "resolve_powershell_executable", lambda: "pwsh")
    monkeypatch.setenv(happy_env.ALLOW_POLICY_BYPASS_ENV, "1")

    command = happy_env.build_script_command("sync-to-home.ps1", ("-DryRun",))

    assert command[:5] == ("pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File")


def test_decode_process_output_uses_windows_locale(monkeypatch) -> None:
    monkeypatch.setattr(happy_env.locale, "getpreferredencoding", lambda _do_setlocale=False: "cp932")

    decoded = happy_env.decode_process_output("Windows の堅牢性".encode("cp932"))

    assert decoded == "Windows の堅牢性"


def test_run_script_decodes_stdout_and_stderr_with_locale(monkeypatch) -> None:
    monkeypatch.setattr(happy_env, "build_script_command", lambda script_name, arguments: ("pwsh", "-File", script_name, *arguments))
    monkeypatch.setattr(happy_env.locale, "getpreferredencoding", lambda _do_setlocale=False: "cp932")

    completed = subprocess.CompletedProcess(
        args=("pwsh",),
        returncode=3,
        stdout="詳細ログ".encode("cp932"),
        stderr="警告".encode("cp932"),
    )
    monkeypatch.setattr(happy_env.subprocess, "run", lambda *args, **kwargs: completed)

    result = happy_env.run_script("sync-to-home.ps1", ("-VerboseLog",), label="ホーム同期")

    assert result.returncode == 3
    assert result.stdout == "詳細ログ"
    assert result.stderr == "警告"


def test_gui_gives_extra_vertical_space_to_log_pane() -> None:
    root = _create_tk_root_or_skip()
    try:
        gui = happy_env.HappyEnvGui(root)
        assert gui.main_frame is not None
        assert int(gui.output.grid_info()["row"]) == 4
        assert int(gui.main_frame.grid_rowconfigure(4)["weight"]) == 1
        assert int(gui.main_frame.grid_rowconfigure(3)["weight"]) == 0
    finally:
        root.destroy()


def test_main_home_delegates_to_cli(monkeypatch) -> None:
    captured: list[str | tuple[str, ...]] = []

    def fake_run_cli(namespace) -> int:
        captured.append(namespace.command)
        return 7

    monkeypatch.setattr(happy_env, "run_cli", fake_run_cli)
    monkeypatch.setattr(happy_env, "launch_gui", lambda: 99)

    exit_code = happy_env.main(["home", "--dry-run"])

    assert exit_code == 7
    assert captured == ["home"]


def test_run_cli_home_mirror_without_dry_run_skips_confirmation(monkeypatch) -> None:
    called: list[bool] = []

    def fake_run_home_sync(**kw: object) -> happy_env.CommandResult:
        called.append(True)
        return happy_env.CommandResult(label="test", command=(), returncode=0, stdout="", stderr="")

    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)

    exit_code = happy_env.run_cli(
        happy_env.build_parser().parse_args(["home", "--mirror"])
    )

    assert exit_code == 0
    assert called == [True]


def test_run_cli_mirror_with_dry_run_skips_confirmation(monkeypatch) -> None:
    called: list[bool] = []

    def fake_run_home_sync(**kw: object) -> happy_env.CommandResult:
        called.append(True)
        return happy_env.CommandResult(label="test", command=(), returncode=0, stdout="", stderr="")

    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)

    exit_code = happy_env.run_cli(
        happy_env.build_parser().parse_args(["home", "--mirror", "--dry-run"])
    )

    assert exit_code == 0
    assert called == [True]



