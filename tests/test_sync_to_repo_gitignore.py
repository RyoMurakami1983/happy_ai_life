from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-to-repo.ps1"
ROBOCOPY = shutil.which("robocopy")
SKIP_REASON = "sync-to-repo.ps1 requires Windows robocopy"
GUARD_POLICY_PATH = ROOT / "policy" / "guard-policy.json"
GUARD_POLICY_SCHEMA_PATH = ROOT / "policy" / "guard-policy.schema.json"


def _powershell_executable() -> str:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    pytest.skip("PowerShell executable not found")


pytestmark = pytest.mark.skipif(
    os.name != "nt" or ROBOCOPY is None,
    reason=SKIP_REASON,
)


def _run_sync(
    source_root: Path,
    target_repo: Path,
    *,
    dry_run: bool,
    hooks_mode: str | None = None,
    policy_profile: str | None = None,
    policy_relative_path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-SourceRoot",
        str(source_root),
        "-TargetRepoPath",
        str(target_repo),
        "-HooksRelativePath",
        "",
        "-GitHooksRelativePath",
        "",
        "-DocsSessionsRelativePath",
        "",
    ]
    if hooks_mode is not None:
        command.extend(["-HooksMode", hooks_mode])
    if policy_profile is not None:
        command.extend(["-PolicyProfile", policy_profile])
    if policy_relative_path is not None:
        command.extend(["-PolicyRelativePath", policy_relative_path])
    if dry_run:
        command.append("-DryRun")

    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _create_minimal_source_root(base: Path) -> Path:
    template_dir = base / "repo-template" / ".github"
    template_dir.mkdir(parents=True)
    instructions_dir = template_dir / "instructions"
    instructions_dir.mkdir()
    (template_dir / ".gitignore").write_text(
        "# Session and local files\n"
        "sessions/\n"
        "instructions/session-context.instructions.md\n",
        encoding="utf-8",
    )
    (instructions_dir / "python.instructions.md").write_text(
        "# Python instructions\n",
        encoding="utf-8",
    )
    (instructions_dir / "enterprise.instructions.md").write_text(
        "# Enterprise instructions\n",
        encoding="utf-8",
    )
    policy_dir = base / "policy"
    policy_dir.mkdir()
    shutil.copy2(GUARD_POLICY_PATH, policy_dir / "guard-policy.json")
    shutil.copy2(GUARD_POLICY_SCHEMA_PATH, policy_dir / "guard-policy.schema.json")
    return base


def _create_source_root_with_hooks(base: Path) -> Path:
    source_root = _create_minimal_source_root(base)
    hooks_root = source_root / ".github" / "hooks"
    hooks_root.mkdir(parents=True)
    (hooks_root / "safety-guard.json").write_text("{}", encoding="utf-8")
    (hooks_root / "session-continuity.json").write_text("{}", encoding="utf-8")
    return source_root


