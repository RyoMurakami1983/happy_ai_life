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


def test_build_repo_sync_arguments_include_target_and_flags() -> None:
    target_repo_path = Path(r"C:\repos\sample")

    arguments = happy_env.build_repo_sync_arguments(
        target_repo_path,
        mirror=True,
        dry_run=True,
        verbose_log=True,
    )

    assert arguments == (
        "-TargetRepoPath",
        str(target_repo_path),
        "-Mirror",
        "-DryRun",
        "-VerboseLog",
    )


def test_build_repo_secure_check_arguments_include_target_and_json_flag() -> None:
    target_repo_path = Path(r"C:\repos\sample")

    arguments = happy_env.build_repo_secure_check_arguments(target_repo_path, as_json=True)

    assert arguments == ("-TargetRepoPath", str(target_repo_path), "-AsJson")


def test_build_option_summary_for_dry_run_and_mirror() -> None:
    summary = happy_env.build_option_summary(dry_run=True, mirror=True, verbose_log=False)

    assert "現在はドライランです。" in summary
    assert "ミラー指定の影響を確認します。" in summary
    assert "リポジトリ同期ではミラー削除が有効です。" in summary
    assert "同期先だけのファイルやディレクトリは完全削除されます。" in summary
    assert "ホーム同期は skills/、agents/、repo-template/、.github/hooks/" in summary


def test_build_option_summary_for_live_normal_sync_with_verbose_log() -> None:
    summary = happy_env.build_option_summary(dry_run=False, mirror=False, verbose_log=True)

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


def test_run_repo_sync_resolves_relative_paths_from_caller_cwd(tmp_path: Path, monkeypatch) -> None:
    caller_dir = tmp_path / "caller"
    caller_dir.mkdir()
    captured_arguments: dict[str, tuple[str, ...]] = {}

    def fake_run_script(script_name: str, arguments: tuple[str, ...], *, label: str, notes=()) -> happy_env.CommandResult:
        captured_arguments["arguments"] = arguments
        return happy_env.CommandResult(label=label, command=(script_name,), returncode=0, stdout="", stderr="", notes=tuple(notes))

    monkeypatch.chdir(caller_dir)
    monkeypatch.setattr(happy_env, "run_script", fake_run_script)

    result = happy_env.run_repo_sync(Path("."))

    assert result.succeeded
    assert captured_arguments["arguments"][:2] == ("-TargetRepoPath", str(caller_dir.resolve()))


def test_run_repo_secure_check_resolves_relative_paths_from_caller_cwd(tmp_path: Path, monkeypatch) -> None:
    caller_dir = tmp_path / "caller"
    caller_dir.mkdir()
    captured_arguments: dict[str, tuple[str, ...]] = {}

    def fake_run_script(script_name: str, arguments: tuple[str, ...], *, label: str, notes=()) -> happy_env.CommandResult:
        captured_arguments["script_name"] = (script_name,)
        captured_arguments["arguments"] = arguments
        return happy_env.CommandResult(label=label, command=(script_name,), returncode=0, stdout="", stderr="", notes=tuple(notes))

    monkeypatch.chdir(caller_dir)
    monkeypatch.setattr(happy_env, "run_script", fake_run_script)

    result = happy_env.run_repo_secure_check(Path("."))

    assert result.succeeded
    assert captured_arguments["script_name"] == ("repo-secure-check.ps1",)
    assert captured_arguments["arguments"][:2] == ("-TargetRepoPath", str(caller_dir.resolve()))


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


def test_parse_repo_security_report_validates_shape() -> None:
    report = happy_env.parse_repo_security_report(
        """
        {
          "targetRepoPath": "C:\\\\repos\\\\sample",
          "isGitRepo": true,
          "missing": ["repoInstructions"],
          "warnings": ["Branch Protection / Ruleset はローカルでは確認できません。"],
          "checks": [
            {
              "key": "repoInstructions",
              "label": "repo instructions",
              "ok": false,
              "path": "C:\\\\repos\\\\sample\\\\.github\\\\copilot-instructions.md",
              "details": "repo-wide instructions がありません。"
            }
          ]
        }
        """
    )

    assert report["targetRepoPath"] == r"C:\repos\sample"
    assert report["missing"] == ["repoInstructions"]
    assert report["checks"][0]["ok"] is False


