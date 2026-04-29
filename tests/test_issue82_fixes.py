"""
Tests for Issue #82 fixes:
1. Field name mismatch: checksum_required → checksum
2. Checksum persistence: plan.md not updated with calculated checksums

Follows TDD Red-Green-Refactor.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# Add plugin package to path for skill imports
ROOT_DIR = Path(__file__).resolve().parents[1]
ORCHESTRATOR_DIR = (
    ROOT_DIR
    / "plugins"
    / "happy-ai-life"
    / "skills"
    / "impl-and-ship"
    / "orchestrator"
)
CHECKPOINT_DIR = (
    ROOT_DIR
    / "plugins"
    / "happy-ai-life"
    / "skills"
    / "impl-and-ship"
    / "checkpoints"
)

for dir_path in [ORCHESTRATOR_DIR, CHECKPOINT_DIR]:
    if str(dir_path) not in sys.path:
        sys.path.insert(0, str(dir_path))

# noqa: E402 - Module level import after path manipulation
from fleet_orchestrator import orchestrate_multi_repo_impl_and_ship  # noqa: E402
from contract_verify import verify_contracts  # noqa: E402


class TestIssue82FieldNameMismatch:
    """Test: checksum field name fix in fleet_orchestrator."""

    def test_orchestrator_reads_checksum_field_not_checksum_required(self) -> None:
        """
        Issue #82 Fix 1: fleet_orchestrator must read 'checksum' field, not 'checksum_required'.

        Phase 1 generates 'checksum' field in requires.
        fleet_orchestrator.py line 237 must read req.get("checksum"), not req.get("checksum_required").
        """
        repos = {
            "backend": {
                "dependencies": {
                    "blocking": [],
                    "contracts": {
                        "provides": [{"artifact": "api", "checksum": "sha256:abc123"}]
                    },
                }
            },
            "frontend": {
                "dependencies": {
                    "blocking": ["backend"],
                    "contracts": {
                        "requires": [
                            {
                                "source_repo": "backend",
                                "artifact": "api",
                                # Using 'checksum' not 'checksum_required' (Phase 1 output)
                                "checksum": "sha256:wrongchecksum",
                            }
                        ]
                    },
                }
            },
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        # frontend should be blocked due to checksum mismatch (with correct field name)
        assert "backend" in result.repos_passed
        assert "frontend" in result.repos_blocked
        assert result.overall_status == "FAILURE"
        # Verify the blocking reason mentions checksum mismatch
        assert any("checksum" in log.lower() for log in result.status_log)

    def test_orchestrator_checksum_match_allows_execution(self) -> None:
        """Test: when checksums match, frontend proceeds (using correct field name)."""
        repos = {
            "backend": {
                "dependencies": {
                    "blocking": [],
                    "contracts": {
                        "provides": [{"artifact": "api", "checksum": "sha256:correctchecksum"}]
                    },
                }
            },
            "frontend": {
                "dependencies": {
                    "blocking": ["backend"],
                    "contracts": {
                        "requires": [
                            {
                                "source_repo": "backend",
                                "artifact": "api",
                                # Same checksum as provider (correct field name)
                                "checksum": "sha256:correctchecksum",
                            }
                        ]
                    },
                }
            },
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        # Both should pass since checksums match
        assert "backend" in result.repos_passed
        assert "frontend" in result.repos_passed
        assert result.overall_status == "SUCCESS"


class TestIssue82ChecksumPersistence:
    """Test: checksums calculated in Phase 3 persist to plan.md."""

    def test_verify_contracts_persists_checksums_to_plan_file(self, tmp_path: Path) -> None:
        """
        Issue #82 Fix 2: contract_verify must persist updated checksums to plan.md file.

        On first run, checksum=null in plan.md.
        After verify_contracts() calculates checksum, it should be saved to plan.md.
        """
        # Create artifact with exact content
        artifact_dir = tmp_path / "docs"
        artifact_dir.mkdir(parents=True)
        artifact_file = artifact_dir / "openapi.yaml"
        
        # Use simpler content to avoid encoding issues
        artifact_content = "test content for checksum"
        artifact_file.write_text(artifact_content)
        
        # Calculate what the checksum should be
        expected_checksum = hashlib.sha256(artifact_content.encode()).hexdigest()

        # Create plan.md with YAML front-matter (null checksum)
        plan_file = tmp_path / "plan.md"
        # Use a properly formatted YAML
        plan_file.write_text(
            "---\n"
            "project_context:\n"
            "  repository: frontend\n"
            "\n"
            "dependencies:\n"
            "  contracts:\n"
            "    requires:\n"
            "      - source_repo: backend\n"
            "        artifact: openapi\n"
            "        path: docs/openapi.yaml\n"
            "        checksum: null\n"
            "\n"
            "---\n"
            "# Plan Content\n"
            "\n"
            "This is the main plan document.\n"
        )

        # Parse plan_dict from YAML (simulating what would come from plan loader)
        plan_dict = {
            "project_context": {"repository": "frontend"},
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": None,
                        }
                    ]
                }
            },
        }

        # Run verification (should calculate checksum and update plan_dict)
        result = verify_contracts(plan_dict, tmp_path)
        assert result.status == "PASS"
        assert plan_dict["dependencies"]["contracts"]["requires"][0]["checksum"] == expected_checksum

        # Verify persistence: re-read plan.md and check checksum was saved
        updated_plan_content = plan_file.read_text()
        assert expected_checksum in updated_plan_content, (
            f"Checksum not persisted to plan.md. "
            f"Expected checksum {expected_checksum} not found in:\n{updated_plan_content}"
        )
        assert "checksum: null" not in updated_plan_content, (
            "Checksum should not be null after verification"
        )

    def test_verify_contracts_updates_plan_dict_in_memory(self, tmp_path: Path) -> None:
        """Test: verify_contracts updates plan_dict in-memory (current behavior)."""
        # Create artifact
        artifact_file = tmp_path / "schema.json"
        artifact_content = '{"type": "object"}'
        artifact_file.write_text(artifact_content)
        expected_checksum = hashlib.sha256(artifact_content.encode()).hexdigest()

        # Plan with null checksum
        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "schema",
                            "path": "schema.json",
                            "checksum": None,
                        }
                    ]
                }
            }
        }

        # Before verification
        assert plan_dict["dependencies"]["contracts"]["requires"][0]["checksum"] is None

        result = verify_contracts(plan_dict, tmp_path)

        # After verification
        assert result.status == "PASS"
        assert (
            plan_dict["dependencies"]["contracts"]["requires"][0]["checksum"]
            == expected_checksum
        ), "plan_dict should be updated with calculated checksum"
