"""
Tests for contract_verify checkpoint in impl-and-ship.

Follows TDD Red-Green-Refactor:
1. Red: Minimal failing test that captures expected behavior
2. Green: Minimal implementation to pass the test
3. Refactor: Clean up code while maintaining passing tests

Schema: dependencies.contracts.requires[*] with fields:
  - source_repo: str
  - artifact: str
  - path: str
  - checksum: str | null  (null on first run, calculated and updated on first verify)
  - version: str (optional)
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# Add home-template to path for skill imports
ROOT_DIR = Path(__file__).resolve().parents[1]
CHECKPOINT_DIR = (
    ROOT_DIR
    / "home-template"
    / ".copilot"
    / "skills"
    / "impl-and-ship"
    / "checkpoints"
)
if str(CHECKPOINT_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKPOINT_DIR))

# noqa: E402 - Module level import after path manipulation (needed for skill imports)
from contract_verify import (  # noqa: E402
    verify_contracts,
)


class TestContractVerifyMissingArtifact:
    """Test: missing artifact → FAIL with clear error."""

    def test_contract_verify_missing_artifact(self, tmp_path: Path) -> None:
        """Test: required artifact missing → FAIL."""
        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": "sha256:abc123",
                        }
                    ]
                }
            }
        }

        # Repo doesn't have the required artifact
        repo_root = tmp_path / "frontend"
        repo_root.mkdir()

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "FAIL"
        assert "missing" in result.reason.lower() or "not found" in result.reason.lower()
        assert "docs/openapi.yaml" in result.reason


class TestContractVerifyChecksumMismatch:
    """Test: checksum mismatch → FAIL with clear error."""

    def test_contract_verify_checksum_mismatch(self, tmp_path: Path) -> None:
        """Test: checksum mismatch → FAIL."""
        # Create a file with different content than expected checksum
        artifact_path = tmp_path / "docs" / "openapi.yaml"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text("actual openapi content")

        # Different expected checksum (don't recalculate actual, just use wrong one)
        expected_checksum = "sha256:expectedchecksumxyz"

        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": expected_checksum,
                        }
                    ]
                }
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "FAIL"
        assert "checksum" in result.reason.lower() or "mismatch" in result.reason.lower()
        assert expected_checksum in result.reason or "expected" in result.reason.lower()


class TestContractVerifyAllPass:
    """Test: all contracts valid → PASS."""

    def test_contract_verify_all_pass(self, tmp_path: Path) -> None:
        """Test: all contracts match → PASS."""
        # Create artifact with known content
        artifact_path = tmp_path / "docs" / "openapi.yaml"
        artifact_path.parent.mkdir(parents=True)
        artifact_content = "openapi: 3.0.0\ninfo:\n  title: Test API"
        artifact_path.write_bytes(artifact_content.encode())

        # Calculate checksum (without sha256: prefix per new schema)
        checksum = hashlib.sha256(artifact_content.encode()).hexdigest()

        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": checksum,
                        }
                    ]
                }
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "PASS"
        assert "verified" in result.reason.lower() or "success" in result.reason.lower()


class TestContractVerifyNoContracts:
    """Test: no requires → PASS."""

    def test_contract_verify_no_contracts(self, tmp_path: Path) -> None:
        """Test: no required contracts → PASS."""
        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": []
                }
            }
        }

        repo_root = tmp_path
        repo_root.mkdir(exist_ok=True)

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "PASS"
        assert "no" in result.reason.lower() or "0" in result.reason


class TestContractVerifyErrorMessageClarity:
    """Test: error messages are actionable."""

    def test_contract_verify_error_message_clarity(self, tmp_path: Path) -> None:
        """Test: error messages suggest remediation."""
        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi-v1",
                            "path": "dist/openapi-v1.yaml",
                            "checksum": "sha256:missing123",
                        }
                    ]
                }
            }
        }

        repo_root = tmp_path
        repo_root.mkdir(exist_ok=True)

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "FAIL"
        # Error message should suggest action
        reason_lower = result.reason.lower()
        assert any(
            keyword in reason_lower
            for keyword in [
                "wait",
                "check",
                "upstream",
                "merged",
                "path",
                "backend",
            ]
        ), f"Error message not actionable: {result.reason}"


class TestContractVerifyMultipleArtifacts:
    """Test: verify multiple artifacts."""

    def test_contract_verify_multiple_artifacts_all_pass(self, tmp_path: Path) -> None:
        """Test: multiple artifacts, all passing → PASS."""
        # Create first artifact
        artifact1_path = tmp_path / "docs" / "openapi.yaml"
        artifact1_path.parent.mkdir(parents=True)
        artifact1_content = "openapi spec"
        artifact1_path.write_text(artifact1_content)
        checksum1 = hashlib.sha256(artifact1_content.encode()).hexdigest()

        # Create second artifact
        artifact2_path = tmp_path / "schemas" / "models.json"
        artifact2_path.parent.mkdir(parents=True)
        artifact2_content = '{"User": {"type": "object"}}'
        artifact2_path.write_text(artifact2_content)
        checksum2 = hashlib.sha256(artifact2_content.encode()).hexdigest()

        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": checksum1,
                        },
                        {
                            "source_repo": "backend",
                            "artifact": "schemas",
                            "path": "schemas/models.json",
                            "checksum": checksum2,
                        },
                    ]
                }
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "PASS"
        assert "2" in result.reason or "multiple" in result.reason.lower()

    def test_contract_verify_multiple_artifacts_one_fails(
        self, tmp_path: Path
    ) -> None:
        """Test: multiple artifacts, one missing → FAIL."""
        # Create first artifact
        artifact1_path = tmp_path / "docs" / "openapi.yaml"
        artifact1_path.parent.mkdir(parents=True)
        artifact1_content = "openapi spec"
        artifact1_path.write_text(artifact1_content)
        checksum1 = hashlib.sha256(artifact1_content.encode()).hexdigest()

        # Second artifact missing

        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": checksum1,
                        },
                        {
                            "source_repo": "backend",
                            "artifact": "schemas",
                            "path": "schemas/models.json",
                            "checksum": "sha256:missing",
                        },
                    ]
                }
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "FAIL"
        assert "models.json" in result.reason


class TestContractVerifyNoDependencies:
    """Test: plan with no dependencies section."""

    def test_contract_verify_no_dependencies_section(self, tmp_path: Path) -> None:
        """Test: plan without dependencies section → PASS."""
        plan_dict = {}

        repo_root = tmp_path
        repo_root.mkdir(exist_ok=True)

        result = verify_contracts(plan_dict, repo_root)

        assert result.status == "PASS"


class TestContractVerifyNullChecksum:
    """Test: null checksum (first run) → calculate, update plan_dict, and PASS."""

    def test_contract_verify_null_checksum_calculates_and_updates(
        self, tmp_path: Path
    ) -> None:
        """Test: checksum=null → calculate actual, update plan_dict, PASS.
        
        This is the key new behavior for Phase 3:
        - On first run, checksum is null in plan.md
        - verify_contracts() calculates actual checksum from file
        - Updates plan_dict[requires[idx]['checksum']] with calculated value
        - Returns PASS
        """
        # Create artifact with known content
        artifact_path = tmp_path / "docs" / "openapi.yaml"
        artifact_path.parent.mkdir(parents=True)
        artifact_content = "openapi: 3.0.0\ninfo:\n  title: Test API"
        artifact_path.write_bytes(artifact_content.encode())

        # Expected checksum (what we'll calculate)
        expected_checksum = hashlib.sha256(artifact_content.encode()).hexdigest()

        # Plan starts with null checksum (first run)
        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": None,  # ← Key: first run has null checksum
                        }
                    ]
                }
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        # Should PASS
        assert result.status == "PASS"

        # plan_dict should be updated with calculated checksum
        actual_checksum = plan_dict["dependencies"]["contracts"]["requires"][0][
            "checksum"
        ]
        assert actual_checksum == expected_checksum, (
            f"Checksum not updated in plan_dict. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )

    def test_contract_verify_null_checksum_with_multiple_artifacts(
        self, tmp_path: Path
    ) -> None:
        """Test: multiple artifacts with null checksums → all calculated and updated."""
        # Create first artifact
        artifact1_path = tmp_path / "docs" / "openapi.yaml"
        artifact1_path.parent.mkdir(parents=True)
        artifact1_content = "openapi spec"
        artifact1_path.write_bytes(artifact1_content.encode())
        checksum1 = hashlib.sha256(artifact1_content.encode()).hexdigest()

        # Create second artifact
        artifact2_path = tmp_path / "schemas" / "models.json"
        artifact2_path.parent.mkdir(parents=True)
        artifact2_content = '{"User": {"type": "object"}}'
        artifact2_path.write_bytes(artifact2_content.encode())
        checksum2 = hashlib.sha256(artifact2_content.encode()).hexdigest()

        # Plan with null checksums
        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": None,
                        },
                        {
                            "source_repo": "backend",
                            "artifact": "schemas",
                            "path": "schemas/models.json",
                            "checksum": None,
                        },
                    ]
                }
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        # Should PASS
        assert result.status == "PASS"

        # Both checksums should be updated
        assert (
            plan_dict["dependencies"]["contracts"]["requires"][0]["checksum"]
            == checksum1
        )
        assert (
            plan_dict["dependencies"]["contracts"]["requires"][1]["checksum"]
            == checksum2
        )

    def test_contract_verify_null_checksum_missing_artifact_fails(
        self, tmp_path: Path
    ) -> None:
        """Test: null checksum but artifact missing → still FAIL.
        
        Even if checksum is null, if the artifact is missing, verify should fail.
        """
        # Artifact does NOT exist
        plan_dict = {
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
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        # Should FAIL because artifact is missing
        assert result.status == "FAIL"
        assert "missing" in result.reason.lower()

    def test_contract_verify_existing_checksum_still_validates(
        self, tmp_path: Path
    ) -> None:
        """Test: after first run (checksum populated), subsequent runs still validate.
        
        If checksum is not null, it should still be validated against actual file.
        """
        # Create artifact with known content
        artifact_path = tmp_path / "docs" / "openapi.yaml"
        artifact_path.parent.mkdir(parents=True)
        artifact_content = "openapi: 3.0.0"
        artifact_path.write_bytes(artifact_content.encode())

        wrong_checksum = "sha256:wrongchecksumvalue"

        # Plan with existing (but wrong) checksum
        plan_dict = {
            "dependencies": {
                "contracts": {
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "checksum": wrong_checksum,
                        }
                    ]
                }
            }
        }

        repo_root = tmp_path

        result = verify_contracts(plan_dict, repo_root)

        # Should FAIL because checksum doesn't match
        assert result.status == "FAIL"
        assert "mismatch" in result.reason.lower() or "checksum" in result.reason.lower()

