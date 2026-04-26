"""
Contract Verification Checkpoint for impl-and-ship.

Validates that all required artifacts from dependent repos are present
and verifies checksums match between upstream provides and local requires.

This checkpoint runs after eval checkpoint in the impl-and-ship workflow.

On first run (checksum is null in plan_dict), calculates and updates the checksum.
On subsequent runs, verifies checksum matches.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CheckpointResult:
    """Result of checkpoint verification."""

    status: str  # "PASS" or "FAIL"
    reason: str


class ContractMismatchError(Exception):
    """Raised when contract verification fails."""

    pass


def verify_contracts(plan_dict: dict[str, Any], repo_root: Path) -> CheckpointResult:
    """
    Verify all required contracts in the plan.

    On first run (checksum is null), calculates actual checksum from file and updates plan_dict.
    On subsequent runs (checksum exists), validates that actual checksum matches.

    Args:
        plan_dict: Plan YAML front-matter as dict, containing dependencies.contracts.requires
                   Schema: requires[*] = {source_repo, artifact, path, checksum (null | hex)}
        repo_root: Path to the repository root

    Returns:
        CheckpointResult with status and reason
        Updates plan_dict[dependencies][contracts][requires][idx][checksum] on first run

    Raises:
        None (returns FAIL status instead of raising)
    """
    # Handle missing dependencies section
    if not plan_dict:
        return CheckpointResult(
            status="PASS", reason="No plan dictionary provided: 0 contracts verified"
        )

    dependencies = plan_dict.get("dependencies", {})
    contracts = dependencies.get("contracts", {})
    requires = contracts.get("requires", [])

    # No required contracts
    if not requires:
        return CheckpointResult(
            status="PASS", reason="No required contracts: 0 artifacts to verify"
        )

    # Verify each required artifact
    failed_artifacts = []
    verified_count = 0

    for idx, require in enumerate(requires):
        artifact_name = require.get("artifact", "unknown")
        artifact_path_str = require.get("path", "")
        checksum_value = require.get("checksum")  # Can be None, hex string

        artifact_path = repo_root / artifact_path_str

        # Check if artifact exists
        if not artifact_path.exists():
            failed_artifacts.append(
                {
                    "artifact": artifact_name,
                    "path": artifact_path_str,
                    "reason": "missing",
                }
            )
            continue

        # Calculate actual checksum from file
        actual_content = artifact_path.read_bytes()
        actual_checksum = hashlib.sha256(actual_content).hexdigest()

        # Handle first run: checksum is null, calculate and update plan_dict
        if checksum_value is None:
            # Update plan_dict with calculated checksum
            plan_dict["dependencies"]["contracts"]["requires"][idx]["checksum"] = (
                actual_checksum
            )
            verified_count += 1
            continue

        # Verify checksum matches (subsequent runs)
        if actual_checksum != checksum_value:
            failed_artifacts.append(
                {
                    "artifact": artifact_name,
                    "path": artifact_path_str,
                    "reason": "checksum_mismatch",
                    "expected": checksum_value,
                    "actual": actual_checksum,
                }
            )
            continue

        # Artifact verified
        verified_count += 1

    # Return failure if any artifact failed
    if failed_artifacts:
        return _build_failure_result(failed_artifacts, verified_count, requires)

    # All contracts verified; persist updated checksums to plan.md if it exists
    plan_file = repo_root / "plan.md"
    if plan_file.exists():
        save_plan_with_updated_checksums(plan_file, plan_dict)

    # All contracts verified
    return CheckpointResult(
        status="PASS",
        reason=f"Contract verified: {len(requires)} artifacts, {verified_count} checksums validated",
    )


def _build_failure_result(
    failed_artifacts: list[dict[str, Any]], verified_count: int, requires: list[Any]
) -> CheckpointResult:
    """Build a detailed failure result with actionable error message."""
    error_parts = [
        "Contract verification failed:",
    ]

    for failed in failed_artifacts:
        artifact = failed["artifact"]
        path = failed["path"]
        reason = failed["reason"]

        if reason == "missing":
            error_parts.append(
                f"\n  - Missing artifact: {artifact}"
                f"\n    Path: {path}"
                f"\n    Action: Check if upstream repo merged PR with this artifact"
                f"\n    Remediation: Wait for upstream impl-and-ship to complete, or verify path is correct"
            )
        elif reason == "checksum_mismatch":
            expected = failed.get("expected", "unknown")
            actual = failed.get("actual", "unknown")
            error_parts.append(
                f"\n  - Checksum mismatch: {artifact}"
                f"\n    Path: {path}"
                f"\n    Expected: {expected}"
                f"\n    Actual:   {actual}"
                f"\n    Action: Upstream artifact changed since design handoff"
                f"\n    Remediation: Contact upstream team or re-run design-workshop"
            )

    if verified_count > 0:
        error_parts.append(f"\n  ({verified_count}/{len(requires)} artifacts verified)")

    reason = "".join(error_parts)

    return CheckpointResult(status="FAIL", reason=reason)


def save_plan_with_updated_checksums(plan_path: Path, plan_dict: dict) -> None:
    """Save plan.md with updated checksums in YAML front-matter.
    
    Preserves non-YAML content while updating the YAML front-matter with new checksums.
    """
    if not plan_path.exists():
        return  # Nothing to save if no file

    # Read original file to preserve non-YAML content
    original_content = plan_path.read_text()

    # Find YAML front-matter boundaries
    lines = original_content.split("\n")
    yaml_end_idx = None
    
    # Skip first line (opening ---)
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            yaml_end_idx = idx
            break

    if yaml_end_idx is None:
        return  # No YAML front-matter found, can't update

    # Serialize YAML front-matter using PyYAML
    front_matter = {}
    if "project_context" in plan_dict:
        front_matter["project_context"] = plan_dict["project_context"]
    if "dependencies" in plan_dict:
        front_matter["dependencies"] = plan_dict["dependencies"]
    
    yaml_str = yaml.dump(front_matter, default_flow_style=False, sort_keys=False)
    yaml_lines = ["---", *yaml_str.rstrip("\n").split("\n"), "---"]
    
    # Combine YAML with rest of file
    rest_of_file = "\n".join(lines[yaml_end_idx + 1 :])
    updated_content = "\n".join(yaml_lines) + "\n" + rest_of_file

    # Write back
    plan_path.write_text(updated_content)


