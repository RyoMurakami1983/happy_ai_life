from __future__ import annotations

import argparse
import locale
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TextIO

ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
ALLOW_POLICY_BYPASS_ENV = "HAPPY_ENV_ALLOW_POLICY_BYPASS"
REPAIR_MARKETPLACE = "happy-ai-life-marketplace"
REPAIRABLE_PLUGINS = ("happy-core", "happy-coding")


@dataclass(frozen=True)
class CommandResult:
    label: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    notes: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class PluginRepairTarget:
    name: str
    install_spec: str
    installed_dir: Path
    backup_dir: Path
    existed_before: bool


@dataclass(frozen=True)
class PluginRepairPlan:
    marketplace: str
    backup_root: Path
    targets: tuple[PluginRepairTarget, ...]


def resolve_user_home() -> Path:
    return Path.home()


def resolve_copilot_home() -> Path:
    return resolve_user_home() / ".copilot"


def resolve_copilot_executable() -> str:
    resolved = shutil.which("copilot")
    if resolved is not None:
        return resolved

    raise RuntimeError("copilot CLI が見つかりません。インストール後に再実行してください。")


def resolve_powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved is not None:
            return resolved

    raise RuntimeError("PowerShell が見つかりません。インストール後に再実行してください。")


def resolve_bash_executable() -> str:
    resolved = shutil.which("bash")
    if resolved is not None:
        return resolved

    raise RuntimeError("bash が見つかりません。インストール後に再実行してください。")


def resolve_script_path(script_name: str) -> Path:
    if script_name.endswith((".ps1", ".sh")):
        script_path = SCRIPTS_DIR / script_name
        if script_path.exists():
            return script_path
        raise FileNotFoundError(f"Script not found: {script_path}")

    preferred_suffixes = (".ps1",) if os.name == "nt" else (".sh", ".ps1")
    for suffix in preferred_suffixes:
        candidate = SCRIPTS_DIR / f"{script_name}{suffix}"
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Script not found for stem: {script_name}")


def build_script_command(script_name: str, arguments: Sequence[str]) -> tuple[str, ...]:
    script_path = resolve_script_path(script_name)
    if script_path.suffix == ".sh":
        normalized_arguments = tuple(
            f"--{argument[1:]}" if argument.startswith("-") and not argument.startswith("--") else argument
            for argument in arguments
        )
        return (resolve_bash_executable(), str(script_path), *normalized_arguments, "--SourceRoot", str(ROOT_DIR))

    command = [resolve_powershell_executable(), "-NoProfile"]
    if os.getenv(ALLOW_POLICY_BYPASS_ENV) == "1":
        command.extend(["-ExecutionPolicy", "Bypass"])

    command.extend(["-File", str(script_path), *arguments])
    return tuple(command)


def build_home_sync_arguments(
    *,
    mirror: bool = False,
    dry_run: bool = False,
    verbose_log: bool = False,
) -> tuple[str, ...]:
    arguments: list[str] = []
    if mirror:
        arguments.append("-Mirror")
    if dry_run:
        arguments.append("-DryRun")
    if verbose_log:
        arguments.append("-VerboseLog")
    return tuple(arguments)


def normalize_plugin_selection(selected_plugins: Sequence[str] | None) -> tuple[str, ...]:
    if not selected_plugins:
        return REPAIRABLE_PLUGINS

    normalized: list[str] = []
    for plugin_name in selected_plugins:
        if plugin_name not in REPAIRABLE_PLUGINS:
            raise ValueError(f"未対応の plugin 名です: {plugin_name}")
        if plugin_name not in normalized:
            normalized.append(plugin_name)
    return tuple(normalized)


