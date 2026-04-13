from __future__ import annotations

import argparse
import locale
import os
import shutil
import subprocess
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText

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


def build_repo_sync_arguments(
    target_repo_path: Path,
    *,
    mirror: bool = False,
    dry_run: bool = False,
    verbose_log: bool = False,
) -> tuple[str, ...]:
    arguments = ["-TargetRepoPath", str(target_repo_path)]
    if mirror:
        arguments.append("-Mirror")
    if dry_run:
        arguments.append("-DryRun")
    if verbose_log:
        arguments.append("-VerboseLog")
    return tuple(arguments)


def build_install_git_hooks_arguments(target_repo_path: Path) -> tuple[str, ...]:
    return ("-TargetRepoPath", str(target_repo_path))


def normalize_user_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


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


def run_repo_sync(
    target_repo_path: Path,
    *,
    mirror: bool = False,
    dry_run: bool = False,
    verbose_log: bool = False,
) -> CommandResult:
    normalized_target_repo_path = normalize_user_path(target_repo_path)
    return run_script(
        "sync-to-repo.ps1",
        build_repo_sync_arguments(
            normalized_target_repo_path,
            mirror=mirror,
            dry_run=dry_run,
            verbose_log=verbose_log,
        ),
        label="リポジトリ同期",
    )


def run_install_git_hooks(target_repo_path: Path) -> CommandResult:
    normalized_target_repo_path = normalize_user_path(target_repo_path)
    return run_script(
        "install-git-hooks.ps1",
        build_install_git_hooks_arguments(normalized_target_repo_path),
        label="Git hooks インストール",
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


def build_option_summary(*, dry_run: bool, mirror: bool, verbose_log: bool) -> str:
    lines = []
    if dry_run:
        lines.append("現在はドライランです。ファイルは変更せず、何が起こるかだけを確認します。")
    else:
        lines.append("現在は実行モードです。選んだ同期内容が実際に反映されます。")

    if mirror:
        if dry_run:
            lines.append("ミラー指定の影響を確認します。")
            lines.append("補足: リポジトリ同期ではミラー削除が有効です。同期先だけのファイルやディレクトリは完全削除されます。ホーム同期は whitelist copy のため、--mirror を指定しても削除しません。")
        else:
            lines.append("補足: リポジトリ同期ではミラー削除が有効です。同期先だけのファイルやディレクトリは完全削除されます。ホーム同期は whitelist copy のため、--mirror を指定しても削除しません。")
    else:
        lines.append("通常同期です。ホーム同期は tracked な template 項目だけをコピーし、既存の HOME 側ファイルは保持します。")

    if verbose_log:
        lines.append("詳細ログを表示します。robocopy の出力が増えるため、実行内容を追いやすくなります。")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="既存の PowerShell を正本のまま呼び出す Python launcher。",
    )
    subparsers = parser.add_subparsers(dest="command")

    gui_parser = subparsers.add_parser("gui", help="GUI ランチャーを開きます。")
    gui_parser.set_defaults(command="gui")

    home_parser = subparsers.add_parser("home", help="home-template/.copilot を $HOME/.copilot へ同期します。")
    home_parser.add_argument("--mirror", action="store_true", help="互換オプションです。ホーム同期では無視されます。")
    home_parser.add_argument("--dry-run", action="store_true", help="書き込み前に差分だけ確認します。")
    home_parser.add_argument("--verbose-log", action="store_true", help="robocopy の詳細ログを表示します。")

    repo_parser = subparsers.add_parser("repo", help="repo-template/.github を対象リポジトリへ同期します。")
    repo_parser.add_argument("target_repo_path", type=Path, help="対象リポジトリのパス。")
    repo_parser.add_argument("--mirror", action="store_true", help="同期先をミラーします。")
    repo_parser.add_argument("--dry-run", action="store_true", help="書き込み前に差分だけ確認します。")
    repo_parser.add_argument("--verbose-log", action="store_true", help="robocopy の詳細ログを表示します。")

    hooks_parser = subparsers.add_parser("hooks", help="対象リポジトリへ Git hooks をインストールします。")
    hooks_parser.add_argument("target_repo_path", type=Path, help="対象リポジトリのパス。")

    return parser


_MIRROR_CONFIRM_PROMPT = (
    "警告: リポジトリのミラー同期では同期先にだけあるファイル・ディレクトリが\n"
    "完全削除されます（ゴミ箱には入りません）。\n"
    "続けるには 'yes' と入力してください: "
)


def confirm_mirror_sync() -> bool:
    """Return True if the user explicitly confirms mirror sync."""
    try:
        answer = input(_MIRROR_CONFIRM_PROMPT).strip().lower()
        return answer == "yes"
    except EOFError:
        return False


def run_cli(namespace: argparse.Namespace) -> int:
    if namespace.command == "home":
        result = run_home_sync(
            mirror=namespace.mirror,
            dry_run=namespace.dry_run,
            verbose_log=namespace.verbose_log,
        )
    elif namespace.command == "repo":
        if namespace.mirror and not namespace.dry_run:
            if not confirm_mirror_sync():
                print("中断しました。")
                return 1
        result = run_repo_sync(
            namespace.target_repo_path,
            mirror=namespace.mirror,
            dry_run=namespace.dry_run,
            verbose_log=namespace.verbose_log,
        )
    elif namespace.command == "hooks":
        result = run_install_git_hooks(namespace.target_repo_path)
    else:
        raise ValueError(f"未対応の CLI コマンドです: {namespace.command}")

    print(format_command_result(result))
    return result.returncode


class HappyEnvGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("happy env ランチャー")
        self.root.minsize(760, 480)
        self.dry_run_var = tk.BooleanVar(value=True)
        self.mirror_var = tk.BooleanVar(value=False)
        self.verbose_log_var = tk.BooleanVar(value=False)
        self.option_summary_var = tk.StringVar()
        self._is_running = False
        self._action_buttons: list[ttk.Button] = []
        self.main_frame: ttk.Frame | None = None
        self._build_layout()
        self._update_option_summary()

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        self.main_frame = frame
        frame.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(4, weight=1)

        ttk.Label(
            frame,
            text="既存の PowerShell スクリプトを app.py から実行します。",
        ).grid(row=0, column=0, sticky="w")

        options = ttk.Frame(frame)
        options.grid(row=1, column=0, sticky="w", pady=(12, 12))
        ttk.Checkbutton(
            options,
            text="ドライラン（変更せず、何が起こるかだけ確認）",
            variable=self.dry_run_var,
            command=self._update_option_summary,
        ).grid(row=0, column=0, padx=(0, 12))
        ttk.Checkbutton(
            options,
            text="ミラー同期（リポジトリ同期では同期先だけのファイルやディレクトリを削除）",
            variable=self.mirror_var,
            command=self._update_option_summary,
        ).grid(row=1, column=0, padx=(0, 12), pady=(6, 0), sticky="w")
        ttk.Checkbutton(
            options,
            text="詳細ログ（robocopy の出力を詳しく表示）",
            variable=self.verbose_log_var,
            command=self._update_option_summary,
        ).grid(row=2, column=0, padx=(0, 12), pady=(6, 0), sticky="w")

        ttk.Label(
            frame,
            textvariable=self.option_summary_var,
            wraplength=680,
            justify="left",
            foreground="#8B0000",
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))

        actions = ttk.Frame(frame)
        actions.grid(row=3, column=0, sticky="w", pady=(0, 12))
        self._register_action_button(actions, "ホームへ同期", self._run_home_sync).grid(row=0, column=0, padx=(0, 8))
        self._register_action_button(actions, "リポジトリへ同期...", self._run_repo_sync).grid(row=0, column=1, padx=(0, 8))
        self._register_action_button(actions, "Git hooks をインストール...", self._run_install_hooks).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(actions, text="ログをクリア", command=self._clear_log).grid(row=0, column=3)

        self.output = ScrolledText(frame, wrap="word", height=16)
        self.output.grid(row=4, column=0, sticky="nsew")
        self.output.insert(
            "end",
            "準備完了。ホーム同期は tracked な template 項目だけをコピーし、mcp-config.json など user-owned file は保護します。\n",
        )
        self.output.configure(state="disabled")

    def _register_action_button(self, parent: ttk.Frame, text: str, command: Callable[[], None]) -> ttk.Button:
        button = ttk.Button(parent, text=text, command=command)
        self._action_buttons.append(button)
        return button

    def _set_running(self, value: bool) -> None:
        self._is_running = value
        state = "disabled" if value else "normal"
        for button in self._action_buttons:
            button.configure(state=state)

    def _append_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", f"{text}\n\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _clear_log(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _update_option_summary(self) -> None:
        self.option_summary_var.set(
            build_option_summary(
                dry_run=self.dry_run_var.get(),
                mirror=self.mirror_var.get(),
                verbose_log=self.verbose_log_var.get(),
            )
        )

    def _run_in_background(self, runner: Callable[[], CommandResult]) -> None:
        if self._is_running:
            self._append_output("別の処理を実行中です。")
            return

        self._set_running(True)
        self._append_output("実行中...")

        def worker() -> None:
            try:
                result = runner()
                message = format_command_result(result)
            except Exception as exc:  # pragma: no cover - defensive boundary to keep GUI alive.
                message = f"実行前に処理が失敗しました:\n{exc}"
            finally:
                self.root.after(0, lambda: self._finish_run(message))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _finish_run(self, message: str) -> None:
        self._append_output(message)
        self._set_running(False)

    def _run_home_sync(self) -> None:
        self._run_in_background(
            lambda: run_home_sync(
                mirror=self.mirror_var.get(),
                dry_run=self.dry_run_var.get(),
                verbose_log=self.verbose_log_var.get(),
            )
        )

    def _select_directory(self) -> Path | None:
        selected = filedialog.askdirectory(initialdir=str(ROOT_DIR), mustexist=True)
        if not selected:
            self._append_output("操作をキャンセルしました。")
            return None
        return Path(selected)

    def _run_repo_sync(self) -> None:
        target_repo_path = self._select_directory()
        if target_repo_path is None:
            return

        if self.mirror_var.get() and not self.dry_run_var.get():
            self._append_output("警告: リポジトリのミラー同期では、同期先だけにあるファイルやディレクトリは削除されます。")
            self._append_output("robocopy の '*EXTRA' は同期先だけにある項目を表します。本番の /MIR では削除対象です。")

        self._run_in_background(
            lambda: run_repo_sync(
                target_repo_path,
                mirror=self.mirror_var.get(),
                dry_run=self.dry_run_var.get(),
                verbose_log=self.verbose_log_var.get(),
            )
        )

    def _run_install_hooks(self) -> None:
        target_repo_path = self._select_directory()
        if target_repo_path is None:
            return

        self._run_in_background(lambda: run_install_git_hooks(target_repo_path))


def launch_gui() -> int:
    root = tk.Tk()
    HappyEnvGui(root)
    root.mainloop()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = list(argv) if argv is not None else None
    namespace = parser.parse_args(args)

    if namespace.command in {None, "gui"}:
        return launch_gui()

    return run_cli(namespace)
