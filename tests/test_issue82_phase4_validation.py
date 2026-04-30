"""
Test: Issue #82 Phase 4 - Input Validation for Unknown Dependencies.

Tests for validating that references to non-existent repos are caught
before orchestration execution, preventing KeyError crashes.

Follows TDD Red-Green-Refactor:
1. Red: Test fails because validation doesn't exist yet
2. Green: Add validation function and call it
3. Refactor: Clean up and integrate
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add plugin package to path for skill imports
ROOT_DIR = Path(__file__).resolve().parents[1]
ORCHESTRATOR_DIR = (
    ROOT_DIR
    / "plugins"
    / "happy-coding"
    / "skills"
    / "impl-and-ship"
    / "orchestrator"
)
if str(ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_DIR))

# noqa: E402 - Module level import after path manipulation (needed for skill imports)
from fleet_orchestrator import (  # noqa: E402
    orchestrate_multi_repo_impl_and_ship,
    validate_repo_dependencies,
)


class TestValidateRepoDependencies:
    """Test: validate_repo_dependencies function validates repo references."""

    def test_validation_passes_no_dependencies(self) -> None:
        """Test: repo with no dependencies passes validation."""
        repo_plans = {
            "backend": {"dependencies": {"blocking": []}},
        }
        errors = validate_repo_dependencies(repo_plans)
        assert errors == []

    def test_validation_passes_valid_dependencies(self) -> None:
        """Test: repo that references existing repos passes validation."""
        repo_plans = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
        }
        errors = validate_repo_dependencies(repo_plans)
        assert errors == []

    def test_validation_catches_unknown_single_dependency(self) -> None:
        """Test: reference to non-existent repo is caught."""
        repo_plans = {
            "frontend": {"dependencies": {"blocking": ["nonexistent_repo"]}},
        }
        errors = validate_repo_dependencies(repo_plans)
        assert len(errors) == 1
        assert "frontend" in errors[0]
        assert "nonexistent_repo" in errors[0]

    def test_validation_catches_unknown_in_multiple_dependencies(self) -> None:
        """Test: unknown repo in a list of dependencies is caught."""
        repo_plans = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend", "nonexistent"]}},
        }
        errors = validate_repo_dependencies(repo_plans)
        assert len(errors) == 1
        assert "frontend" in errors[0]
        assert "nonexistent" in errors[0]

    def test_validation_catches_multiple_unknown_dependencies(self) -> None:
        """Test: multiple repos with unknown dependencies all caught."""
        repo_plans = {
            "frontend": {"dependencies": {"blocking": ["unknown1"]}},
            "mobile": {"dependencies": {"blocking": ["unknown2"]}},
        }
        errors = validate_repo_dependencies(repo_plans)
        assert len(errors) == 2
        # Both errors should be present
        error_text = "\n".join(errors)
        assert "frontend" in error_text
        assert "mobile" in error_text
        assert "unknown1" in error_text
        assert "unknown2" in error_text

    def test_validation_handles_missing_dependencies_key(self) -> None:
        """Test: repo without 'dependencies' key doesn't crash."""
        repo_plans = {
            "backend": {},  # Missing 'dependencies' key
        }
        errors = validate_repo_dependencies(repo_plans)
        assert errors == []

    def test_validation_handles_missing_blocking_key(self) -> None:
        """Test: repo without 'blocking' key doesn't crash."""
        repo_plans = {
            "backend": {"dependencies": {}},  # Missing 'blocking' key
        }
        errors = validate_repo_dependencies(repo_plans)
        assert errors == []

    def test_validation_returns_list(self) -> None:
        """Test: validation always returns a list."""
        repo_plans = {"backend": {"dependencies": {"blocking": []}}}
        errors = validate_repo_dependencies(repo_plans)
        assert isinstance(errors, list)


class TestOrchestratorValidatesInput:
    """Test: orchestrate_multi_repo_impl_and_ship validates input before execution."""

    def test_orchestrator_validates_unknown_dependency(self) -> None:
        """Test: Unknown repo reference causes FAILURE with validation error."""
        repo_plans = {
            "frontend": {"dependencies": {"blocking": ["backend", "nonexistent_repo"]}},
        }
        result = orchestrate_multi_repo_impl_and_ship(repo_plans, mock_mode=True)

        # Should fail validation
        assert result.overall_status == "FAILURE"
        # All repos should be marked failed (due to validation failure)
        assert set(result.repos_failed) == {"frontend"}
        # Error message should mention the unknown repo
        error_text = "\n".join(result.status_log)
        assert "nonexistent_repo" in error_text

    def test_orchestrator_validation_error_appears_in_status_log(self) -> None:
        """Test: Validation error message is clear in status log."""
        repo_plans = {
            "mobile": {"dependencies": {"blocking": ["unknown_backend"]}},
        }
        result = orchestrate_multi_repo_impl_and_ship(repo_plans, mock_mode=True)

        assert result.overall_status == "FAILURE"
        status_text = "\n".join(result.status_log)
        assert "validation" in status_text.lower() or "unknown" in status_text.lower()
        assert "unknown_backend" in status_text

    def test_orchestrator_runs_when_validation_passes(self) -> None:
        """Test: Orchestrator runs normally when validation passes."""
        repo_plans = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
        }
        result = orchestrate_multi_repo_impl_and_ship(
            repo_plans, mock_mode=True, polling_interval_sec=1, timeout_sec=5
        )

        # Should succeed (valid dependencies)
        assert result.overall_status == "SUCCESS"
        # No repos should be failed due to validation
        assert len(result.repos_failed) == 0

    def test_orchestrator_validation_before_circular_check(self) -> None:
        """Test: Validation runs before circular dependency check."""
        # This has both a missing repo AND a circular dependency
        # Validation should catch the missing repo first
        repo_plans = {
            "repo_a": {"dependencies": {"blocking": ["nonexistent"]}},
            "repo_b": {"dependencies": {"blocking": ["repo_a"]}},
        }
        result = orchestrate_multi_repo_impl_and_ship(repo_plans, mock_mode=True)

        # Should fail validation for unknown repo (before circular check)
        assert result.overall_status == "FAILURE"
        status_text = "\n".join(result.status_log)
        assert "nonexistent" in status_text