def test_run_repo_bootstrap_dry_run_uses_repo_sync_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        happy_env,
        "inspect_repo_security",
        lambda path: {
            "targetRepoPath": str(path),
            "isGitRepo": True,
            "missing": ["repoInstructions"],
            "warnings": ["Branch Protection / Ruleset はローカルでは確認できません。"],
            "checks": [],
        },
    )
    monkeypatch.setattr(
        happy_env,
        "run_repo_sync",
        lambda path, **kwargs: happy_env.CommandResult(
            label="リポジトリ同期",
            command=("repo", str(path)),
            returncode=0,
            stdout="dry-run ok",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        happy_env,
        "run_install_git_hooks",
        lambda path: pytest.fail("run_install_git_hooks must not be called for dry-run bootstrap"),
    )

    result = happy_env.run_repo_bootstrap(Path(r"C:\repos\sample"), apply=False)

    assert result.succeeded
    assert "不足があるため、repo bootstrap のドライランを実行しました。" in result.stdout
    assert "実適用では repo sync の後に Git hooks インストールも実行します。" in result.stdout
    assert "dry-run ok" in result.stdout


def test_run_repo_bootstrap_apply_runs_repo_sync_and_install_hooks(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        happy_env,
        "inspect_repo_security",
        lambda path: {
            "targetRepoPath": str(path),
            "isGitRepo": True,
            "missing": ["repoInstructions", "coreHooksPath"],
            "warnings": [],
            "checks": [],
        },
    )

    def fake_run_repo_sync(path: Path, **kwargs: object) -> happy_env.CommandResult:
        calls.append(f"repo:{path}")
        return happy_env.CommandResult(label="リポジトリ同期", command=("repo", str(path)), returncode=0, stdout="repo ok", stderr="")

    def fake_run_install_git_hooks(path: Path) -> happy_env.CommandResult:
        calls.append(f"hooks:{path}")
        return happy_env.CommandResult(label="Git hooks インストール", command=("hooks", str(path)), returncode=0, stdout="hooks ok", stderr="")

    monkeypatch.setattr(happy_env, "run_repo_sync", fake_run_repo_sync)
    monkeypatch.setattr(happy_env, "run_install_git_hooks", fake_run_install_git_hooks)

    result = happy_env.run_repo_bootstrap(Path(r"C:\repos\sample"), apply=True)

    assert result.succeeded
    assert calls == [r"repo:C:\repos\sample", r"hooks:C:\repos\sample"]
    assert "repo ok" in result.stdout
    assert "hooks ok" in result.stdout


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


def test_gui_mirror_checkbox_label_matches_warning_language() -> None:
    root = _create_tk_root_or_skip()
    try:
        gui = happy_env.HappyEnvGui(root)
        assert gui.main_frame is not None
        labels: list[str] = []
        for child in gui.main_frame.winfo_children():
            if child.winfo_class() != "TFrame":
                continue
            labels.extend(
                widget.cget("text")
                for widget in child.winfo_children()
                if widget.winfo_class() == "TCheckbutton"
            )

        assert "ミラー同期（リポジトリ同期では同期先だけのファイルやディレクトリを削除）" in labels
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


def test_confirm_mirror_sync_returns_true_for_yes(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")
    assert happy_env.confirm_mirror_sync() is True


def test_confirm_mirror_sync_returns_false_for_non_yes(monkeypatch) -> None:
    for answer in ("y", "no", "", "はい"):
        monkeypatch.setattr("builtins.input", lambda _prompt, _a=answer: _a)
        assert happy_env.confirm_mirror_sync() is False, f"Expected False for {answer!r}"


def test_confirm_repo_bootstrap_returns_true_for_yes(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")
    assert happy_env.confirm_repo_bootstrap() is True


def test_confirm_repo_bootstrap_returns_false_for_non_yes(monkeypatch) -> None:
    for answer in ("y", "no", "", "はい"):
        monkeypatch.setattr("builtins.input", lambda _prompt, _a=answer: _a)
        assert happy_env.confirm_repo_bootstrap() is False, f"Expected False for {answer!r}"


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


def test_run_cli_repo_mirror_without_dry_run_prompts_for_confirmation(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "no")
    monkeypatch.setattr(happy_env, "run_repo_sync", lambda *args, **kwargs: pytest.fail("run_repo_sync must not be called"))

    exit_code = happy_env.run_cli(
        happy_env.build_parser().parse_args(["repo", r"C:\repos\sample", "--mirror"])
    )

    assert exit_code == 1


def test_run_cli_repo_bootstrap_without_apply_skips_confirmation(monkeypatch) -> None:
    called: list[bool] = []

    def fake_run_repo_bootstrap(*args: object, **kwargs: object) -> happy_env.CommandResult:
        called.append(True)
        return happy_env.CommandResult(label="test", command=(), returncode=0, stdout="", stderr="")

    monkeypatch.setattr(happy_env, "run_repo_bootstrap", fake_run_repo_bootstrap)

    exit_code = happy_env.run_cli(
        happy_env.build_parser().parse_args(["repo-bootstrap", r"C:\repos\sample"])
    )

    assert exit_code == 0
    assert called == [True]
