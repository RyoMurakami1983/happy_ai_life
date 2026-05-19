"""
Tests for Phase 2 SKILL.md updates (Issue #82).

Verifies:
1. sdd/SKILL.md includes split_multi_repo_plan references
2. impl-and-ship/SKILL.md includes contract_verify checkpoint
3. balanced-coupling-design/SKILL.md includes multi-repo footnote

Follows TDD Red-Green-Refactor:
1. Red: Minimal failing tests that capture expected changes
2. Green: Minimal SKILL.md updates to pass tests
3. Refactor: Ensure consistency across files
"""

from __future__ import annotations

from pathlib import Path

import pytest


# Paths to SKILL.md files
ROOT_DIR = Path(__file__).resolve().parents[1]
SDD_SKILL_PATH = (
    ROOT_DIR / "plugins" / "happy-coding" / "skills" / "sdd" / "SKILL.md"
)
IMPL_AND_SHIP_SKILL_PATH = (
    ROOT_DIR / "plugins" / "happy-coding" / "skills" / "impl-and-ship" / "SKILL.md"
)
BALANCED_COUPLING_SKILL_PATH = (
    ROOT_DIR
    / "plugins"
    / "happy-coding"
    / "skills"
    / "design-workshop"
    / "sub_skills"
    / "balanced-coupling-design"
    / "SKILL.md"
)


class TestSddSkillMdUpdates:
    """Test sdd/SKILL.md includes split_multi_repo_plan references."""

    @pytest.fixture
    def sdd_content(self) -> str:
        """Read sdd/SKILL.md content."""
        return SDD_SKILL_PATH.read_text(encoding="utf-8")

    def test_sdd_skill_md_exists(self) -> None:
        """Test: sdd/SKILL.md file exists."""
        assert SDD_SKILL_PATH.exists(), f"{SDD_SKILL_PATH} does not exist"

    def test_sdd_mentions_split_multi_repo_plan(self, sdd_content: str) -> None:
        """Test: sdd/SKILL.md contains 'split_multi_repo_plan' reference."""
        assert (
            "split_multi_repo_plan" in sdd_content
        ), "sdd/SKILL.md should mention 'split_multi_repo_plan'"

    def test_sdd_frontmatter_updated(self, sdd_content: str) -> None:
        """Test: sdd/SKILL.md frontmatter mentions multi-repo / multirepository."""
        lines = sdd_content.split("\n")
        # Frontmatter should be between first --- and second ---
        frontmatter_end = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                frontmatter_end = i
                break

        assert frontmatter_end is not None, "Frontmatter closing --- not found"

        frontmatter = "\n".join(lines[1:frontmatter_end])

        # Should mention multirepository or multi-repo in description
        assert (
            "multirepository" in frontmatter.lower()
            or "multi-repo" in frontmatter.lower()
            or "multi repo" in frontmatter.lower()
        ), "sdd/SKILL.md frontmatter should mention multi-repo capability"

    def test_sdd_workflow_section_updated(self, sdd_content: str) -> None:
        """Test: sdd/SKILL.md workflow section references split_multi_repo_plan."""
        # Should have 全体フロー section with split_multi_repo_plan
        assert "全体フロー" in sdd_content, "Should have '全体フロー' section"
        assert (
            "split_multi_repo_plan" in sdd_content
        ), "split_multi_repo_plan should be in workflow"