def _run_hooks_sync(
    source_root: Path,
    target_repo: Path,
    *,
    hooks_mode: str | None = None,
    dry_run: bool = False,
    mirror: bool = False,
    policy_profile: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-SourceRoot",
        str(source_root),
        "-TargetRepoPath",
        str(target_repo),
        "-GitHooksRelativePath",
        "",
        "-DocsSessionsRelativePath",
        "",
    ]
    if hooks_mode is not None:
        command.extend(["-HooksMode", hooks_mode])
    if policy_profile is not None:
        command.extend(["-PolicyProfile", policy_profile])
    if dry_run:
        command.append("-DryRun")
    if mirror:
        command.append("-Mirror")

    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_sync_to_repo_preserves_existing_github_gitignore_on_dry_run(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    github_dir = target_repo / ".github"
    github_dir.mkdir(parents=True)
    original = "# custom local rule\ncustom.local\n"
    target_file = github_dir / ".gitignore"
    target_file.write_text(original, encoding="utf-8")

    result = _run_sync(source_root, target_repo, dry_run=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert target_file.read_text(encoding="utf-8") == original


def test_sync_to_repo_appends_missing_github_gitignore_rules(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    github_dir = target_repo / ".github"
    github_dir.mkdir(parents=True)
    target_file = github_dir / ".gitignore"
    target_file.write_text("# custom local rule\ncustom.local\n", encoding="utf-8")

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr

    content = target_file.read_text(encoding="utf-8")
    assert "# custom local rule" in content
    assert "custom.local" in content
    assert "sessions/" in content
    assert "instructions/session-context.instructions.md" in content
    assert (target_repo / ".github" / "instructions" / "python.instructions.md").exists()


def test_sync_to_repo_creates_missing_github_gitignore(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    (target_repo / ".github").mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr

    target_file = target_repo / ".github" / ".gitignore"
    assert target_file.exists()
    content = target_file.read_text(encoding="utf-8")
    assert "sessions/" in content
    assert "instructions/session-context.instructions.md" in content
    assert (target_repo / ".github" / "instructions" / "python.instructions.md").exists()


def test_sync_to_repo_copies_guard_policy_files(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (target_repo / "policy" / "guard-policy.json").read_text(encoding="utf-8") == GUARD_POLICY_PATH.read_text(encoding="utf-8")
    assert (target_repo / "policy" / "guard-policy.schema.json").read_text(encoding="utf-8") == GUARD_POLICY_SCHEMA_PATH.read_text(encoding="utf-8")


def test_sync_to_repo_fails_when_policy_source_is_missing(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    shutil.rmtree(source_root / "policy")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode != 0
    assert "Guard policy source path not found" in result.stderr


def test_sync_to_repo_missing_policy_source_fails_before_any_writes(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    shutil.rmtree(source_root / "policy")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode != 0
    assert "Guard policy source path not found" in result.stderr
    assert not (target_repo / ".github").exists()
    assert not (target_repo / ".githooks").exists()
    assert not (target_repo / "policy").exists()


@pytest.mark.parametrize("missing_policy_file", ["guard-policy.json", "guard-policy.schema.json"])
def test_sync_to_repo_missing_required_policy_file_fails_before_any_writes(tmp_path: Path, missing_policy_file: str) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    (source_root / "policy" / missing_policy_file).unlink()
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode != 0
    assert "Guard policy source file not found" in result.stderr
    assert missing_policy_file in result.stderr
    assert not (target_repo / ".github").exists()
    assert not (target_repo / ".githooks").exists()
    assert not (target_repo / "policy").exists()


def test_sync_to_repo_allows_explicit_policy_sync_opt_out(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    shutil.rmtree(source_root / "policy")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False, policy_relative_path="")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (target_repo / "policy").exists()


def test_sync_to_repo_default_profile_excludes_enterprise_instruction(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    (target_repo / ".github").mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (target_repo / ".github" / "instructions" / "enterprise.instructions.md").exists()


def test_sync_to_repo_default_profile_removes_existing_enterprise_instruction(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    instructions_dir = target_repo / ".github" / "instructions"
    instructions_dir.mkdir(parents=True)
    stale_instruction = instructions_dir / "enterprise.instructions.md"
    stale_instruction.write_text("# stale enterprise instructions\n", encoding="utf-8")

    result = _run_sync(source_root, target_repo, dry_run=False, policy_profile="Default")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not stale_instruction.exists()
    assert "Removed excluded policy profile artifact" in result.stdout


def test_sync_to_repo_default_profile_dry_run_preserves_existing_enterprise_instruction(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    instructions_dir = target_repo / ".github" / "instructions"
    instructions_dir.mkdir(parents=True)
    stale_instruction = instructions_dir / "enterprise.instructions.md"
    stale_instruction.write_text("# stale enterprise instructions\n", encoding="utf-8")

    result = _run_sync(source_root, target_repo, dry_run=True, policy_profile="Default")

    assert result.returncode == 0, result.stdout + result.stderr
    assert stale_instruction.exists()
    assert "Would remove excluded policy profile artifact" in result.stdout


def test_sync_to_repo_enterprise_profile_includes_enterprise_instruction(tmp_path: Path) -> None:
    source_root = _create_minimal_source_root(tmp_path / "source")
    target_repo = tmp_path / "target"
    (target_repo / ".github").mkdir(parents=True)

    result = _run_sync(source_root, target_repo, dry_run=False, policy_profile="Enterprise")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (target_repo / ".github" / "instructions" / "enterprise.instructions.md").exists()


def test_sync_to_repo_safety_only_excludes_session_continuity_hook(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_hooks_sync(source_root, target_repo, hooks_mode="SafetyOnly")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (target_repo / ".github" / "hooks" / "safety-guard.json").exists()
    assert not (target_repo / ".github" / "hooks" / "session-continuity.json").exists()


def test_sync_to_repo_default_hooks_mode_is_safety_only(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_hooks_sync(source_root, target_repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (target_repo / ".github" / "hooks" / "safety-guard.json").exists()
    assert not (target_repo / ".github" / "hooks" / "session-continuity.json").exists()


def test_sync_to_repo_safety_only_removes_existing_session_continuity_hook(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    hooks_dir = target_repo / ".github" / "hooks"
    hooks_dir.mkdir(parents=True)
    stale_hook = hooks_dir / "session-continuity.json"
    stale_hook.write_text("{}", encoding="utf-8")

    result = _run_hooks_sync(source_root, target_repo, hooks_mode="SafetyOnly", mirror=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (hooks_dir / "safety-guard.json").exists()
    assert not stale_hook.exists()
    assert "Removed sealed session continuity artifact" in result.stdout


def test_sync_to_repo_safety_only_dry_run_preserves_existing_session_continuity_hook(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    hooks_dir = target_repo / ".github" / "hooks"
    hooks_dir.mkdir(parents=True)
    stale_hook = hooks_dir / "session-continuity.json"
    stale_hook.write_text("{}", encoding="utf-8")

    result = _run_hooks_sync(source_root, target_repo, hooks_mode="SafetyOnly", dry_run=True, mirror=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert stale_hook.exists()
    assert "Would remove sealed session continuity artifact" in result.stdout


def test_sync_to_repo_safety_only_removes_existing_session_context_instruction(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    instructions_dir = target_repo / ".github" / "instructions"
    instructions_dir.mkdir(parents=True)
    stale_instruction = instructions_dir / "session-context.instructions.md"
    stale_instruction.write_text("# stale context\n", encoding="utf-8")

    result = _run_hooks_sync(source_root, target_repo, hooks_mode="SafetyOnly")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not stale_instruction.exists()
    assert "Removed sealed session continuity artifact" in result.stdout


def test_sync_to_repo_hooks_mode_all_includes_session_continuity_hook(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_hooks_sync(source_root, target_repo, hooks_mode="All")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (target_repo / ".github" / "hooks" / "safety-guard.json").exists()
    assert (target_repo / ".github" / "hooks" / "session-continuity.json").exists()


def test_sync_to_repo_hooks_mode_none_skips_hooks(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    target_repo.mkdir(parents=True)

    result = _run_hooks_sync(source_root, target_repo, hooks_mode="None")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (target_repo / ".github" / "hooks").exists()


def test_sync_to_repo_empty_hooks_path_skips_sealed_artifact_cleanup(tmp_path: Path) -> None:
    source_root = _create_source_root_with_hooks(tmp_path / "source")
    target_repo = tmp_path / "target"
    stale_hook = target_repo / ".github" / "hooks" / "session-continuity.json"
    stale_instruction = target_repo / ".github" / "instructions" / "session-context.instructions.md"
    stale_hook.parent.mkdir(parents=True)
    stale_instruction.parent.mkdir(parents=True)
    stale_hook.write_text("{}", encoding="utf-8")
    stale_instruction.write_text("# stale context\n", encoding="utf-8")

    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-SourceRoot",
        str(source_root),
        "-TargetRepoPath",
        str(target_repo),
        "-HooksRelativePath",
        "",
        "-GitHooksRelativePath",
        "",
        "-DocsSessionsRelativePath",
        "",
        "-HooksMode",
        "SafetyOnly",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert stale_hook.exists()
    assert stale_instruction.exists()
