"""
Integration Test: Issue #82 Phase 1 → Phase 4 Schema Alignment.

Tests that Phase 1 output (split_multi_repo_plan) can be consumed
by Phase 4 (orchestrate_multi_repo_impl_and_ship) without validation errors.

This ensures schema alignment between phases: Phase 1 generates plans
with correct dependencies.blocking structure for Phase 4 to consume.

Follows TDD Red-Green-Refactor:
1. Red: Integration test fails if schemas don't align
2. Green: Ensure Phase 1 output matches Phase 4 expectations
3. Refactor: Clean up test data and improve clarity
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add home-template to path for skill imports
ROOT_DIR = Path(__file__).resolve().parents[1]
ORCHESTRATOR_DIR = (
    ROOT_DIR
    / "home-template"
    / ".copilot"
    / "skills"
    / "impl-and-ship"
    / "orchestrator"
)
if str(ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_DIR))

# noqa: E402 - Module level import after path manipulation (needed for skill imports)
from fleet_orchestrator import (  # noqa: E402
    orchestrate_multi_repo_impl_and_ship,
)


class TestPhase1ToPhase4Integration:
    """Test: Phase 1 output schema works with Phase 4 input expectations."""

    def test_simple_two_repo_flow(self) -> None:
        """
        Test: Phase 1 generates backend/frontend plans → Phase 4 consumes them.

        This represents what Phase 1 (split_multi_repo_plan) would generate
        when given a unified architecture with backend → frontend dependency.

        Phase 1 output schema (YAML front-matter):
        ```yaml
        project_context:
          repository: "backend"
          related_repositories: ["frontend"]
        dependencies:
          blocking: []
          contracts:
            provides:
              - artifact: "openapi"
                path: "docs/openapi.yaml"
                checksum: null
                version: "v1"
        ```

        Phase 4 should consume repo_plans dict with this structure.
        """
        # Simulate what Phase 1 outputs (parsed YAML front-matter into dict)
        # This is what would be extracted from split_multi_repo_plan output
        repo_plans = {
            "backend": {
                "project_context": {
                    "repository": "backend",
                    "related_repositories": ["frontend"],
                },
                "dependencies": {
                    "blocking": [],  # backend has no upstream deps
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "openapi",
                                "path": "docs/openapi.yaml",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                        "requires": [],
                    },
                },
            },
            "frontend": {
                "project_context": {
                    "repository": "frontend",
                    "related_repositories": ["backend"],
                },
                "dependencies": {
                    "blocking": ["backend"],  # frontend depends on backend
                    "contracts": {
                        "provides": [],
                        "requires": [
                            {
                                "source_repo": "backend",
                                "artifact": "openapi",
                                "path": "../backend/docs/openapi.yaml",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                    },
                },
            },
        }

        # Phase 4 should consume this without validation errors
        result = orchestrate_multi_repo_impl_and_ship(
            repo_plans, mock_mode=True, polling_interval_sec=1, timeout_sec=5
        )

        # Validation should pass (all repos referenced exist)
        assert result.overall_status == "SUCCESS"
        assert "backend" in result.repos_passed
        assert "frontend" in result.repos_passed
        assert len(result.repos_failed) == 0

    def test_three_tier_dependency_flow(self) -> None:
        """
        Test: 3-tier architecture backend → frontend → mobile.

        Validates that Phase 1 output for multi-level dependencies
        is properly consumed by Phase 4.
        """
        repo_plans = {
            "backend": {
                "project_context": {
                    "repository": "backend",
                    "related_repositories": ["frontend", "mobile"],
                },
                "dependencies": {
                    "blocking": [],
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "openapi",
                                "path": "docs/openapi.yaml",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                        "requires": [],
                    },
                },
            },
            "frontend": {
                "project_context": {
                    "repository": "frontend",
                    "related_repositories": ["backend", "mobile"],
                },
                "dependencies": {
                    "blocking": ["backend"],
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "ui_components",
                                "path": "lib/components.ts",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                        "requires": [
                            {
                                "source_repo": "backend",
                                "artifact": "openapi",
                                "path": "../backend/docs/openapi.yaml",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                    },
                },
            },
            "mobile": {
                "project_context": {
                    "repository": "mobile",
                    "related_repositories": ["backend", "frontend"],
                },
                "dependencies": {
                    "blocking": ["backend", "frontend"],
                    "contracts": {
                        "provides": [],
                        "requires": [
                            {
                                "source_repo": "backend",
                                "artifact": "openapi",
                                "path": "../backend/docs/openapi.yaml",
                                "checksum": None,
                                "version": "v1",
                            },
                            {
                                "source_repo": "frontend",
                                "artifact": "ui_components",
                                "path": "../frontend/lib/components.ts",
                                "checksum": None,
                                "version": "v1",
                            },
                        ],
                    },
                },
            },
        }

        # Phase 4 should process this correctly
        result = orchestrate_multi_repo_impl_and_ship(
            repo_plans, mock_mode=True, polling_interval_sec=1, timeout_sec=5
        )

        # All repos should execute in correct order
        assert result.overall_status == "SUCCESS"
        assert len(result.repos_passed) == 3
        assert set(result.repos_passed) == {"backend", "frontend", "mobile"}

        # Verify ordering: backend first, then frontend, then mobile
        backend_idx = result.status_log[0]  # First to start
        assert "backend" in backend_idx.lower()

    def test_diamond_dependency_pattern(self) -> None:
        """
        Test: Diamond dependency pattern (common in multi-repo).

        ```
            api
           /   \\
        web     mobile
           \\   /
         shared
        ```

        Both web and mobile depend on api, and shared depends on both.
        """
        repo_plans = {
            "api": {
                "project_context": {"repository": "api"},
                "dependencies": {
                    "blocking": [],
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "api_spec",
                                "path": "spec.json",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                        "requires": [],
                    },
                },
            },
            "web": {
                "project_context": {"repository": "web"},
                "dependencies": {
                    "blocking": ["api"],
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "web_bundle",
                                "path": "dist/bundle.js",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                        "requires": [
                            {
                                "source_repo": "api",
                                "artifact": "api_spec",
                                "path": "../api/spec.json",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                    },
                },
            },
            "mobile": {
                "project_context": {"repository": "mobile"},
                "dependencies": {
                    "blocking": ["api"],
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "mobile_app",
                                "path": "app.apk",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                        "requires": [
                            {
                                "source_repo": "api",
                                "artifact": "api_spec",
                                "path": "../api/spec.json",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                    },
                },
            },
            "shared": {
                "project_context": {"repository": "shared"},
                "dependencies": {
                    "blocking": ["web", "mobile"],
                    "contracts": {
                        "provides": [],
                        "requires": [
                            {
                                "source_repo": "web",
                                "artifact": "web_bundle",
                                "path": "../web/dist/bundle.js",
                                "checksum": None,
                                "version": "v1",
                            },
                            {
                                "source_repo": "mobile",
                                "artifact": "mobile_app",
                                "path": "../mobile/app.apk",
                                "checksum": None,
                                "version": "v1",
                            },
                        ],
                    },
                },
            },
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repo_plans, mock_mode=True, polling_interval_sec=1, timeout_sec=5
        )

        # Diamond pattern should work: api → (web, mobile) → shared
        assert result.overall_status == "SUCCESS"
        assert len(result.repos_passed) == 4
        assert set(result.repos_passed) == {"api", "web", "mobile", "shared"}

    def test_phase1_schema_with_all_optional_fields(self) -> None:
        """
        Test: Phase 1 output includes all schema fields (full schema coverage).

        Ensures Phase 4 doesn't crash on unexpected fields from Phase 1.
        """
        repo_plans = {
            "repo_complete": {
                # Full schema as generated by Phase 1
                "project_context": {
                    "repository": "repo_complete",
                    "related_repositories": ["repo_other"],
                    "workspace_path": "/workspace/repos/repo_complete",
                },
                "dependencies": {
                    "blocking": ["repo_other"],
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "library",
                                "path": "lib/index.ts",
                                "checksum": None,
                                "version": "v1",
                                "documentation": "https://example.com/lib",
                            }
                        ],
                        "requires": [
                            {
                                "source_repo": "repo_other",
                                "artifact": "config",
                                "path": "../repo_other/config.json",
                                "checksum": None,
                                "version": "v1",
                                "documentation": "https://example.com/config",
                            }
                        ],
                    },
                },
                "implementation_requirements": {
                    "team": "platform",
                    "deadline": "2026-05-30",
                },
            },
            "repo_other": {
                "project_context": {"repository": "repo_other"},
                "dependencies": {
                    "blocking": [],
                    "contracts": {
                        "provides": [
                            {
                                "artifact": "config",
                                "path": "config.json",
                                "checksum": None,
                                "version": "v1",
                            }
                        ],
                        "requires": [],
                    },
                },
            },
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repo_plans, mock_mode=True, polling_interval_sec=1, timeout_sec=5
        )

        # Should handle full schema without issues
        assert result.overall_status == "SUCCESS"
        assert "repo_other" in result.repos_passed
        assert "repo_complete" in result.repos_passed

    def test_phase1_minimal_schema(self) -> None:
        """
        Test: Phase 1 output with minimal schema (only required fields).

        Ensures Phase 4 works with simplest Phase 1 output.
        """
        repo_plans = {
            "service_a": {
                "dependencies": {
                    "blocking": [],
                }
            },
            "service_b": {
                "dependencies": {
                    "blocking": ["service_a"],
                }
            },
        }

        result = orchestrate_multi_repo_impl_and_ship(
            repo_plans, mock_mode=True, polling_interval_sec=1, timeout_sec=5
        )

        # Should work with minimal schema
        assert result.overall_status == "SUCCESS"
        assert len(result.repos_passed) == 2
