"""
Tests for split_multi_repo_plan sub-skill.

Follows TDD Red-Green-Refactor:
1. Red: Minimal failing test that captures expected behavior
2. Green: Minimal implementation to pass the test
3. Refactor: Clean up code while maintaining passing tests
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add plugin package to path for skill imports
ROOT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT_DIR / "plugins" / "happy-coding" / "skills" / "sdd" / "sub_skills" / "split_multi_repo_plan"
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

# noqa: E402 - Module level import after path manipulation (needed for skill imports)
from main import (  # noqa: E402
    build_dependency_graph,
    calculate_checksums,
    find_cycles,
    generate_plan_md,
    split_multi_repo_plan,
    validate_contracts,
    CircularDependencyError,
    ContractMismatchError,
)


class TestBuildDependencyGraph:
    """Test DAG construction from repos list."""

    def test_simple_linear_dependency(self) -> None:
        """Test: backend -> frontend (no cycles)."""
        repos = [
            {
                "name": "backend",
                "modules": ["api_server", "database"],
                "provides": [
                    {"artifact": "openapi", "path": "docs/openapi.yaml", "version": "v1"}
                ],
            },
            {
                "name": "frontend",
                "modules": ["web_ui"],
                "requires": [
                    {
                        "source_repo": "backend",
                        "artifact": "openapi",
                        "version": "v1",
                    }
                ],
            },
        ]

        graph = build_dependency_graph(repos)

        # Graph should have nodes for both repos
        assert "backend" in graph
        assert "frontend" in graph

        # Frontend depends on backend
        assert "backend" in graph["frontend"]


class TestFindCycles:
    """Test cycle detection in dependency graph."""

    def test_simple_linear_no_cycle(self) -> None:
        """Test: backend -> frontend (no cycles detected)."""
        graph = {"backend": [], "frontend": ["backend"]}
        cycles = find_cycles(graph)
        assert cycles == []

    def test_circular_dependency_detected(self) -> None:
        """Test: backend ↔ frontend (cycle detected)."""
        graph = {"backend": ["frontend"], "frontend": ["backend"]}
        cycles = find_cycles(graph)

        # Should detect at least one cycle
        assert len(cycles) > 0
        # Cycle should contain both nodes
        assert "backend" in cycles[0]
        assert "frontend" in cycles[0]


class TestValidateContracts:
    """Test provides/requires contract matching."""

    def test_matching_contract_passes(self) -> None:
        """Test: requires/provides match → no errors."""
        repos = [
            {
                "name": "backend",
                "modules": ["api_server"],
                "provides": [
                    {
                        "artifact": "openapi",
                        "path": "docs/openapi.yaml",
                        "version": "v1",
                    }
                ],
            },
            {
                "name": "frontend",
                "modules": ["web_ui"],
                "requires": [
                    {
                        "source_repo": "backend",
                        "artifact": "openapi",
                        "version": "v1",
                    }
                ],
            },
        ]

        errors = validate_contracts(repos)
        assert errors == []

    def test_missing_required_artifact_fails(self) -> None:
        """Test: requires artifact that doesn't exist → error."""
        repos = [
            {
                "name": "backend",
                "modules": ["api_server"],
                "provides": [],  # No openapi artifact
            },
            {
                "name": "frontend",
                "modules": ["web_ui"],
                "requires": [
                    {
                        "source_repo": "backend",
                        "artifact": "openapi",
                        "version": "v1",
                    }
                ],
            },
        ]

        errors = validate_contracts(repos)
        assert len(errors) > 0
        assert "openapi" in errors[0].lower()


class TestCalculateChecksums:
    """Test checksum placeholder generation for artifacts."""

    def test_checksum_generation(self) -> None:
        """Test: checksums are null (placeholder) for all artifacts."""
        provides = [
            {"artifact": "openapi", "path": "docs/openapi.yaml", "version": "v1"},
            {"artifact": "config", "path": "config.json", "version": "v1"},
        ]

        checksums = calculate_checksums(provides)

        # Should have 2 checksums
        assert len(checksums) == 2

        # Each should have checksum field set to None (placeholder)
        for item in checksums:
            assert "checksum" in item
            assert item["checksum"] is None


