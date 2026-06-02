from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MANAGED_HOME_HOOK_ID = "happy-ai-life-safety-guard"
MANAGED_HOME_HOOK_EVENTS = ("preToolUse", "permissionRequest")
ALLOW_POLICY_BYPASS_ENV = "HAPPY_ENV_ALLOW_POLICY_BYPASS"
LEGACY_HOME_HOOK_RELATIVE_FILES = (
    "session-continuity.json",
    "safety-guard.json",
    "scripts/guard_pre_tool.ps1",
    "scripts/guard_pre_tool.sh",
    "scripts/session-end.js",
    "scripts/session-start.js",
    "scripts/lib/decision-validation.js",
    "scripts/lib/session-utils.js",
)


@dataclass(frozen=True)
class FileAction:
    kind: str
    destination: Path
    source: Path | None = None
    content: str | None = None


@dataclass
class SyncPlan:
    actions: list[FileAction] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    mirror_mode: bool = False
    destination_root: Path | None = None


@dataclass(frozen=True)
class ConfigJsonDocument:
    preamble: str
    content: dict[str, Any]


def write_line(message: str = "", *, stream: Any = sys.stdout) -> None:
    stream.write(f"{message}\n")
    stream.flush()


def warn(message: str) -> None:
    write_line(f"WARNING: {message}", stream=sys.stderr)


def resolve_home_template_root(source_root: Path, template_path: str) -> Path:
    nested_template_path = (source_root / template_path).resolve()
    if nested_template_path.exists():
        return nested_template_path

    if (source_root / "copilot-instructions.md").exists():
        return source_root

    raise FileNotFoundError(
        f"Home template root not found. SourceRoot={source_root} TemplateRelativePath={template_path}"
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path) -> dict[Path, Path]:
    if not root.exists():
        return {}

    return {
        path.relative_to(root): path
        for path in root.rglob("*")
        if path.is_file()
    }


def normalize_preview_path(root_prefix: str, relative_path: Path | str) -> str:
    relative = str(relative_path).replace("\\", "/")
    if not root_prefix:
        return relative
    if not relative:
        return root_prefix.replace("\\", "/")
    return f"{root_prefix.replace('\\', '/').rstrip('/')}/{relative.lstrip('/')}"


def get_directory_sync_plan(
    *,
    source: Path,
    destination: Path,
    preview_root: str,
    mirror_mode: bool,
) -> SyncPlan:
    if not source.exists():
        raise FileNotFoundError(f"Source path not found: {source}")

    source_files = collect_files(source)
    destination_files = collect_files(destination)
    plan = SyncPlan(mirror_mode=mirror_mode, destination_root=destination)

    for relative_path in sorted(source_files):
        source_file = source_files[relative_path]
        destination_file = destination / relative_path
        preview_path = normalize_preview_path(preview_root, relative_path)
        if relative_path not in destination_files:
            plan.added.append(preview_path)
            plan.actions.append(FileAction(kind="copy-file", source=source_file, destination=destination_file))
            continue

        if file_sha256(source_file) != file_sha256(destination_files[relative_path]):
            plan.updated.append(preview_path)
            plan.actions.append(FileAction(kind="copy-file", source=source_file, destination=destination_file))

    if mirror_mode:
        for relative_path in sorted(destination_files):
            if relative_path in source_files:
                continue
            preview_path = normalize_preview_path(preview_root, relative_path)
            plan.deleted.append(preview_path)
            plan.actions.append(FileAction(kind="delete-path", destination=destination / relative_path))

    return plan