def build_plugin_repair_plan(
    *,
    selected_plugins: Sequence[str] | None = None,
    marketplace: str = REPAIR_MARKETPLACE,
    now: datetime | None = None,
) -> PluginRepairPlan:
    installed_root = resolve_copilot_home() / "installed-plugins" / marketplace
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S-%f")
    backup_root = resolve_copilot_home() / "plugin-backups" / f"{marketplace}-{timestamp}"

    targets = tuple(
        PluginRepairTarget(
            name=plugin_name,
            install_spec=f"{plugin_name}@{marketplace}",
            installed_dir=installed_root / plugin_name,
            backup_dir=backup_root / plugin_name,
            existed_before=(installed_root / plugin_name).exists(),
        )
        for plugin_name in normalize_plugin_selection(selected_plugins)
    )
    return PluginRepairPlan(
        marketplace=marketplace,
        backup_root=backup_root,
        targets=targets,
    )


def build_plugin_repair_followup_command(plan: PluginRepairPlan) -> str:
    command = ["uv", "run", "app.py", "plugin-repair"]
    if tuple(target.name for target in plan.targets) != REPAIRABLE_PLUGINS:
        for target in plan.targets:
            command.extend(["--plugin", target.name])
    command.extend(["--yes", "--no-interactive"])
    return " ".join(command)


def format_plugin_repair_plan(plan: PluginRepairPlan) -> str:
    lines = [
        "◆ plugin-repair ドライラン",
        f"対象 marketplace: {plan.marketplace}",
        f"backup root: {plan.backup_root}",
        "",
        "予定操作:",
    ]
    for target in plan.targets:
        if target.existed_before:
            lines.append(f"- backup {target.installed_dir} -> {target.backup_dir}")
            lines.append(f"- delete {target.installed_dir}")
        else:
            lines.append(f"- skip backup (未インストール): {target.installed_dir}")
        lines.append(f"- copilot plugin install {target.install_spec}")

    lines.extend(
        [
            "",
            f"実行するには `{build_plugin_repair_followup_command(plan)}` を使ってください。",
        ]
    )
    return "\n".join(lines)


def prompt_plugin_repair_confirmation(plan: PluginRepairPlan) -> bool:
    write_console_line("")
    write_console_line("◆ plugin repair 確認")
    write_console_line(f"対象 marketplace: {plan.marketplace}")
    write_console_line(f"backup root: {plan.backup_root}")
    write_console_line("対象 plugin:")
    for target in plan.targets:
        state = "installed" if target.existed_before else "missing"
        write_console_line(f"  - {target.name} ({state})")
    write_console_line("")
    write_console_line("この操作は対象 plugin directory を backup 後に削除して再インストールします。")
    write_console_line("続行する場合は y を入力してください。")
    write_console_line("")

    answer = input("> ").strip().lower()
    return answer in {"y", "yes"}


def run_external_command(command: Sequence[str], *, label: str) -> CommandResult:
    completed = subprocess.run(
        tuple(command),
        cwd=ROOT_DIR,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=False,
        check=False,
    )
    return CommandResult(
        label=label,
        command=tuple(command),
        returncode=completed.returncode,
        stdout=decode_process_output(completed.stdout).strip(),
        stderr=decode_process_output(completed.stderr).strip(),
    )


def run_copilot_plugin_install(install_spec: str) -> CommandResult:
    return run_external_command(
        (resolve_copilot_executable(), "plugin", "install", install_spec),
        label=f"plugin install {install_spec}",
    )


