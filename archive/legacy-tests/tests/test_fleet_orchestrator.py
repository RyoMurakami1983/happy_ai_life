"""
Tests for fleet orchestrator in impl-and-ship.

Follows TDD Red-Green-Refactor:
1. Red: Minimal failing test that captures expected behavior
2. Green: Minimal implementation to pass the test
3. Refactor: Clean up code while maintaining passing tests

Tests cover:
- Circular dependency detection
- Linear dependency ordering
- Parallel execution of independent repos
- Blocking dependency enforcement
- Contract verification blocking on mismatch
- Upstream failure propagating to downstream
- Status polling loop (30s intervals)
- Final report generation
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

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
    CircularDependencyError,
    OrchestratorResult,
    detect_circular_dependencies,
    orchestrate_multi_repo_impl_and_ship,
    resolve_dependency_order,
)


class TestCircularDependencyDetection:
    """Test: Tarjan's algorithm detects cycles in dependency graph."""

    def test_no_cycle_linear_chain(self) -> None:
        """Test: backend -> frontend -> mobile (no cycle) → no error."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
            "mobile": {"dependencies": {"blocking": ["frontend"]}},
        }

        # Should not raise - linear chain is not a cycle
        detect_circular_dependencies(repos)

    def test_simple_cycle_two_repos(self) -> None:
        """Test: A -> B -> A (simple cycle) → CircularDependencyError."""
        repos = {
            "repo_a": {"dependencies": {"blocking": ["repo_b"]}},
            "repo_b": {"dependencies": {"blocking": ["repo_a"]}},
        }

        with pytest.raises(CircularDependencyError) as exc_info:
            detect_circular_dependencies(repos)

        error_msg = str(exc_info.value)
        assert "cycle" in error_msg.lower()
        # Should mention repos in the cycle
        assert "repo_a" in error_msg or "repo_b" in error_msg

    def test_complex_cycle_three_repos(self) -> None:
        """Test: A -> B -> C -> A (complex cycle) → CircularDependencyError."""
        repos = {
            "repo_a": {"dependencies": {"blocking": ["repo_b"]}},
            "repo_b": {"dependencies": {"blocking": ["repo_c"]}},
            "repo_c": {"dependencies": {"blocking": ["repo_a"]}},
        }

        with pytest.raises(CircularDependencyError) as exc_info:
            detect_circular_dependencies(repos)

        error_msg = str(exc_info.value)
        assert "cycle" in error_msg.lower()

    def test_self_referential_cycle(self) -> None:
        """Test: A -> A (self-reference) → CircularDependencyError."""
        repos = {
            "repo_a": {"dependencies": {"blocking": ["repo_a"]}},
        }

        with pytest.raises(CircularDependencyError) as exc_info:
            detect_circular_dependencies(repos)

        error_msg = str(exc_info.value)
        assert "cycle" in error_msg.lower()

    def test_cycle_with_independent_repos(self) -> None:
        """Test: Independent repos + cycle in subset → CircularDependencyError."""
        repos = {
            "repo_x": {"dependencies": {"blocking": []}},  # independent
            "repo_a": {"dependencies": {"blocking": ["repo_b"]}},  # part of cycle
            "repo_b": {"dependencies": {"blocking": ["repo_a"]}},  # part of cycle
        }

        with pytest.raises(CircularDependencyError) as exc_info:
            detect_circular_dependencies(repos)

        error_msg = str(exc_info.value)
        assert "cycle" in error_msg.lower()


class TestDependencyResolution:
    """Test: DAG resolution orders repos by blocking dependencies."""

    def test_linear_dependency_ordering(self) -> None:
        """Test: backend -> frontend -> mobile ordered correctly."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
            "mobile": {"dependencies": {"blocking": ["frontend"]}},
        }

        order = resolve_dependency_order(repos)

        # backend must come before frontend, frontend before mobile
        backend_idx = order.index("backend")
        frontend_idx = order.index("frontend")
        mobile_idx = order.index("mobile")
        assert backend_idx < frontend_idx < mobile_idx

    def test_independent_repos_first(self) -> None:
        """Test: repos with no blocking deps start first."""
        repos = {
            "repo_a": {"dependencies": {"blocking": []}},
            "repo_b": {"dependencies": {"blocking": []}},
            "repo_c": {"dependencies": {"blocking": ["repo_a"]}},
        }

        order = resolve_dependency_order(repos)

        # repo_a and repo_b should come before repo_c
        repo_a_idx = order.index("repo_a")
        repo_b_idx = order.index("repo_b")
        repo_c_idx = order.index("repo_c")
        assert repo_a_idx < repo_c_idx and repo_b_idx < repo_c_idx

    def test_parallel_independent_repos(self) -> None:
        """Test: multiple independent repos in parallel tier."""
        repos = {
            "repo_a": {"dependencies": {"blocking": []}},
            "repo_b": {"dependencies": {"blocking": []}},
            "repo_c": {"dependencies": {"blocking": []}},
        }

        order = resolve_dependency_order(repos)

        # All three should be in order (parallel execution)
        assert len(order) == 3
        assert set(order) == {"repo_a", "repo_b", "repo_c"}

    def test_complex_dag_resolution(self) -> None:
        """Test: complex DAG with multiple levels."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
            "mobile": {"dependencies": {"blocking": ["backend"]}},
            "docs": {"dependencies": {"blocking": ["frontend", "mobile"]}},
        }

        order = resolve_dependency_order(repos)

        # backend first, then frontend/mobile (independent of each other), then docs
        backend_idx = order.index("backend")
        frontend_idx = order.index("frontend")
        mobile_idx = order.index("mobile")
        docs_idx = order.index("docs")

        assert backend_idx < frontend_idx
        assert backend_idx < mobile_idx
        assert frontend_idx < docs_idx
        assert mobile_idx < docs_idx


class TestParallelExecutionScheduling:
    """Test: Independent repos start in parallel."""

    def test_parallel_execution_independent_repos(self) -> None:
        """Test: 3 independent repos start in parallel (same execution tier)."""
        repos = {
            "repo_a": {"dependencies": {"blocking": []}},
            "repo_b": {"dependencies": {"blocking": []}},
            "repo_c": {"dependencies": {"blocking": []}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        # All 3 should have been started and polled
        assert result.overall_status == "SUCCESS"
        assert len(result.repos_passed) == 3
        assert set(result.repos_passed) == {"repo_a", "repo_b", "repo_c"}


class TestBlockingDependencyEnforcement:
    """Test: Downstream repos wait for upstream to complete."""

    def test_blocking_dependency_enforcement(self) -> None:
        """Test: frontend waits for backend before starting."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        # Both should pass, but frontend only after backend
        assert result.overall_status == "SUCCESS"
        assert "backend" in result.repos_passed
        assert "frontend" in result.repos_passed

    def test_blocking_multiple_dependencies(self) -> None:
        """Test: repo waits for all blocking deps."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": []}},
            "docs": {"dependencies": {"blocking": ["backend", "frontend"]}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        # All should pass
        assert result.overall_status == "SUCCESS"
        assert len(result.repos_passed) == 3


class TestContractVerificationBlocking:
    """Test: Checksum mismatch blocks downstream repo."""

    def test_contract_verification_blocks_mismatch(self) -> None:
        """Test: checksum mismatch blocks downstream."""
        repos = {
            "backend": {
                "dependencies": {
                    "blocking": [],
                    "contracts": {"provides": [{"artifact": "api", "checksum": "sha256:abc123"}]},
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

        # frontend should be blocked, backend passed
        assert "backend" in result.repos_passed
        assert "frontend" in result.repos_blocked
        assert result.overall_status == "FAILURE"


class TestUpstreamFailureBlocking:
    """Test: Upstream failure blocks downstream (auto-block)."""

    def test_upstream_failure_blocks_downstream(self) -> None:
        """Test: if backend fails, frontend is auto-blocked."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
        }

        # Mock backend to fail
        result = orchestrate_multi_repo_impl_and_ship(
            repos,
            polling_interval_sec=1,
            timeout_sec=5,
            mock_mode=True,
            mock_failures=["backend"],
        )

        # backend failed, frontend blocked
        assert "backend" in result.repos_failed
        assert "frontend" in result.repos_blocked
        assert result.overall_status == "FAILURE"

    def test_upstream_failure_propagates_through_chain(self) -> None:
        """Test: backend failure → frontend blocked → mobile blocked."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
            "mobile": {"dependencies": {"blocking": ["frontend"]}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos,
            polling_interval_sec=1,
            timeout_sec=5,
            mock_mode=True,
            mock_failures=["backend"],
        )

        # backend failed, both downstream blocked
        assert "backend" in result.repos_failed
        assert "frontend" in result.repos_blocked
        assert "mobile" in result.repos_blocked
        assert result.overall_status == "FAILURE"


class TestStatusPollingLoop:
    """Test: Polling loop runs at 30s intervals."""

    def test_status_polling_loop(self) -> None:
        """Test: status is polled periodically."""
        repos = {
            "repo_a": {"dependencies": {"blocking": []}},
            "repo_b": {"dependencies": {"blocking": ["repo_a"]}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        # Should have polled and completed successfully
        assert result.overall_status == "SUCCESS"
        assert len(result.status_log) > 0


class TestFinalReportGeneration:
    """Test: Generate final orchestration summary."""

    def test_final_report_all_pass(self) -> None:
        """Test: summary shows X PASS, Y FAIL, Z BLOCKED."""
        repos = {
            "repo_a": {"dependencies": {"blocking": []}},
            "repo_b": {"dependencies": {"blocking": ["repo_a"]}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        assert result.overall_status == "SUCCESS"
        assert len(result.repos_passed) == 2
        assert len(result.repos_failed) == 0
        assert len(result.repos_blocked) == 0
        # Status log should have entries
        assert len(result.status_log) > 0

    def test_final_report_mixed_status(self) -> None:
        """Test: report shows mixed PASS/FAIL/BLOCKED."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
            "mobile": {"dependencies": {"blocking": ["frontend"]}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos,
            polling_interval_sec=1,
            timeout_sec=5,
            mock_mode=True,
            mock_failures=["frontend"],
        )

        # backend passed, frontend failed, mobile blocked
        assert "backend" in result.repos_passed
        assert "frontend" in result.repos_failed
        assert "mobile" in result.repos_blocked
        assert result.overall_status == "FAILURE"

    def test_final_report_actionable_messages(self) -> None:
        """Test: status log messages are actionable."""
        repos = {
            "backend": {"dependencies": {"blocking": []}},
            "frontend": {"dependencies": {"blocking": ["backend"]}},
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repos,
            polling_interval_sec=1,
            timeout_sec=5,
            mock_mode=True,
            mock_failures=["backend"],
        )

        # Status log should explain why frontend is blocked
        status_text = "\n".join(result.status_log)
        assert "frontend" in status_text.lower()
        assert "blocked" in status_text.lower() or "fail" in status_text.lower()


class TestOrchestratorResultDataclass:
    """Test: OrchestratorResult dataclass structure."""

    def test_orchestrator_result_fields(self) -> None:
        """Test: OrchestratorResult has expected fields."""
        result = OrchestratorResult(
            overall_status="SUCCESS",
            repos_passed=["repo_a", "repo_b"],
            repos_failed=[],
            repos_blocked=[],
            status_log=["Started repo_a", "Started repo_b"],
        )

        assert result.overall_status == "SUCCESS"
        assert result.repos_passed == ["repo_a", "repo_b"]
        assert result.repos_failed == []
        assert result.repos_blocked == []
        assert len(result.status_log) == 2


class TestEmptyRepoList:
    """Test: Edge case with no repos."""

    def test_empty_repo_list(self) -> None:
        """Test: empty repo list → SUCCESS with no repos."""
        repos: dict[str, Any] = {}

        result = orchestrate_multi_repo_impl_and_ship(
            repos, polling_interval_sec=1, timeout_sec=5, mock_mode=True
        )

        assert result.overall_status == "SUCCESS"
        assert len(result.repos_passed) == 0
        assert len(result.repos_failed) == 0
        assert len(result.repos_blocked) == 0
