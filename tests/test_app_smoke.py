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