def remove_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def copy_directory(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def restore_plugin_directory(target: PluginRepairTarget) -> str:
    if not target.existed_before or not target.backup_dir.exists():
        return "未実行"

    try:
        remove_directory(target.installed_dir)
        copy_directory(target.backup_dir, target.installed_dir)
        return "成功"
    except OSError as exc:
        return f"失敗 ({exc})"


def build_plugin_repair_failure(
    *,
    plan: PluginRepairPlan,
    target: PluginRepairTarget,
    step: str,
    message: str,
    restore_message: str = "未実行",
    completed_plugins: Sequence[str] = (),
    install_result: CommandResult | None = None,
) -> CommandResult:
    lines = [
        "✗ plugin-repair 失敗",
        f"失敗した plugin: {target.name}",
        f"失敗した step: {step}",
        f"backup root: {plan.backup_root}",
        f"復元: {restore_message}",
        f"詳細: {message}",
    ]
    if completed_plugins:
        lines.append(f"先に完了した plugin: {', '.join(completed_plugins)}")
    if install_result is not None and install_result.stdout:
        lines.extend(("", "copilot stdout:", install_result.stdout))
    if install_result is not None and install_result.stderr:
        lines.extend(("", "copilot stderr:", install_result.stderr))
    return CommandResult(
        label="plugin-repair",
        command=("app.py", "plugin-repair"),
        returncode=1,
        stdout="\n".join(lines),
        stderr="",
    )


def execute_plugin_repair(plan: PluginRepairPlan) -> CommandResult:
    plan.backup_root.mkdir(parents=True, exist_ok=True)
    completed_plugins: list[str] = []

    for target in plan.targets:
        if target.existed_before:
            try:
                copy_directory(target.installed_dir, target.backup_dir)
            except OSError as exc:
                return build_plugin_repair_failure(
                    plan=plan,
                    target=target,
                    step="backup",
                    message=str(exc),
                    completed_plugins=completed_plugins,
                )

        try:
            remove_directory(target.installed_dir)
        except OSError as exc:
            return build_plugin_repair_failure(
                plan=plan,
                target=target,
                step="delete",
                message=str(exc),
                restore_message=restore_plugin_directory(target),
                completed_plugins=completed_plugins,
            )

        install_result = run_copilot_plugin_install(target.install_spec)
        if install_result.succeeded:
            completed_plugins.append(target.name)
            continue

        return build_plugin_repair_failure(
            plan=plan,
            target=target,
            step="install",
            message=f"{target.install_spec} の再インストールに失敗しました。",
            restore_message=restore_plugin_directory(target),
            completed_plugins=completed_plugins,
            install_result=install_result,
        )

    lines = [
        "✓ plugin-repair 完了",
        f"対象 marketplace: {plan.marketplace}",
        f"backup root: {plan.backup_root}",
        f"完了した plugin: {', '.join(completed_plugins) if completed_plugins else 'なし'}",
        "次の確認: copilot plugin list",
    ]
    return CommandResult(
        label="plugin-repair",
        command=("app.py", "plugin-repair"),
        returncode=0,
        stdout="\n".join(lines),
        stderr="",
    )


def run_plugin_repair(
    *,
    selected_plugins: Sequence[str] | None = None,
    dry_run: bool = False,
    assume_yes: bool = False,
    interactive: bool | None = None,
) -> CommandResult:
    plan = build_plugin_repair_plan(selected_plugins=selected_plugins)

    if dry_run:
        return CommandResult(
            label="plugin-repair",
            command=("app.py", "plugin-repair"),
            returncode=0,
            stdout=format_plugin_repair_plan(plan),
            stderr="",
        )

    should_prompt = interactive is not False and stdin_is_interactive()
    if not assume_yes:
        if should_prompt:
            try:
                confirmed = prompt_plugin_repair_confirmation(plan)
            except EOFError:
                confirmed = False
            if not confirmed:
                return CommandResult(
                    label="plugin-repair",
                    command=("app.py", "plugin-repair"),
                    returncode=1,
                    stdout="plugin-repair を中止しました。",
                    stderr="",
                )
        else:
            return CommandResult(
                label="plugin-repair",
                command=("app.py", "plugin-repair"),
                returncode=1,
                stdout="確認が必要です。削除を伴うため、対話端末で実行するか `--yes --no-interactive` を付けてください。",
                stderr="",
            )

    return execute_plugin_repair(plan)


def decode_process_output(data: bytes) -> str:
    if not data:
        return ""

    encoding = locale.getpreferredencoding(False)
    return data.decode(encoding, errors="replace")


def run_script(script_name: str, arguments: Sequence[str], *, label: str, notes: Sequence[str] = ()) -> CommandResult:
    command = build_script_command(script_name, (*arguments, "-SourceRoot", str(ROOT_DIR)) if os.name == "nt" else arguments)
    completed = subprocess.run(
        command,
        cwd=ROOT_DIR,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=False,
        check=False,
    )
    return CommandResult(
        label=label,
        command=command,
        returncode=completed.returncode,
        stdout=decode_process_output(completed.stdout).strip(),
        stderr=decode_process_output(completed.stderr).strip(),
        notes=tuple(notes),
    )


def run_home_sync(*, mirror: bool = False, dry_run: bool = False, verbose_log: bool = False) -> CommandResult:
    arguments = list(build_home_sync_arguments(mirror=mirror, dry_run=dry_run, verbose_log=verbose_log))
    if sys.executable and resolve_script_path("sync-to-home").suffix == ".ps1":
        arguments.extend(["-PythonExecutable", sys.executable])

    return run_script(
        "sync-to-home",
        tuple(arguments),
        label="ホーム同期",
    )



def format_command_result(result: CommandResult) -> str:
    lines = [
        f"== {result.label} ==",
        f"コマンド   : {' '.join(result.command)}",
        f"終了コード : {result.returncode}",
        f"結果       : {'成功' if result.succeeded else '失敗'}",
    ]

    if result.notes:
        lines.extend(("", "補足:", *result.notes))

    if result.stdout:
        lines.extend(("", "標準出力:", result.stdout))

    if result.stderr:
        lines.extend(("", "標準エラー:", result.stderr))

    return "\n".join(lines)


def parse_sync_stats(stdout: str) -> dict[str, int] | None:
    """
    PowerShell から出力された "SYNC_STATS:..." 行を parse（複数実行に対応）
    
    例: "SYNC_STATS:ADDED=123,UPDATED=45,DELETED=0"
    複数の robocopy 実行がある場合は全行を集計
    """
    matches = re.findall(r'SYNC_STATS:ADDED=(\d+),UPDATED=(\d+),DELETED=(\d+)', stdout)
    if matches:
        total = {'added': 0, 'updated': 0, 'deleted': 0}
        for added, updated, deleted in matches:
            total['added'] += int(added)
            total['updated'] += int(updated)
            total['deleted'] += int(deleted)
        return total
    return None


def parse_sync_files_dry(stdout: str) -> dict[str, list[str] | int] | None:
    """
    PowerShell から出力された "SYNC_FILES_DRY:..." 行を parse（複数実行に対応）
    
    例: 
    SYNC_FILES_DRY:ADDED=["file1.md","file2.json"]
    SYNC_FILES_DRY:UPDATED=["file3.md"]
    SYNC_FILES_DRY:DELETED=[]
    
    複数の robocopy 実行がある場合は全ファイルをマージ
    """
    import json
    
    result: dict[str, list[str] | int] = {
        'added': [],
        'updated': [],
        'deleted': [],
        'added_more': 0,
        'updated_more': 0,
        'deleted_more': 0,
    }
    
    def extend_from_json_line(bucket: str) -> None:
        pattern = rf"SYNC_FILES_DRY:{bucket.upper()}=(.+)"
        matches = re.findall(pattern, stdout)
        file_bucket = result[bucket]
        if not isinstance(file_bucket, list):
            return
        for match_str in matches:
            candidate = match_str.strip()
            try:
                files = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            if isinstance(files, list):
                file_bucket.extend(files)
            elif isinstance(files, str):
                file_bucket.append(files)

    extend_from_json_line("added")
    extend_from_json_line("updated")
    extend_from_json_line("deleted")
    
    # Parse overflow counts（合算）
    matches = re.findall(r'SYNC_FILES_OVERFLOW:ADDED_MORE=(\d+)', stdout)
    result['added_more'] = sum(int(m) for m in matches)
    
    matches = re.findall(r'SYNC_FILES_OVERFLOW:UPDATED_MORE=(\d+)', stdout)
    result['updated_more'] = sum(int(m) for m in matches)
    
    matches = re.findall(r'SYNC_FILES_OVERFLOW:DELETED_MORE=(\d+)', stdout)
    result['deleted_more'] = sum(int(m) for m in matches)
    
    # リストが空でも、オーバーフロー情報がある場合は結果を返す
    added_files = result["added"]
    updated_files = result["updated"]
    deleted_files = result["deleted"]
    added_more = result["added_more"]
    updated_more = result["updated_more"]
    deleted_more = result["deleted_more"]

    has_files = any(
        isinstance(files, list) and files
        for files in (added_files, updated_files, deleted_files)
    )
    has_overflow = any(
        isinstance(count, int) and count > 0
        for count in (added_more, updated_more, deleted_more)
    )
    return result if (has_files or has_overflow) else None


def normalize_path_to_relative(abs_path: str, base_path: str | None = None) -> str:
    r"""
    絶対パスを相対パスに正規化。Windows パス区切りを Unix スタイルに統一
    
    相対パスが渡された場合はそのまま返す。
    
    例: C:\Users\xxx\.copilot\skills\foo.md → skills/foo.md
    例: skills/foo.md → skills/foo.md
    """
    try:
        path_obj = Path(abs_path)
        
        # すでに相対パスの場合はそのまま返す
        if not path_obj.is_absolute():
            return str(abs_path).replace('\\', '/')
        
        if base_path:
            rel = path_obj.relative_to(base_path)
        else:
            # Fallback: .copilot 以降を抽出（大文字小文字を区別しない）
            lower_path = abs_path.lower().replace('\\', '/')
            copilot_idx = lower_path.find('.copilot')
            if copilot_idx >= 0:
                # ".copilot/" または ".copilot\" の次の位置から抽出
                start_idx = copilot_idx + 9  # len(".copilot/") = 9
                rel_part = abs_path[start_idx:]
                return rel_part.replace('\\', '/')
            else:
                # .copilot が見つからない場合は、ファイル名だけではなく末尾の部分を抽出
                # robocopy ログ形式は "path/to/file" で来るはずなので、そのまま返す
                return str(abs_path).replace('\\', '/')
        
        return str(rel).replace('\\', '/')
    except (ValueError, OSError):
        # パス正規化に失敗した場合はそのまま返す
        return str(abs_path).replace('\\', '/')


def format_file_details(files: dict[str, list[str] | int] | None, dry_run: bool = False) -> str:
    """
    ドライラン時のファイル詳細情報をフォーマット
    
    実行時は空文字列を返す（ファイル一覧は表示しない）
    オーバーフロー情報があれば「一覧取得に失敗したが N 件以上の変更あり」と表示
    """
    if not dry_run or not files:
        return ""
    
    lines: list[str] = []
    
    # Check if we have any overflow (file list unavailable but changes detected)
    added_more = files.get('added_more', 0)
    updated_more = files.get('updated_more', 0)
    deleted_more = files.get('deleted_more', 0)
    added_more_int = added_more if isinstance(added_more, int) else 0
    updated_more_int = updated_more if isinstance(updated_more, int) else 0
    deleted_more_int = deleted_more if isinstance(deleted_more, int) else 0
    
    has_overflow = added_more_int > 0 or updated_more_int > 0 or deleted_more_int > 0
    
    # 追加項目
    added = files.get('added')
    if added and isinstance(added, list) and len(added) > 0:
        lines.append("")
        lines.append("")
        lines.append(f"◆ 追加項目 ({len(added) + added_more_int} 個)")
        for file_path in added:
            rel_path = normalize_path_to_relative(file_path)
            lines.append(f"  {rel_path}")
        if added_more_int > 0:
            lines.append(f"  ... 残り {added_more_int} 個")
    elif added_more_int > 0:
        lines.append("")
        lines.append("")
        lines.append(f"◆ 追加項目 ({added_more_int} 個以上 / 一覧取得に失敗)")
    
    # 更新項目
    updated = files.get('updated')
    if updated and isinstance(updated, list) and len(updated) > 0:
        lines.append("")
        lines.append(f"◆ 更新項目 ({len(updated) + updated_more_int} 個)")
        for file_path in updated:
            rel_path = normalize_path_to_relative(file_path)
            lines.append(f"  {rel_path}")
        if updated_more_int > 0:
            lines.append(f"  ... 残り {updated_more_int} 個")
    elif updated_more_int > 0:
        lines.append("")
        lines.append(f"◆ 更新項目 ({updated_more_int} 個以上 / 一覧取得に失敗)")
    
    # 削除項目
    deleted = files.get('deleted')
    if deleted and isinstance(deleted, list) and len(deleted) > 0:
        lines.append("")
        lines.append(f"◆ 削除項目 ({len(deleted) + deleted_more_int} 個)")
        for file_path in deleted:
            rel_path = normalize_path_to_relative(file_path)
            lines.append(f"  {rel_path}")
        if deleted_more_int > 0:
            lines.append(f"  ... 残り {deleted_more_int} 個")
    elif deleted_more_int > 0:
        lines.append("")
        lines.append(f"◆ 削除項目 ({deleted_more_int} 個以上 / 一覧取得に失敗)")
    
    # すべて空でオーバーフロー情報もない場合のみ「変更項目なし」を表示
    added_count = len(added) if added and isinstance(added, list) else 0
    updated_count = len(updated) if updated and isinstance(updated, list) else 0
    deleted_count = len(deleted) if deleted and isinstance(deleted, list) else 0
    
    if added_count == 0 and updated_count == 0 and deleted_count == 0 and not has_overflow:
        lines.append("")
        lines.append("")
        lines.append("◆ 変更項目なし")
    
    return "\n".join(lines)


def format_sync_summary(stats: dict[str, int] | None, dry_run: bool = False, success: bool = False) -> str:
    """
    同期統計情報を非技術層向けにフォーマット
    
    - ドライラン: "✓ ドライラン確認: 追加 X 個 / 更新 Y 個 / 削除 Z 個"
    - 実行成功: "✓ 同期完了: 追加 X 個 / 更新 Y 個 / 削除 Z 個"
    """
    if not stats:
        return "同期結果が取得できませんでした"
    
    added, updated, deleted = stats['added'], stats['updated'], stats['deleted']
    summary = f"追加 {added} 個 / 更新 {updated} 個 / 削除 {deleted} 個"
    
    if dry_run:
        return f"✓ ドライラン確認: {summary}"
    elif success:
        return f"✓ 同期完了: {summary}"
    else:
        return "✗ 同期失敗"


def suggest_error_resolution(stderr: str) -> str:
    """
    stderr から一般的なエラーを検出し、ユーザー向け対処法を提示
    """
    stderr_lower = stderr.lower()
    if "access denied" in stderr_lower or "権限" in stderr:
        return "✗ 権限エラー — Admin 権限で再実行してください"
    elif "path" in stderr_lower or "見つかりません" in stderr:
        return "✗ パスエラー — パスが正しいか確認してください"
    elif "network" in stderr_lower or "ネットワーク" in stderr:
        return "✗ ネットワークエラー — インターネット接続を確認してください"
    else:
        return "✗ 同期失敗 — 詳細はログを確認してください"


def format_failure_details(result: CommandResult) -> str:
    lines: list[str] = []
    if result.stdout:
        lines.extend(("", "標準出力:", result.stdout))
    if result.stderr:
        lines.extend(("", "標準エラー:", result.stderr))
    return "\n".join(lines)


def format_command_result_improved(result: CommandResult, dry_run: bool = False, verbose_log: bool = False) -> str:
    """
    改善版: robocopy 生ログを人間が読める形に変換
    
    成功時は統計情報を表示、失敗時は対処法を提示
    ドライラン時はファイル詳細を追加表示
    """
    if not result.succeeded:
        message = suggest_error_resolution(f"{result.stdout}\n{result.stderr}")
        if verbose_log:
            message += format_failure_details(result)
        return message
    
    stats = parse_sync_stats(result.stdout)
    message = format_sync_summary(stats, dry_run=dry_run, success=True)
    
    # ドライラン時のみファイル詳細を追加
    if dry_run:
        files = parse_sync_files_dry(result.stdout)
        file_details = format_file_details(files, dry_run=True)
        message += file_details
    
    return message


def build_option_summary_improved(*, dry_run: bool, verbose_log: bool) -> str:
    """
    改善版: ドライラン/実行モードの説明を見やすく
    """
    lines = []
    if dry_run:
        lines.append("◆ ドライランモード")
        lines.append("このモードではファイルは実際に変更されません。何が同期されるか確認できます。")
    else:
        lines.append("◆ 実行モード")
        lines.append("確認後、同期内容が実際に反映されます。")
    
    lines.append("")
    lines.append("ホーム同期は Copilot instructions と repo bootstrap 資産だけを同期します。")
    lines.append("skills/、agents/、docs/ は plugin install / user-owned surface として触りません。")
    
    if verbose_log:
        lines.append("")
        lines.append("◆ 詳細ログ表示")
        lines.append("同期計画と適用対象の詳細を表示します。")
    
    return "\n".join(lines)


def build_option_summary(*, dry_run: bool, verbose_log: bool) -> str:
    lines = []
    if dry_run:
        lines.append("現在はドライランです。ファイルは変更せず、何が起こるかだけを確認します。")
    else:
        lines.append("現在は実行モードです。選んだ同期内容が実際に反映されます。")

    lines.append("通常同期です。Copilot instructions と repo bootstrap 資産だけを同期し、skills/、agents/、docs/ は plugin install / user-owned surface として触りません。")

    if verbose_log:
        lines.append("詳細ログを表示します。同期計画と適用対象の詳細を追加表示します。")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="既存の PowerShell を正本のまま呼び出す Python launcher（CLI モードのみ）。",
    )
    
    # グローバルフラグ（サブコマンド前）
    parser.add_argument("--mirror", action="store_true", help="互換オプションです。ホーム同期の managed directory は常に template 一致へ同期します。")
    parser.add_argument("--dry-run", action="store_true", help="書き込み前に差分だけ確認します。")
    parser.add_argument("--verbose-log", action="store_true", help="同期計画と適用対象の詳細を表示します。")
    parser.add_argument(
        "--interactive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="未指定時は対話可能な端末でのみプロンプトを表示します。--no-interactive で非対話実行を強制できます。",
    )
    
    subparsers = parser.add_subparsers(dest="command")

    home_parser = subparsers.add_parser("home", help="home-template/.copilot を $HOME/.copilot へ同期します。")
    # home サブコマンド用のフラグ（互換性のため）
    home_parser.add_argument("--mirror", action="store_true", help="互換オプションです。ホーム同期の managed directory は常に template 一致へ同期します。")
    home_parser.add_argument("--dry-run", action="store_true", help="書き込み前に差分だけ確認します。")
    home_parser.add_argument("--verbose-log", action="store_true", help="同期計画と適用対象の詳細を表示します。")
    home_parser.add_argument(
        "--interactive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="未指定時は対話可能な端末でのみプロンプトを表示します。--no-interactive で非対話実行を強制できます。",
    )

    repair_parser = subparsers.add_parser(
        "plugin-repair",
        help="happy-ai-life marketplace plugin を backup 後に再インストールします。",
    )
    repair_parser.add_argument(
        "--plugin",
        dest="plugins",
        action="append",
        choices=REPAIRABLE_PLUGINS,
        help="対象 plugin を限定します。未指定時は happy-core と happy-coding の両方を扱います。",
    )
    repair_parser.add_argument("--dry-run", action="store_true", help="backup / delete / reinstall の予定だけを表示します。")
    repair_parser.add_argument("--yes", action="store_true", help="確認プロンプトを省略して実行します。")
    repair_parser.add_argument(
        "--interactive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="未指定時は対話可能な端末でのみ確認プロンプトを表示します。--no-interactive で非対話実行を強制できます。",
    )

    return parser