class TestGeneratePlanMd:
    """Test YAML front-matter + narrative markdown generation."""

    def test_plan_md_output_format(self) -> None:
        """Test: generates markdown with YAML front-matter."""
        repo = {
            "name": "backend",
            "modules": ["api_server", "database"],
            "provides": [
                {"artifact": "openapi", "path": "docs/openapi.yaml", "version": "v1"}
            ],
        }
        all_repos = [repo]

        plan_md = generate_plan_md(repo, all_repos)

        # Should start with YAML front-matter
        assert plan_md.startswith("---\n")

        # Should contain project_context
        assert "project_context:" in plan_md
        assert "backend" in plan_md

        # Should have repository field
        assert "repository:" in plan_md

        # Should contain contracts section (new schema)
        assert "contracts:" in plan_md

        # Should close YAML with --- (appears twice: opening and closing)
        lines = plan_md.split("\n")
        yaml_close_count = sum(1 for line in lines if line.strip() == "---")
        assert yaml_close_count >= 2  # At least opening and closing

        # Should have narrative section
        assert "# Backend Implementation Plan" in plan_md or "# " in plan_md

    def test_plan_md_provides_in_contracts(self) -> None:
        """Test: provides artifacts under contracts.provides (new schema)."""
        repo = {
            "name": "backend",
            "modules": ["api_server"],
            "provides": [
                {"artifact": "openapi", "path": "docs/openapi.yaml", "version": "v1"}
            ],
        }
        all_repos = [repo]

        plan_md = generate_plan_md(repo, all_repos)

        # Should have contracts.provides section
        assert "contracts:" in plan_md
        assert "provides:" in plan_md
        # Field name should be "artifact" (not "name")
        assert "artifact: \"openapi\"" in plan_md or "artifact: openapi" in plan_md

    def test_plan_md_requires_in_contracts(self) -> None:
        """Test: requires artifacts under contracts.requires (new schema)."""
        backend_repo = {
            "name": "backend",
            "modules": ["api_server"],
            "provides": [
                {"artifact": "openapi", "path": "docs/openapi.yaml", "version": "v1"}
            ],
        }
        frontend_repo = {
            "name": "frontend",
            "modules": ["web_ui"],
            "requires": [
                {
                    "source_repo": "backend",
                    "artifact": "openapi",
                    "version": "v1",
                }
            ],
        }
        all_repos = [backend_repo, frontend_repo]

        plan_md = generate_plan_md(frontend_repo, all_repos)

        # Should have contracts.requires section
        assert "contracts:" in plan_md
        assert "requires:" in plan_md
        # Should include source_repo and artifact fields
        assert "source_repo:" in plan_md
        assert "artifact:" in plan_md

    def test_plan_md_checksum_is_null(self) -> None:
        """Test: checksums are null (placeholder) in new schema."""
        repo = {
            "name": "backend",
            "modules": ["api_server"],
            "provides": [
                {"artifact": "openapi", "path": "docs/openapi.yaml", "version": "v1"}
            ],
        }
        all_repos = [repo]

        plan_md = generate_plan_md(repo, all_repos)

        # Checksum should be null (not sha256:...)
        assert "checksum: null" in plan_md or "checksum: ~" in plan_md
        # Should NOT have sha256: prefix
        assert "sha256:" not in plan_md

    def test_plan_md_relative_path_in_requires(self) -> None:
        """Test: requires artifacts have relative path from source repo."""
        backend_repo = {
            "name": "backend",
            "modules": ["api_server"],
            "provides": [
                {"artifact": "openapi", "path": "docs/openapi.yaml", "version": "v1"}
            ],
        }
        frontend_repo = {
            "name": "frontend",
            "modules": ["web_ui"],
            "requires": [
                {
                    "source_repo": "backend",
                    "artifact": "openapi",
                    "version": "v1",
                }
            ],
        }
        all_repos = [backend_repo, frontend_repo]

        plan_md = generate_plan_md(frontend_repo, all_repos)

        # Should include relative path starting with ..
        assert "../backend/" in plan_md


class TestSplitMultiRepoPlan:
    """Test main function: unified architecture → per-repo plans."""

    def test_simple_multi_repo_split(self) -> None:
        """Test: split unified architecture into per-repo plans."""
        unified_architecture = {
            "repos": [
                {
                    "name": "backend",
                    "modules": ["api_server", "database"],
                    "provides": [
                        {
                            "artifact": "openapi",
                            "path": "docs/openapi.yaml",
                            "version": "v1",
                        }
                    ],
                },
                {
                    "name": "frontend",
                    "modules": ["web_ui"],
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "version": "v1",
                        }
                    ],
                },
            ]
        }

        result = split_multi_repo_plan(unified_architecture)

        # Should return dict with repo names as keys
        assert "backend" in result
        assert "frontend" in result

        # Each should have plan_md
        assert "plan_md" in result["backend"]
        assert "plan_md" in result["frontend"]

        # plan_md should be non-empty strings
        assert isinstance(result["backend"]["plan_md"], str)
        assert len(result["backend"]["plan_md"]) > 0


class TestErrorHandling:
    """Test error cases: circular deps, contract mismatches."""

    def test_circular_dependency_raises_error(self) -> None:
        """Test: circular dependency → CircularDependencyError."""
        unified_architecture = {
            "repos": [
                {
                    "name": "backend",
                    "modules": ["api"],
                    "provides": [
                        {"artifact": "api_spec", "path": "spec.yaml", "version": "v1"}
                    ],
                    "requires": [
                        {
                            "source_repo": "frontend",
                            "artifact": "ui_schema",
                            "version": "v1",
                        }
                    ],
                },
                {
                    "name": "frontend",
                    "modules": ["ui"],
                    "provides": [
                        {"artifact": "ui_schema", "path": "schema.json", "version": "v1"}
                    ],
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "api_spec",
                            "version": "v1",
                        }
                    ],
                },
            ]
        }

        with pytest.raises(CircularDependencyError):
            split_multi_repo_plan(unified_architecture)

    def test_contract_mismatch_raises_error(self) -> None:
        """Test: missing artifact → ContractMismatchError."""
        unified_architecture = {
            "repos": [
                {
                    "name": "backend",
                    "modules": ["api"],
                    "provides": [],  # No artifact
                },
                {
                    "name": "frontend",
                    "modules": ["ui"],
                    "requires": [
                        {
                            "source_repo": "backend",
                            "artifact": "openapi",
                            "version": "v1",
                        }
                    ],
                },
            ]
        }

        with pytest.raises(ContractMismatchError):
            split_multi_repo_plan(unified_architecture)