def get_tracked_file_plan(*, source: Path, destination: Path, preview_path: str) -> SyncPlan:
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    plan = SyncPlan(destination_root=destination.parent)
    if not destination.exists():
        plan.added.append(preview_path)
        plan.actions.append(FileAction(kind="copy-file", source=source, destination=destination))
        return plan

    if file_sha256(source) != file_sha256(destination):
        plan.updated.append(preview_path)
        plan.actions.append(FileAction(kind="copy-file", source=source, destination=destination))

    return plan


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_comment_prefixed_config_json(raw: str, *, config_path: Path) -> ConfigJsonDocument:
    if not raw.strip():
        return ConfigJsonDocument(preamble="", content={})

    lines = raw.splitlines(keepends=True)
    preamble_lines: list[str] = []
    body_start_index = 0
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("//") or not stripped.strip():
            preamble_lines.append(line)
            continue
        body_start_index = index
        break
    else:
        return ConfigJsonDocument(preamble=raw, content={})

    body = "".join(lines[body_start_index:])
    try:
        content = json.loads(body)
    except json.JSONDecodeError as exc:
        warn(
            "Skipping managed enterprise/global guard update in config.json because the existing file "
            f"contains unsupported JSON content: {config_path}. Error: {exc}"
        )
        raise

    if not isinstance(content, dict):
        warn(
            "Skipping managed enterprise/global guard update in config.json because the existing file "
            f"does not contain a JSON object at the top level: {config_path}."
        )
        raise ValueError("config.json top-level value must be an object")

    return ConfigJsonDocument(preamble="".join(preamble_lines), content=content)


def render_comment_prefixed_config_json(*, preamble: str, content: dict[str, Any]) -> str:
    rendered_body = json.dumps(content, ensure_ascii=False, indent=2) + "\n"
    if not preamble:
        return rendered_body
    if preamble.endswith(("\n", "\r")):
        return f"{preamble}{rendered_body}"
    return f"{preamble}\n{rendered_body}"


