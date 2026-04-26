from __future__ import annotations

import io
import subprocess
from pathlib import Path

import happy_env


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


def test_write_console_line_replaces_unencodable_characters() -> None:
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="ascii", newline="\n")

    happy_env.write_console_line("status ✓", stream=stream)

    stream.flush()
    assert buffer.getvalue() == b"status ?\n"


def test_prompt_sync_options_toggles_requested_options(monkeypatch) -> None:
    answers = iter(["1", "2", ""])
    stream = io.StringIO()

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(happy_env.sys, "stdout", stream)

    dry_run, verbose_log = happy_env.prompt_sync_options()

    assert (dry_run, verbose_log) == (False, True)
    output = stream.getvalue()
    assert "[ON] enabled" in output
    assert "[OFF] disabled" in output


def test_run_cli_interactive_uses_safe_defaults_when_stdin_is_not_tty(monkeypatch) -> None:
    captured: dict[str, bool] = {}
    output = io.StringIO()

    class _FakeStdin:
        def isatty(self) -> bool:
            return False

    def fake_run_home_sync(*, mirror: bool, dry_run: bool, verbose_log: bool) -> happy_env.CommandResult:
        captured["mirror"] = mirror
        captured["dry_run"] = dry_run
        captured["verbose_log"] = verbose_log
        return happy_env.CommandResult(
            label="test",
            command=(),
            returncode=0,
            stdout="SYNC_STATS:ADDED=1,UPDATED=0,DELETED=0",
            stderr="",
        )

    monkeypatch.setattr(happy_env.sys, "stdin", _FakeStdin())
    monkeypatch.setattr(happy_env.sys, "stdout", output)
    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)

    exit_code = happy_env.run_cli_interactive(
        happy_env.build_parser().parse_args(["home"])
    )

    assert exit_code == 0
    assert captured == {"mirror": False, "dry_run": True, "verbose_log": False}


def test_run_cli_interactive_allows_non_interactive_live_mode(monkeypatch) -> None:
    captured: dict[str, bool] = {}
    output = io.StringIO()

    class _FakeStdin:
        def isatty(self) -> bool:
            return False

    def fake_run_home_sync(*, mirror: bool, dry_run: bool, verbose_log: bool) -> happy_env.CommandResult:
        captured["mirror"] = mirror
        captured["dry_run"] = dry_run
        captured["verbose_log"] = verbose_log
        return happy_env.CommandResult(
            label="test",
            command=(),
            returncode=0,
            stdout="SYNC_STATS:ADDED=1,UPDATED=0,DELETED=0",
            stderr="",
        )

    monkeypatch.setattr(happy_env.sys, "stdin", _FakeStdin())
    monkeypatch.setattr(happy_env.sys, "stdout", output)
    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)

    exit_code = happy_env.run_cli_interactive(
        happy_env.build_parser().parse_args(["home", "--no-interactive"])
    )

    assert exit_code == 0
    assert captured == {"mirror": False, "dry_run": False, "verbose_log": False}


def test_run_cli_interactive_falls_back_to_safe_defaults_on_eof(monkeypatch) -> None:
    captured: dict[str, bool] = {}
    output = io.StringIO()

    class _FakeStdin:
        def isatty(self) -> bool:
            return True

    def fake_run_home_sync(*, mirror: bool, dry_run: bool, verbose_log: bool) -> happy_env.CommandResult:
        captured["mirror"] = mirror
        captured["dry_run"] = dry_run
        captured["verbose_log"] = verbose_log
        return happy_env.CommandResult(
            label="test",
            command=(),
            returncode=0,
            stdout="SYNC_STATS:ADDED=1,UPDATED=0,DELETED=0",
            stderr="",
        )

    monkeypatch.setattr(happy_env.sys, "stdin", _FakeStdin())
    monkeypatch.setattr(happy_env.sys, "stdout", output)
    monkeypatch.setattr("builtins.input", lambda _prompt="": (_ for _ in ()).throw(EOFError()))
    monkeypatch.setattr(happy_env, "run_home_sync", fake_run_home_sync)

    exit_code = happy_env.run_cli_interactive(
        happy_env.build_parser().parse_args(["home"])
    )

    assert exit_code == 0
    assert captured == {"mirror": False, "dry_run": True, "verbose_log": False}


