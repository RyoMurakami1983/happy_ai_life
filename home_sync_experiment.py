from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from dataclasses import dataclass

from scripts import home_sync_planner as planner


@dataclass(frozen=True)
class ExperimentWorkspace:
    root: Path
    source_root: Path
    destination_root: Path
    archive_root: Path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def copy_path(source: Path, destination: Path) -> None:
    ensure_parent(destination)
    if source.is_dir():
        shutil.copytree(source, destination)
        return
    shutil.copy2(source, destination)


def backup_existing(destination: Path, archive: Path) -> None:
    remove_path(archive)
    if not destination.exists():
        return
    copy_path(destination, archive)


def replace_with_archive(source: Path, destination: Path, archive: Path) -> None:
    backup_existing(destination, archive)
    remove_path(destination)
    copy_path(source, destination)


def plan_experiment_sync(workspace: ExperimentWorkspace) -> list[planner.SyncAction]:
    return planner.plan_home_sync(
        source_root=workspace.source_root,
        destination_root=workspace.destination_root,
        archive_root=workspace.archive_root,
    )


def apply_sync_actions(actions: list[planner.SyncAction]) -> None:
    for action in actions:
        match action.kind:
            case "copy-skill" | "copy-agent":
                if action.source is None:
                    raise ValueError(f"Source is required for {action.kind}")
                remove_path(action.destination)
                copy_path(action.source, action.destination)
            case "update-skill" | "update-agent":
                if action.source is None or action.archive is None:
                    raise ValueError(f"Source and archive are required for {action.kind}")
                replace_with_archive(action.source, action.destination, action.archive)
            case "preserve-skill-extra" | "preserve-agent-extra":
                continue
            case _:
                raise ValueError(f"Unsupported action kind: {action.kind}")


def create_demo_workspace(root: Path) -> ExperimentWorkspace:
    workspace = ExperimentWorkspace(
        root=root,
        source_root=root / "source",
        destination_root=root / "home",
        archive_root=root / "copilot_archives",
    )

    template_copilot = workspace.source_root / "home-template" / ".copilot"
    template_skills = template_copilot / "skills"
    template_agents = template_copilot / "agents"
    home_skills = workspace.destination_root / "skills"
    home_agents = workspace.destination_root / "agents"

    (template_skills / "managed-skill").mkdir(parents=True, exist_ok=True)
    (template_skills / "new-skill").mkdir(parents=True, exist_ok=True)
    (template_agents / "nested").mkdir(parents=True, exist_ok=True)
    home_skills.mkdir(parents=True, exist_ok=True)
    home_agents.mkdir(parents=True, exist_ok=True)

    (template_skills / "managed-skill" / "SKILL.md").write_text("# managed v2\n", encoding="utf-8")
    (template_skills / "managed-skill" / "references.txt").write_text("new reference\n", encoding="utf-8")
    (template_skills / "new-skill" / "SKILL.md").write_text("# new skill\n", encoding="utf-8")
    (template_agents / "review.agent.md").write_text("# review v2\n", encoding="utf-8")
    (template_agents / "nested" / "triage.agent.md").write_text("# triage v1\n", encoding="utf-8")

    (home_skills / "managed-skill").mkdir(parents=True, exist_ok=True)
    (home_skills / "local-extra").mkdir(parents=True, exist_ok=True)
    (home_skills / "managed-skill" / "SKILL.md").write_text("# managed v1\n", encoding="utf-8")
    (home_skills / "managed-skill" / "references.txt").write_text("old reference\n", encoding="utf-8")
    (home_skills / "local-extra" / "SKILL.md").write_text("# local extra\n", encoding="utf-8")
    (home_agents / "review.agent.md").write_text("# review v1\n", encoding="utf-8")
    (home_agents / "custom.agent.md").write_text("# custom extra\n", encoding="utf-8")

    return workspace


def prefix_snapshot(prefix: str, snapshot: dict[str, str]) -> dict[str, str]:
    return {f"{prefix}/{relative_path}": digest for relative_path, digest in snapshot.items()}


def run_demo(workspace_root: Path) -> dict[str, object]:
    workspace = create_demo_workspace(workspace_root)
    planned_actions = plan_experiment_sync(workspace)
    apply_sync_actions(planned_actions)
    return {
        "workspace": str(workspace.root),
        "actions": planner.serialize_actions(planned_actions),
        "skills": prefix_snapshot("skills", planner.collect_file_hashes(workspace.destination_root / "skills")),
        "agents": prefix_snapshot("agents", planner.collect_file_hashes(workspace.destination_root / "agents")),
        "archives": planner.collect_file_hashes(workspace.archive_root),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a temporary filesystem-diff home-sync experiment for skills and agents.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Optional workspace root. If omitted, a temporary directory is created and printed.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workspace_root = args.workspace or Path(tempfile.mkdtemp(prefix="happy-home-sync-experiment-"))
    result = run_demo(workspace_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