def normalize_hooks_map(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    hooks = config.get("hooks")
    if hooks is None:
        hooks = {}
        config["hooks"] = hooks
        return hooks

    if isinstance(hooks, dict):
        return hooks

    warn(
        "Replacing unsupported hooks value in config.json with an empty object before updating managed "
        f"home guard entries: {config_path}"
    )
    hooks = {}
    config["hooks"] = hooks
    return hooks


def backup_existing_path(existing_path: Path, *, destination_root: Path, archive_root: Path) -> None:
    if not existing_path.exists():
        return

    archive_path = archive_root / existing_path.relative_to(destination_root)
    if archive_path.exists():
        if archive_path.is_dir():
            shutil.rmtree(archive_path)
        else:
            archive_path.unlink()

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if existing_path.is_dir():
        shutil.copytree(existing_path, archive_path)
    else:
        shutil.copy2(existing_path, archive_path)


def managed_powershell_hook_command(script_path: str) -> str:
    if os.getenv(ALLOW_POLICY_BYPASS_ENV) == "1":
        return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{script_path}"'

    return (
        "if ($PSVersionTable.PSEdition -eq 'Core') "
        f"{{ & \"{script_path}\" }} "
        f"elseif (Get-Command pwsh -ErrorAction SilentlyContinue) {{ & pwsh -NoProfile -File \"{script_path}\" }} "
        f"else {{ & \"{script_path}\" }}"
    )


def managed_home_hook_entry(*, powershell_script_path: str, bash_script_path: str | None, event_name: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "type": "command",
        "powershell": managed_powershell_hook_command(powershell_script_path),
        "cwd": ".",
        "timeoutSec": 10,
        "env": {
            "HAPPY_AI_LIFE_HOOK_ID": MANAGED_HOME_HOOK_ID,
            "HAPPY_AI_LIFE_HOOK_EVENT": event_name,
        },
    }

    if bash_script_path:
        entry["bash"] = f'bash "{bash_script_path}"'

    return entry


def get_home_config_hook_plan(config_path: Path, *, powershell_script_path: str, bash_script_path: str) -> SyncPlan:
    config_exists = config_path.exists()
    original_stable_json: str | None = None
    preamble = ""
    if config_exists:
        raw = config_path.read_text(encoding="utf-8")
        try:
            parsed_document = parse_comment_prefixed_config_json(raw, config_path=config_path)
        except (ValueError, json.JSONDecodeError):
            return SyncPlan(destination_root=config_path.parent)

        preamble = parsed_document.preamble
        config = parsed_document.content
        original_stable_json = stable_json(config)
    else:
        config = {}

    hooks = normalize_hooks_map(config, config_path=config_path)
    for event_name in MANAGED_HOME_HOOK_EVENTS:
        existing_entries = hooks.get(event_name, [])
        if not isinstance(existing_entries, list):
            existing_entries = [existing_entries]

        preserved_entries = []
        for entry in existing_entries:
            if not isinstance(entry, dict):
                preserved_entries.append(entry)
                continue
            entry_id = (
                entry.get("env", {}).get("HAPPY_AI_LIFE_HOOK_ID")
                if isinstance(entry.get("env"), dict)
                else None
            )
            if entry_id != MANAGED_HOME_HOOK_ID:
                preserved_entries.append(entry)

        preserved_entries.append(
            managed_home_hook_entry(
                powershell_script_path=powershell_script_path,
                bash_script_path=bash_script_path,
                event_name=event_name,
            )
        )
        hooks[event_name] = preserved_entries

    desired_content = render_comment_prefixed_config_json(preamble=preamble, content=config)
    desired_stable_json = stable_json(config)
    plan = SyncPlan(destination_root=config_path.parent)
    if not config_exists:
        plan.added.append("config.json")
        plan.actions.append(FileAction(kind="write-text", destination=config_path, content=desired_content))
    elif original_stable_json != desired_stable_json:
        plan.updated.append("config.json")
        plan.actions.append(FileAction(kind="write-text", destination=config_path, content=desired_content))
    return plan


def get_home_hooks_safety_guard_plan(
    hooks_root: Path,
    *,
    powershell_script_path: str,
    bash_script_path: str | None,
) -> SyncPlan:
    destination = hooks_root / "safety-guard.json"
    document = {
        "version": 1,
        "hooks": {
            "preToolUse": [
                managed_home_hook_entry(
                    powershell_script_path=powershell_script_path,
                    bash_script_path=bash_script_path,
                    event_name="preToolUse",
                )
            ],
            "permissionRequest": [
                managed_home_hook_entry(
                    powershell_script_path=powershell_script_path,
                    bash_script_path=bash_script_path,
                    event_name="permissionRequest",
                )
            ],
        },
    }

    desired_text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    desired_stable = stable_json(document)

    plan = SyncPlan(destination_root=hooks_root)
    if not destination.exists():
        plan.added.append("hooks/safety-guard.json")
        plan.actions.append(FileAction(kind="write-text", destination=destination, content=desired_text))
        return plan

    try:
        existing = json.loads(destination.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        existing = None

    if stable_json(existing) != desired_stable:
        plan.updated.append("hooks/safety-guard.json")
        plan.actions.append(FileAction(kind="write-text", destination=destination, content=desired_text))

    return plan


def get_home_hooks_session_continuity_cleanup_plan(hooks_root: Path) -> SyncPlan:
    relative_files = (
        "session-continuity.json",
        "scripts/session-end.js",
        "scripts/session-start.js",
        "scripts/lib/decision-validation.js",
        "scripts/lib/session-utils.js",
    )

    to_delete = [hooks_root / relative for relative in relative_files if (hooks_root / relative).exists()]
    plan = SyncPlan(destination_root=hooks_root)
    if not to_delete:
        return plan

    plan.deleted.append("hooks/session-continuity.json and scripts")
    for path in to_delete:
        plan.actions.append(FileAction(kind="delete-path", destination=path))

    return plan


def ensure_parent_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def invoke_file_action(action: FileAction) -> None:
    if action.kind == "copy-file":
        if action.source is None:
            raise ValueError("copy-file action requires source")
        ensure_parent_directory(action.destination)
        shutil.copy2(action.source, action.destination)
        return

    if action.kind == "write-text":
        if action.content is None:
            raise ValueError("write-text action requires content")
        ensure_parent_directory(action.destination)
        action.destination.write_text(action.content, encoding="utf-8")
        return

    if action.kind == "delete-path":
        if action.destination.is_dir():
            shutil.rmtree(action.destination)
        elif action.destination.exists():
            action.destination.unlink()
        return

    raise ValueError(f"Unsupported action kind: {action.kind}")


def remove_empty_directories(root: Path) -> None:
    if not root.exists():
        return

    for directory in sorted((path for path in root.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            continue


def write_sync_summary(*, added: int, updated: int, deleted: int, dry_run: bool) -> None:
    summary = f"追加 {added} 個 / 更新 {updated} 個 / 削除 {deleted} 個"
    write_line("")
    if dry_run:
        write_line(f"✓ ドライラン確認: {summary}")
    else:
        write_line(f"✓ 同期完了: {summary}")


def write_sync_markers(preview_state: SyncPlan, *, dry_run: bool) -> None:
    added = preview_state.added
    updated = preview_state.updated
    deleted = preview_state.deleted
    write_line(f"SYNC_STATS:ADDED={len(added)},UPDATED={len(updated)},DELETED={len(deleted)}")

    if not dry_run:
        return

    write_line(f"SYNC_FILES_DRY:ADDED={json.dumps(added[:20], ensure_ascii=False, separators=(',', ':'))}")
    write_line(f"SYNC_FILES_DRY:UPDATED={json.dumps(updated[:20], ensure_ascii=False, separators=(',', ':'))}")
    write_line(f"SYNC_FILES_DRY:DELETED={json.dumps(deleted[:20], ensure_ascii=False, separators=(',', ':'))}")

    if len(added) > 20:
        write_line(f"SYNC_FILES_OVERFLOW:ADDED_MORE={len(added) - 20}")
    if len(updated) > 20:
        write_line(f"SYNC_FILES_OVERFLOW:UPDATED_MORE={len(updated) - 20}")
    if len(deleted) > 20:
        write_line(f"SYNC_FILES_OVERFLOW:DELETED_MORE={len(deleted) - 20}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Linux/WSL2 home sync implementation.")
    parser.add_argument("--SourceRoot", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--TemplateRelativePath", default="home-template/.copilot")
    parser.add_argument("--DestinationPath", default=str(Path.home() / ".copilot"))
    parser.add_argument("--ArchiveRoot", default=str(Path.home() / "copilot_archives"))
    parser.add_argument("--Mirror", action="store_true")
    parser.add_argument("--DryRun", action="store_true")
    parser.add_argument("--VerboseLog", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source_root = Path(args.SourceRoot).resolve()
    destination_path = Path(args.DestinationPath).resolve()
    archive_root = Path(args.ArchiveRoot).resolve()
    template_root = resolve_home_template_root(source_root, args.TemplateRelativePath)

    write_line("")
    write_line("準備完了。home sync は Copilot instructions、repo bootstrap 資産、managed enterprise/global guard を同期し、")
    write_line("skills/、agents/、docs/ は plugin install / user-owned surface として触りません。")
    write_line("実行中...")
    write_line("")

    unsupported_hooks_path = template_root / "hooks"
    if unsupported_hooks_path.exists():
        warn("home-template/.copilot/hooks is ignored. User-level hooks are managed through config.json by this sync script.")

    if args.Mirror:
        warn("-Mirror は互換オプションです。home sync の managed surface はスクリプト定義どおりに同期されます。")

    preview_state = SyncPlan()
    legacy_home_hooks_path = destination_path / ".github" / "hooks"
    legacy_home_github_path = destination_path / ".github"
    legacy_home_hook_files = [
        legacy_home_hooks_path / relative_file
        for relative_file in LEGACY_HOME_HOOK_RELATIVE_FILES
        if (legacy_home_hooks_path / relative_file).exists()
    ]
    if legacy_home_hook_files:
        preview_state.deleted.append(".github/hooks known legacy files")
        write_line(f"Legacy home hook transport detected: {legacy_home_hooks_path}")

    directory_plans = [
        (
            "repo-template/ (managed)",
            get_directory_sync_plan(
                source=source_root / "repo-template",
                destination=destination_path / "repo-template",
                preview_root="repo-template",
                mirror_mode=True,
            ),
        ),
    ]
    tracked_file_specs = [
        ("copilot-instructions.md", template_root / "copilot-instructions.md", destination_path / "copilot-instructions.md"),
        ("managed-manifest.json", template_root / "managed-manifest.json", destination_path / "managed-manifest.json"),
        (
            "hooks/scripts/guard_pre_tool.ps1",
            source_root / ".github" / "hooks" / "scripts" / "guard_pre_tool.ps1",
            destination_path / "hooks" / "scripts" / "guard_pre_tool.ps1",
        ),
        (
            "hooks/scripts/guard_pre_tool.sh",
            source_root / ".github" / "hooks" / "scripts" / "guard_pre_tool.sh",
            destination_path / "hooks" / "scripts" / "guard_pre_tool.sh",
        ),
        ("scripts/sync-to-repo.ps1", source_root / "scripts" / "sync-to-repo.ps1", destination_path / "scripts" / "sync-to-repo.ps1"),
        ("scripts/sync-to-repo.sh", source_root / "scripts" / "sync-to-repo.sh", destination_path / "scripts" / "sync-to-repo.sh"),
        ("scripts/install-git-hooks.ps1", source_root / "scripts" / "install-git-hooks.ps1", destination_path / "scripts" / "install-git-hooks.ps1"),
        ("scripts/install-git-hooks.sh", source_root / "scripts" / "install-git-hooks.sh", destination_path / "scripts" / "install-git-hooks.sh"),
        ("scripts/repo-secure-check.ps1", source_root / "scripts" / "repo-secure-check.ps1", destination_path / "scripts" / "repo-secure-check.ps1"),
        ("scripts/repo-secure-check.sh", source_root / "scripts" / "repo-secure-check.sh", destination_path / "scripts" / "repo-secure-check.sh"),
        ("scripts/enter-copilot-maintenance-mode.ps1", source_root / "scripts" / "enter-copilot-maintenance-mode.ps1", destination_path / "scripts" / "enter-copilot-maintenance-mode.ps1"),
        ("scripts/exit-copilot-maintenance-mode.ps1", source_root / "scripts" / "exit-copilot-maintenance-mode.ps1", destination_path / "scripts" / "exit-copilot-maintenance-mode.ps1"),
        ("policy/guard-policy.json", source_root / "policy" / "guard-policy.json", destination_path / "policy" / "guard-policy.json"),
        ("policy/guard-policy.schema.json", source_root / "policy" / "guard-policy.schema.json", destination_path / "policy" / "guard-policy.schema.json"),
    ]
    tracked_file_plans = [
        (label, get_tracked_file_plan(source=source, destination=destination, preview_path=label))
        for label, source, destination in tracked_file_specs
    ]
    powershell_guard_script = str(destination_path / "hooks" / "scripts" / "guard_pre_tool.ps1")
    bash_guard_script = str(destination_path / "hooks" / "scripts" / "guard_pre_tool.sh")

    hooks_cleanup_plan = get_home_hooks_session_continuity_cleanup_plan(destination_path / "hooks")
    hooks_safety_guard_plan = get_home_hooks_safety_guard_plan(
        destination_path / "hooks",
        powershell_script_path=powershell_guard_script,
        bash_script_path=bash_guard_script,
    )

    config_hook_plan = get_home_config_hook_plan(
        destination_path / "config.json",
        powershell_script_path=powershell_guard_script,
        bash_script_path=bash_guard_script,
    )

    all_plans = directory_plans + tracked_file_plans + [
        ("hooks/session-continuity cleanup", hooks_cleanup_plan),
        ("hooks/safety-guard.json", hooks_safety_guard_plan),
        ("config.json", config_hook_plan),
    ]

    for _label, plan in all_plans:
        preview_state.added.extend(plan.added)
        preview_state.updated.extend(plan.updated)
        preview_state.deleted.extend(plan.deleted)

    if args.VerboseLog:
        write_line("◆ 詳細ログ")
        write_line(f"Mode            : {'dry-run' if args.DryRun else 'live'}")
        for label, plan in all_plans:
            if not plan.actions:
                continue
            write_line(f"  [{label}] actions={len(plan.actions)}")
            for action in plan.actions:
                target = action.destination if action.destination else action.source
                write_line(f"    - {action.kind}: {target}")

    if not args.DryRun:
        for _label, plan in all_plans:
            for action in plan.actions:
                if action.kind in {"copy-file", "write-text", "delete-path"}:
                    backup_existing_path(
                        action.destination,
                        destination_root=destination_path,
                        archive_root=archive_root,
                    )
                invoke_file_action(action)
            if plan.mirror_mode and plan.destination_root is not None:
                remove_empty_directories(plan.destination_root)

        for legacy_file in legacy_home_hook_files:
            if legacy_file.exists():
                legacy_file.unlink()
        if legacy_home_hook_files:
            remove_empty_directories(legacy_home_github_path)
            if legacy_home_github_path.exists() and not any(legacy_home_github_path.iterdir()):
                legacy_home_github_path.rmdir()

    write_sync_summary(
        added=len(preview_state.added),
        updated=len(preview_state.updated),
        deleted=len(preview_state.deleted),
        dry_run=args.DryRun,
    )
    write_sync_markers(preview_state, dry_run=args.DryRun)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