def test_main_defaults_to_home_command(monkeypatch) -> None:
    captured: list[tuple[str, bool]] = []

    def fake_run_cli_interactive(namespace, *, has_explicit_flags: bool = False) -> int:
        captured.append((namespace.command, has_explicit_flags))
        return 7

    monkeypatch.setattr(happy_env, "run_cli_interactive", fake_run_cli_interactive)

    exit_code = happy_env.main([])

    assert exit_code == 7
    assert captured == [("home", False)]


def test_main_detects_explicit_global_flags(monkeypatch) -> None:
    captured: list[tuple[bool, bool, str]] = []

    def fake_run_cli_interactive(namespace, *, has_explicit_flags: bool = False) -> int:
        captured.append((namespace.dry_run, has_explicit_flags, namespace.command))
        return 3

    monkeypatch.setattr(happy_env, "run_cli_interactive", fake_run_cli_interactive)

    exit_code = happy_env.main(["--dry-run"])

    assert exit_code == 3
    assert captured == [(True, True, "home")]


def test_main_detects_explicit_no_interactive_flag(monkeypatch) -> None:
    captured: list[tuple[bool | None, bool, str]] = []

    def fake_run_cli_interactive(namespace, *, has_explicit_flags: bool = False) -> int:
        captured.append((namespace.interactive, has_explicit_flags, namespace.command))
        return 5

    monkeypatch.setattr(happy_env, "run_cli_interactive", fake_run_cli_interactive)

    exit_code = happy_env.main(["home", "--no-interactive"])

    assert exit_code == 5
    assert captured == [(False, True, "home")]


def test_parse_sync_stats_single_execution() -> None:
    """単一 robocopy 実行の統計集計"""
    stdout = "SYNC_STATS:ADDED=10,UPDATED=5,DELETED=2"
    result = happy_env.parse_sync_stats(stdout)
    assert result == {"added": 10, "updated": 5, "deleted": 2}


def test_parse_sync_stats_multiple_executions() -> None:
    """複数 robocopy 実行の統計合算"""
    stdout = """\
SYNC_STATS:ADDED=10,UPDATED=5,DELETED=2
SYNC_STATS:ADDED=3,UPDATED=2,DELETED=0
SYNC_STATS:ADDED=0,UPDATED=1,DELETED=1"""
    result = happy_env.parse_sync_stats(stdout)
    assert result == {"added": 13, "updated": 8, "deleted": 3}


def test_parse_sync_stats_no_match() -> None:
    """マッチしない場合は None を返す"""
    result = happy_env.parse_sync_stats("no stats here")
    assert result is None


def test_parse_sync_files_dry_single_execution() -> None:
    """単一ドライラン実行のファイルリスト抽出"""
    stdout = """\
SYNC_FILES_DRY:ADDED=["file1.md","file2.json"]
SYNC_FILES_DRY:UPDATED=["file3.md"]
SYNC_FILES_DRY:DELETED=[]"""
    result = happy_env.parse_sync_files_dry(stdout)
    assert result is not None
    assert result["added"] == ["file1.md", "file2.json"]
    assert result["updated"] == ["file3.md"]
    assert result["deleted"] == []
    assert result["added_more"] == 0