def write_console_line(message: str, *, stream: TextIO | None = None) -> None:
    target = stream if stream is not None else sys.stdout
    encoding = target.encoding or locale.getpreferredencoding(False) or "utf-8"
    safe_message = message.encode(encoding, errors="replace").decode(encoding, errors="replace")
    target.write(f"{safe_message}\n")
    target.flush()


def stdin_is_interactive(stream: TextIO | None = None) -> bool:
    target = stream if stream is not None else sys.stdin
    isatty = getattr(target, "isatty", None)
    if not callable(isatty):
        return False
    return bool(isatty())


def prompt_sync_options() -> tuple[bool, bool]:
    """
    ホーム同期のオプションをインタラクティブに選択
    
    Returns:
        (dry_run, verbose_log) のタプル
    """
    dry_run = False
    verbose_log = False
    
    write_console_line("")
    write_console_line("◆ ホーム同期モード設定")
    write_console_line("")
    
    while True:
        write_console_line(f"1. ドライランモード: {'[ON] enabled' if dry_run else '[OFF] disabled'}")
        write_console_line(f"2. 詳細ログ表示: {'[ON] enabled' if verbose_log else '[OFF] disabled'}")
        write_console_line("")
        write_console_line("実行するには Enter キーを押してください。")
        write_console_line("設定を変更するには「1」または「2」を入力してください。")
        write_console_line("")

        choice = input("> ").strip()

        if choice == "":
            break
        elif choice == "1":
            dry_run = not dry_run
            write_console_line("")
        elif choice == "2":
            verbose_log = not verbose_log
            write_console_line("")
        else:
            write_console_line("無効な選択です。もう一度入力してください。")
            write_console_line("")

    write_console_line("")
    write_console_line(build_option_summary_improved(dry_run=dry_run, verbose_log=verbose_log))
    write_console_line("")

    return dry_run, verbose_log


