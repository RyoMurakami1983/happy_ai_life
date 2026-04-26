from __future__ import annotations

import argparse
import io
import locale
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
HOME_COPILOT_DIR = Path.home() / ".copilot"
MCP_CONFIG_FILENAME = "mcp-config.json"
MCP_CONFIG_SAMPLE_FILENAME = "mcp-config.sample.json"
ALLOW_POLICY_BYPASS_ENV = "HAPPY_ENV_ALLOW_POLICY_BYPASS"


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



def resolve_powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved is not None:
            return resolved

    raise RuntimeError("PowerShell が見つかりません。インストール後に再実行してください。")


def build_script_command(script_name: str, arguments: Sequence[str]) -> tuple[str, ...]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

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



def build_mcp_config_notes(destination_path: Path = HOME_COPILOT_DIR) -> tuple[str, ...]:
    sample_path = destination_path / MCP_CONFIG_SAMPLE_FILENAME
    live_path = destination_path / MCP_CONFIG_FILENAME
    if live_path.exists() or not sample_path.exists():
        return ()

    return (
        "MCP 設定はまだ初期化されていません。",
        f"'{destination_path}' 配下で '{sample_path.name}' を '{live_path.name}' にコピーしてください。",
        "API キーなどの secret は user-owned な live file にだけ設定し、ホーム同期ではそのファイルを上書きしません。",
    )


def decode_process_output(data: bytes) -> str:
    if not data:
        return ""

    encoding = locale.getpreferredencoding(False)
    return data.decode(encoding, errors="replace")


