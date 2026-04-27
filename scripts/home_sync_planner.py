from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


ActionKind = Literal[
    "copy-skill",
    "update-skill",
    "preserve-skill-extra",
    "copy-agent",
    "update-agent",
    "preserve-agent-extra",
]

CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class SyncAction:
    kind: ActionKind
    item: str
    source: Path | None
    destination: Path
    archive: Path | None = None


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def collect_file_hashes(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}

    hashes: dict[str, str] = {}
    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = file_path.relative_to(root).as_posix()
        hashes[relative] = hash_file(file_path)
    return hashes


def directories_match(left: Path, right: Path) -> bool:
    return collect_file_hashes(left) == collect_file_hashes(right)


def files_match(left: Path, right: Path) -> bool:
    return hash_file(left) == hash_file(right)


def plan_skill_sync(
    template_skills_dir: Path,
    home_skills_dir: Path,
    archive_root: Path,
) -> list[SyncAction]:
    actions: list[SyncAction] = []
    template_entries = {path.name: path for path in sorted(template_skills_dir.iterdir()) if path.is_dir()}
    home_entries = {path.name: path for path in sorted(home_skills_dir.iterdir()) if path.is_dir()} if home_skills_dir.exists() else {}

    for name, source_dir in template_entries.items():
        destination_dir = home_skills_dir / name
        archive_dir = archive_root / "skills" / name
        if name not in home_entries:
            actions.append(SyncAction("copy-skill", name, source_dir, destination_dir))
            continue
        if directories_match(source_dir, destination_dir):
            continue
        actions.append(SyncAction("update-skill", name, source_dir, destination_dir, archive_dir))

    for name, destination_dir in home_entries.items():
        if name in template_entries:
            continue
        actions.append(SyncAction("preserve-skill-extra", name, None, destination_dir))

    return actions


def plan_agent_sync(
    template_agents_dir: Path,
    home_agents_dir: Path,
    archive_root: Path,
) -> list[SyncAction]:
    actions: list[SyncAction] = []
    template_entries = {
        path.relative_to(template_agents_dir).as_posix(): path
        for path in sorted(template_agents_dir.rglob("*.agent.md"))
        if path.is_file()
    }
    home_entries = (
        {
            path.relative_to(home_agents_dir).as_posix(): path
            for path in sorted(home_agents_dir.rglob("*.agent.md"))
            if path.is_file()
        }
        if home_agents_dir.exists()
        else {}
    )

    for relative_path, source_file in template_entries.items():
        destination_file = home_agents_dir / relative_path
        archive_file = archive_root / "agents" / relative_path
        if relative_path not in home_entries:
            actions.append(SyncAction("copy-agent", relative_path, source_file, destination_file))
            continue
        if files_match(source_file, destination_file):
            continue
        actions.append(SyncAction("update-agent", relative_path, source_file, destination_file, archive_file))

    for relative_path, destination_file in home_entries.items():
        if relative_path in template_entries:
            continue
        actions.append(SyncAction("preserve-agent-extra", relative_path, None, destination_file))

    return actions


def plan_home_sync(
    *,
    source_root: Path,
    destination_root: Path,
    archive_root: Path,
) -> list[SyncAction]:
    template_root = resolve_home_template_root(source_root)
    return [
        *plan_skill_sync(
            template_root / "skills",
            destination_root / "skills",
            archive_root,
        ),
        *plan_agent_sync(
            template_root / "agents",
            destination_root / "agents",
            archive_root,
        ),
    ]


def resolve_home_template_root(source_root: Path) -> Path:
    nested_template_root = source_root / "home-template" / ".copilot"
    if nested_template_root.exists():
        return nested_template_root

    packaged_template_root = source_root
    required_paths = (
        packaged_template_root / "skills",
        packaged_template_root / "agents",
        packaged_template_root / "copilot-instructions.md",
    )
    if all(path.exists() for path in required_paths):
        return packaged_template_root

    raise FileNotFoundError(
        f"Could not resolve home template root from source root: {source_root}"
    )


def summarize_actions(actions: list[SyncAction]) -> dict[str, object]:
    added: list[str] = []
    updated: list[str] = []
    deleted: list[str] = []

    for action in actions:
        if action.kind in {"copy-skill", "copy-agent"}:
            if action.kind == "copy-skill":
                added.append(f"skills/{action.item}")
            else:
                added.append(f"agents/{action.item}")
            continue
        if action.kind in {"update-skill", "update-agent"}:
            if action.kind == "update-skill":
                updated.append(f"skills/{action.item}")
            else:
                updated.append(f"agents/{action.item}")
            continue

    return {
        "stats": {
            "added": len(added),
            "updated": len(updated),
            "deleted": len(deleted),
        },
        "preview": {
            "added": added,
            "updated": updated,
            "deleted": deleted,
            "added_more": 0,
            "updated_more": 0,
            "deleted_more": 0,
        },
    }


def serialize_actions(actions: list[SyncAction]) -> list[dict[str, str | None]]:
    serialized: list[dict[str, str | None]] = []
    for action in actions:
        payload = asdict(action)
        serialized.append(
            {
                "kind": payload["kind"],
                "item": payload["item"],
                "source": str(payload["source"]) if payload["source"] else None,
                "destination": str(payload["destination"]),
                "archive": str(payload["archive"]) if payload["archive"] else None,
            }
        )
    return serialized


def build_plan_payload(
    *,
    source_root: Path,
    destination_root: Path,
    archive_root: Path,
) -> dict[str, object]:
    actions = plan_home_sync(
        source_root=source_root,
        destination_root=destination_root,
        archive_root=archive_root,
    )
    summary = summarize_actions(actions)
    return {
        "actions": serialize_actions(actions),
        **summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a filesystem-diff plan for home sync skills/agents.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_plan_payload(
        source_root=args.source_root,
        destination_root=args.destination_root,
        archive_root=args.archive_root,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