def run_cli_interactive(namespace: argparse.Namespace, *, has_explicit_flags: bool = False) -> int:
    """
    CLI インタラクティブモード
    
    フラグが明示的に指定されていない場合、input() でユーザーに選択肢を提示する
    
    Args:
        namespace: argparse のパース結果
        has_explicit_flags: --dry-run や --verbose-log が明示的に指定されたか
    """
    if namespace.command == "home":
        interactive_override = getattr(namespace, "interactive", None)

        if interactive_override is False:
            dry_run = namespace.dry_run
            verbose_log = namespace.verbose_log
        elif has_explicit_flags and interactive_override is not True:
            dry_run = namespace.dry_run
            verbose_log = namespace.verbose_log
        elif stdin_is_interactive():
            try:
                dry_run, verbose_log = prompt_sync_options()
            except EOFError:
                dry_run = False
                verbose_log = False
        else:
            dry_run = False
            verbose_log = False

        result = run_home_sync(
            mirror=namespace.mirror,
            dry_run=dry_run,
            verbose_log=verbose_log,
        )
        message = format_command_result_improved(result, dry_run=dry_run, verbose_log=verbose_log)
    elif namespace.command == "plugin-repair":
        interactive_override = getattr(namespace, "interactive", None)
        result = run_plugin_repair(
            selected_plugins=namespace.plugins,
            dry_run=namespace.dry_run,
            assume_yes=namespace.yes,
            interactive=interactive_override,
        )
        message = result.stdout
    else:
        raise ValueError(f"未対応の CLI コマンドです: {namespace.command}")

    write_console_line(message)

    return result.returncode


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = list(argv) if argv is not None else None
    namespace = parser.parse_args(args)

    raw_args = args if args is not None else sys.argv[1:]
    has_explicit_flags = any(
        flag in raw_args
        for flag in ("--dry-run", "--verbose-log", "--interactive", "--no-interactive")
    )

    # デフォルトコマンド: サブコマンド省略時は "home" を使用
    if namespace.command is None:
        namespace.command = "home"
        namespace.mirror = False
        namespace.dry_run = False
        namespace.verbose_log = False

    return run_cli_interactive(namespace, has_explicit_flags=has_explicit_flags)