def run_script(script_name: str, arguments: Sequence[str], *, label: str, notes: Sequence[str] = ()) -> CommandResult:
    command = build_script_command(script_name, (*arguments, "-SourceRoot", str(ROOT_DIR)))
    completed = subprocess.run(
        command,
        cwd=ROOT_DIR,
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
    return run_script(
        "sync-to-home.ps1",
        build_home_sync_arguments(mirror=mirror, dry_run=dry_run, verbose_log=verbose_log),
        label="ホーム同期",
        notes=build_mcp_config_notes(),
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
    
    # Parse added files（全行をマージ）
    matches = re.findall(r'SYNC_FILES_DRY:ADDED=(\[.*?\])', stdout, re.DOTALL)
    for match_str in matches:
        try:
            files = json.loads(match_str)
            if isinstance(files, list):
                result['added'].extend(files)
        except json.JSONDecodeError:
            pass
    
    # Parse updated files（全行をマージ）
    matches = re.findall(r'SYNC_FILES_DRY:UPDATED=(\[.*?\])', stdout, re.DOTALL)
    for match_str in matches:
        try:
            files = json.loads(match_str)
            if isinstance(files, list):
                result['updated'].extend(files)
        except json.JSONDecodeError:
            pass
    
    # Parse deleted files（全行をマージ）
    matches = re.findall(r'SYNC_FILES_DRY:DELETED=(\[.*?\])', stdout, re.DOTALL)
    for match_str in matches:
        try:
            files = json.loads(match_str)
            if isinstance(files, list):
                result['deleted'].extend(files)
        except json.JSONDecodeError:
            pass
    
    # Parse overflow counts（合算）
    matches = re.findall(r'SYNC_FILES_OVERFLOW:ADDED_MORE=(\d+)', stdout)
    result['added_more'] = sum(int(m) for m in matches)
    
    matches = re.findall(r'SYNC_FILES_OVERFLOW:UPDATED_MORE=(\d+)', stdout)
    result['updated_more'] = sum(int(m) for m in matches)
    
    matches = re.findall(r'SYNC_FILES_OVERFLOW:DELETED_MORE=(\d+)', stdout)
    result['deleted_more'] = sum(int(m) for m in matches)
    
    # リストが空でも、オーバーフロー情報がある場合は結果を返す
    has_files = any(result[k] for k in ['added', 'updated', 'deleted'])
    has_overflow = any(result[k] > 0 for k in ['added_more', 'updated_more', 'deleted_more'])
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
    
    # 追加ファイル
    added = files.get('added')
    if added and isinstance(added, list) and len(added) > 0:
        lines.append("")
        lines.append("")
        lines.append(f"◆ 追加ファイル ({len(added) + added_more_int} 個)")
        for file_path in added:
            rel_path = normalize_path_to_relative(file_path)
            lines.append(f"  {rel_path}")
        if added_more_int > 0:
            lines.append(f"  ... 残り {added_more_int} 個")
    elif added_more_int > 0:
        lines.append("")
        lines.append("")
        lines.append(f"◆ 追加ファイル ({added_more_int} 個以上 / 一覧取得に失敗)")
    
    # 更新ファイル
    updated = files.get('updated')
    if updated and isinstance(updated, list) and len(updated) > 0:
        lines.append("")
        lines.append(f"◆ 更新ファイル ({len(updated) + updated_more_int} 個)")
        for file_path in updated:
            rel_path = normalize_path_to_relative(file_path)
            lines.append(f"  {rel_path}")
        if updated_more_int > 0:
            lines.append(f"  ... 残り {updated_more_int} 個")
    elif updated_more_int > 0:
        lines.append("")
        lines.append(f"◆ 更新ファイル ({updated_more_int} 個以上 / 一覧取得に失敗)")
    
    # 削除ファイル
    deleted = files.get('deleted')
    if deleted and isinstance(deleted, list) and len(deleted) > 0:
        lines.append("")
        lines.append(f"◆ 削除ファイル ({len(deleted) + deleted_more_int} 個)")
        for file_path in deleted:
            rel_path = normalize_path_to_relative(file_path)
            lines.append(f"  {rel_path}")
        if deleted_more_int > 0:
            lines.append(f"  ... 残り {deleted_more_int} 個")
    elif deleted_more_int > 0:
        lines.append("")
        lines.append(f"◆ 削除ファイル ({deleted_more_int} 個以上 / 一覧取得に失敗)")
    
    # すべて空でオーバーフロー情報もない場合のみ「変更ファイルなし」を表示
    added_count = len(added) if added and isinstance(added, list) else 0
    updated_count = len(updated) if updated and isinstance(updated, list) else 0
    deleted_count = len(deleted) if deleted and isinstance(deleted, list) else 0
    
    if added_count == 0 and updated_count == 0 and deleted_count == 0 and not has_overflow:
        lines.append("")
        lines.append("")
        lines.append("◆ 変更ファイルなし")
    
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


def format_command_result_improved(result: CommandResult, dry_run: bool = False) -> str:
    """
    改善版: robocopy 生ログを人間が読める形に変換
    
    成功時は統計情報を表示、失敗時は対処法を提示
    ドライラン時はファイル詳細を追加表示
    """
    if not result.succeeded:
        return suggest_error_resolution(result.stderr)
    
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
    lines.append("ホーム同期は skills/、agents/、repo-template/、.github/hooks/ を template 一致へ同期します。")
    lines.append("mcp-config.json や docs/furikaeri など user-owned 領域は保護されます。")
    
    if verbose_log:
        lines.append("")
        lines.append("◆ 詳細ログ表示")
        lines.append("同期の詳細な実行内容を表示します。")
    
    return "\n".join(lines)


def build_option_summary(*, dry_run: bool, verbose_log: bool) -> str:
    lines = []
    if dry_run:
        lines.append("現在はドライランです。ファイルは変更せず、何が起こるかだけを確認します。")
    else:
        lines.append("現在は実行モードです。選んだ同期内容が実際に反映されます。")

    lines.append("通常同期です。ホーム同期は skills/、agents/、repo-template/、.github/hooks/ を template 一致へ同期し、docs/furikaeri と user-owned file は保持します。")

    if verbose_log:
        lines.append("詳細ログを表示します。robocopy の出力が増えるため、実行内容を追いやすくなります。")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="既存の PowerShell を正本のまま呼び出す Python launcher（CLI モードのみ）。",
    )
    subparsers = parser.add_subparsers(dest="command")

    home_parser = subparsers.add_parser("home", help="home-template/.copilot を $HOME/.copilot へ同期します。")
    home_parser.add_argument("--mirror", action="store_true", help="互換オプションです。ホーム同期の managed directory は常に template 一致へ同期します。")
    home_parser.add_argument("--dry-run", action="store_true", help="書き込み前に差分だけ確認します。")
    home_parser.add_argument("--verbose-log", action="store_true", help="robocopy の詳細ログを表示します。")

    return parser


def prompt_sync_options() -> tuple[bool, bool]:
    """
    ホーム同期のオプションをインタラクティブに選択
    
    Returns:
        (dry_run, verbose_log) のタプル
    """
    dry_run = True
    verbose_log = False
    
    print("\n◆ ホーム同期モード設定")
    print()
    
    while True:
        print(f"1. ドライランモード: {'✓ enabled' if dry_run else '✗ disabled'}")
        print(f"2. 詳細ログ表示: {'✓ enabled' if verbose_log else '✗ disabled'}")
        print()
        print("実行するには Enter キーを押してください。")
        print("設定を変更するには「1」または「2」を入力してください。")
        print()
        
        choice = input("> ").strip()
        
        if choice == "":
            # Enter キーで実行
            break
        elif choice == "1":
            dry_run = not dry_run
            print()
        elif choice == "2":
            verbose_log = not verbose_log
            print()
        else:
            print("無効な選択です。もう一度入力してください。")
            print()
    
    print()
    print(build_option_summary_improved(dry_run=dry_run, verbose_log=verbose_log))
    print()
    
    return dry_run, verbose_log


def run_cli_interactive(namespace: argparse.Namespace) -> int:
    """
    CLI インタラクティブモード
    
    --dry-run や --verbose-log が指定されていない場合、
    input() でユーザーに選択肢を提示する
    """
    if namespace.command == "home":
        # フラグが明示的に指定されていない場合はインタラクティブモードに入る
        # argparse の仕様上、指定なしは False/action="store_true" なら False
        if not namespace.dry_run and not namespace.verbose_log:
            dry_run, verbose_log = prompt_sync_options()
        else:
            dry_run = namespace.dry_run
            verbose_log = namespace.verbose_log
        
        result = run_home_sync(
            mirror=namespace.mirror,
            dry_run=dry_run,
            verbose_log=verbose_log,
        )
        message = format_command_result_improved(result, dry_run=dry_run)
    else:
        raise ValueError(f"未対応の CLI コマンドです: {namespace.command}")
    
    # Print with UTF-8 encoding to handle Unicode characters like ✓
    # Use sys.stdout.buffer to write bytes directly, avoiding encoding issues
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(message.encode('utf-8'))
        sys.stdout.buffer.write(b'\n')
    else:
        print(message)  # Fallback for environments without buffer
    
    return result.returncode


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = list(argv) if argv is not None else None
    namespace = parser.parse_args(args)

    # デフォルトコマンド: サブコマンド省略時は "home" を使用
    if namespace.command is None:
        namespace.command = "home"
        namespace.mirror = False
        namespace.dry_run = False
        namespace.verbose_log = False

    return run_cli_interactive(namespace)