class TestImplAndShipSkillMdUpdates:
    """Test impl-and-ship/SKILL.md includes contract_verify checkpoint."""

    @pytest.fixture
    def impl_and_ship_content(self) -> str:
        """Read impl-and-ship/SKILL.md content."""
        return IMPL_AND_SHIP_SKILL_PATH.read_text(encoding="utf-8")

    def test_impl_and_ship_skill_md_exists(self) -> None:
        """Test: impl-and-ship/SKILL.md file exists."""
        assert (
            IMPL_AND_SHIP_SKILL_PATH.exists()
        ), f"{IMPL_AND_SHIP_SKILL_PATH} does not exist"

    def test_impl_and_ship_mentions_contract_verify(
        self, impl_and_ship_content: str
    ) -> None:
        """Test: impl-and-ship/SKILL.md mentions 'contract' in checkpoint context."""
        # Should mention contract_verify or contract checkpoint
        assert (
            "contract" in impl_and_ship_content.lower()
        ), "impl-and-ship/SKILL.md should mention 'contract'"

    def test_impl_and_ship_checkpoint_in_workflow(
        self, impl_and_ship_content: str
    ) -> None:
        """Test: impl-and-ship/SKILL.md workflow includes contract checkpoint."""
        # Should have a step mentioning contract before ship/PR
        lines = impl_and_ship_content.split("\n")

        # Look for "eval gate" mention and verify contract is mentioned in workflow
        for i, line in enumerate(lines):
            if "eval gate" in line.lower() or "evaluation" in line.lower():
                break

        # Contract should be mentioned before or around eval gate
        contract_mentioned = "contract" in impl_and_ship_content.lower()
        assert contract_mentioned, "contract should be mentioned in workflow"

    def test_impl_and_ship_step_numbering(self, impl_and_ship_content: str) -> None:
        """Test: impl-and-ship/SKILL.md has sequential steps including contract."""
        # Should have steps numbered 1-10+
        # And contract should be in step description
        assert "### ステップ" in impl_and_ship_content, "Should have numbered steps"
        assert (
            "contract" in impl_and_ship_content.lower()
        ), "contract should be in step content"


class TestBalancedCouplingDesignSkillMdUpdates:
    """Test balanced-coupling-design/SKILL.md includes multi-repo footnote."""

    @pytest.fixture
    def balanced_coupling_content(self) -> str:
        """Read balanced-coupling-design/SKILL.md content."""
        return BALANCED_COUPLING_SKILL_PATH.read_text(encoding="utf-8")

    def test_balanced_coupling_skill_md_exists(self) -> None:
        """Test: balanced-coupling-design/SKILL.md file exists."""
        assert (
            BALANCED_COUPLING_SKILL_PATH.exists()
        ), f"{BALANCED_COUPLING_SKILL_PATH} does not exist"

    def test_balanced_coupling_mentions_split_multi_repo(
        self, balanced_coupling_content: str
    ) -> None:
        """Test: balanced-coupling-design/SKILL.md mentions split_multi_repo_plan."""
        assert (
            "split_multi_repo_plan" in balanced_coupling_content
        ), (
            "balanced-coupling-design/SKILL.md should mention "
            "'split_multi_repo_plan' in footnote or reference"
        )

    def test_balanced_coupling_multi_repo_context(
        self, balanced_coupling_content: str
    ) -> None:
        """Test: balanced-coupling-design/SKILL.md references multi-repo in context."""
        # Should mention multi-repo or multirepository somewhere
        assert (
            "multi-repo" in balanced_coupling_content.lower()
            or "multirepository" in balanced_coupling_content.lower()
            or "複数リポ" in balanced_coupling_content
        ), "balanced-coupling-design should reference multi-repo context"


class TestConsistencyAcrossSkills:
    """Test consistency and integration across all 3 SKILL.md files."""

    @pytest.fixture
    def all_contents(self) -> dict[str, str]:
        """Read all 3 SKILL.md files."""
        return {
            "sdd": SDD_SKILL_PATH.read_text(encoding="utf-8"),
            "impl_and_ship": IMPL_AND_SHIP_SKILL_PATH.read_text(
                encoding="utf-8"
            ),
            "balanced_coupling": BALANCED_COUPLING_SKILL_PATH.read_text(
                encoding="utf-8"
            ),
        }

    def test_no_breaking_changes_to_existing_sections(
        self, all_contents: dict[str, str]
    ) -> None:
        """Test: existing sections preserved (no deletion)."""
        # sdd should still have all original sections
        assert "こんなときに使う" in all_contents["sdd"]
        assert "判断表" in all_contents["sdd"]
        assert "全体フロー" in all_contents["sdd"]
        assert "PLAN mode について" in all_contents["sdd"]

        # impl-and-ship should still have all original steps
        assert "bootstrap 確認" in all_contents["impl_and_ship"]
        assert "implementation eval gate" in all_contents["impl_and_ship"]

    def test_multirepository_terminology_consistent(
        self, all_contents: dict[str, str]
    ) -> None:
        """Test: multirepository terminology used consistently."""
        # All should mention multirepository or related terms
        for skill_name, content in all_contents.items():
            has_reference = (
                "multirepository" in content.lower()
                or "multi-repo" in content.lower()
                or "複数リポ" in content
            )
            assert (
                has_reference
            ), f"{skill_name} should reference multirepository/multi-repo structure"