def test_parse_sync_files_dry_multiple_executions() -> None:
    """複数 robocopy 実行のファイルリストマージ"""
    stdout = """\
SYNC_FILES_DRY:ADDED=["skills/foo.md"]
SYNC_FILES_DRY:UPDATED=["agents/bar.json"]
SYNC_FILES_DRY:DELETED=[]
SYNC_FILES_DRY:ADDED=["repo-template/baz.md"]
SYNC_FILES_DRY:UPDATED=[]
SYNC_FILES_DRY:DELETED=["old.md"]
SYNC_FILES_OVERFLOW:ADDED_MORE=5
SYNC_FILES_OVERFLOW:UPDATED_MORE=3"""
    result = happy_env.parse_sync_files_dry(stdout)
    assert result is not None
    assert result["added"] == ["skills/foo.md", "repo-template/baz.md"]
    assert result["updated"] == ["agents/bar.json"]
    assert result["deleted"] == ["old.md"]
    assert result["added_more"] == 5
    assert result["updated_more"] == 3


def test_parse_sync_files_dry_no_match() -> None:
    """マッチしない場合は None を返す"""
    result = happy_env.parse_sync_files_dry("no sync files here")
    assert result is None


def test_normalize_path_to_relative_with_copilot_prefix() -> None:
    """絶対パスから .copilot 以降を抽出"""
    abs_path = r"C:\Users\test\.copilot\skills\foo\bar.md"
    result = happy_env.normalize_path_to_relative(abs_path)
    # .copilot の次の 9 文字（/.copilot/）をスキップして、skills/foo/bar.md を取得
    assert "skills" in result and "bar.md" in result


def test_normalize_path_to_relative_already_relative() -> None:
    """相対パスはそのまま返す"""
    rel_path = "skills/foo/bar.md"
    result = happy_env.normalize_path_to_relative(rel_path)
    assert result == "skills/foo/bar.md"


def test_normalize_path_to_relative_no_copilot_prefix() -> None:
    """
    .copilot が見つからない場合は、相対パスをそのまま返す
    (robocopy ログから渡ってくる相対パスはそのまま返すべき)
    """
    rel_path = "other/path/file.md"
    result = happy_env.normalize_path_to_relative(rel_path)
    assert result == "other/path/file.md"


def test_parse_sync_files_dry_overflow_only_returns_dict() -> None:
    """
    オーバーフロー情報のみがある場合、dict を返す（None ではない）
    ファイルリスト取得に失敗したが、ファイルが存在することは検出できたケース
    """
    stdout = """\
SYNC_FILES_DRY:ADDED=[]
SYNC_FILES_DRY:UPDATED=[]
SYNC_FILES_DRY:DELETED=[]
SYNC_FILES_OVERFLOW:ADDED_MORE=100
SYNC_FILES_OVERFLOW:UPDATED_MORE=50
SYNC_FILES_OVERFLOW:DELETED_MORE=10"""
    result = happy_env.parse_sync_files_dry(stdout)
    assert result is not None
    assert result["added"] == []
    assert result["updated"] == []
    assert result["deleted"] == []
    assert result["added_more"] == 100
    assert result["updated_more"] == 50
    assert result["deleted_more"] == 10


def test_format_file_details_shows_overflow_message_when_list_unavailable() -> None:
    """
    オーバーフロー情報のみがある場合、「一覧取得に失敗」メッセージを表示
    """
    files = {
        'added': [],
        'updated': [],
        'deleted': [],
        'added_more': 100,
        'updated_more': 50,
        'deleted_more': 10,
    }
    result = happy_env.format_file_details(files, dry_run=True)
    assert "一覧取得に失敗" in result
    assert "100 個以上" in result
    assert "50 個以上" in result
    assert "10 個以上" in result
    # "変更ファイルなし" は表示されないこと
    assert "変更ファイルなし" not in result


def test_format_file_details_no_changes_when_all_empty() -> None:
    """
    ファイルリストもオーバーフロー情報もない場合、「変更ファイルなし」を表示
    """
    files = {
        'added': [],
        'updated': [],
        'deleted': [],
        'added_more': 0,
        'updated_more': 0,
        'deleted_more': 0,
    }
    result = happy_env.format_file_details(files, dry_run=True)
    assert "変更ファイルなし" in result
    assert "一覧取得に失敗" not in result


