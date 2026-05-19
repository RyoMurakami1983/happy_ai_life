from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
HOME_TEMPLATE_INSTRUCTIONS_PATH = (
    ROOT_DIR / "home-template" / ".copilot" / "copilot-instructions.md"
)
DESIGN_WORKSHOP_SKILL_PATH = (
    ROOT_DIR / "plugins" / "happy-coding" / "skills" / "design-workshop" / "SKILL.md"
)
STANDARD_WORKFLOW_PATH = (
    ROOT_DIR
    / "plugins"
    / "happy-coding"
    / "skills"
    / "design-workshop"
    / "sub_skills"
    / "standard"
    / "SKILL.md"
)
TECH_SELECTION_HARNESS_PATH = (
    ROOT_DIR
    / "plugins"
    / "happy-coding"
    / "skills"
    / "design-workshop"
    / "_foundation"
    / "TECH_SELECTION_HARNESS.md"
)
SDD_SKILL_PATH = ROOT_DIR / "plugins" / "happy-coding" / "skills" / "sdd" / "SKILL.md"
BALANCED_COUPLING_PATH = (
    ROOT_DIR
    / "plugins"
    / "happy-coding"
    / "skills"
    / "design-workshop"
    / "sub_skills"
    / "balanced-coupling-design"
    / "SKILL.md"
)
FROM_SCRATCH_PATH = (
    ROOT_DIR / "plugins" / "happy-coding" / "skills" / "sdd" / "sub_skills" / "from-scratch" / "SKILL.md"
)
FROM_SPEC_PATH = (
    ROOT_DIR / "plugins" / "happy-coding" / "skills" / "sdd" / "sub_skills" / "from-spec" / "SKILL.md"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_home_instructions_keep_tech_selection_principles_short() -> None:
    content = read_text(HOME_TEMPLATE_INSTRUCTIONS_PATH)

    assert "## 言語・フレームワーク選定" in content
    assert "要件適合度・保守性・実行環境・チーム習熟度・切り替えコスト" in content
    assert "Decision Log" in content
    assert "| 観点 | 内容 |" not in content


def test_design_workshop_mentions_mvp_tech_selection() -> None:
    content = read_text(DESIGN_WORKSHOP_SKILL_PATH)

    assert "MVP で採用する言語・フレームワーク" in content
    assert "MVP 技術選定" in content
    assert "TECH_SELECTION_HARNESS.md" in content


def test_standard_workflow_has_tech_selection_checkpoint() -> None:
    content = read_text(STANDARD_WORKFLOW_PATH)

    assert "### ステップ 3 — MVP 技術選定チェックポイント" in content
    assert "モックの仮選定と MVP の本選定" in content
    assert "Decision Log" in content
    assert "## MVP 技術選定" in content


def test_tech_selection_harness_exists_with_core_axes() -> None:
    assert TECH_SELECTION_HARNESS_PATH.exists(), f"TECH_SELECTION_HARNESS.md not found at {TECH_SELECTION_HARNESS_PATH}"
    content = read_text(TECH_SELECTION_HARNESS_PATH)
    for phrase in (
        "要件適合度",
        "保守性",
        "実行環境",
        "チーム習熟度",
        "切り替えコスト",
        "小さな技術検証",
        "Decision Log に残す条件",
    ):
        assert phrase in content


def test_sdd_flow_mentions_optional_mock_before_design() -> None:
    content = read_text(SDD_SKILL_PATH)

    assert "spec → 必要ならモック → design → plan" in content
    assert "必要ならモック" in content
    assert "MVP の本選定は design-workshop が担う" in content
    assert "balanced-coupling-design はステップ 3 のモジュール設計で行う" in content


def test_balanced_coupling_route_also_documents_tech_selection() -> None:
    content = read_text(BALANCED_COUPLING_PATH)

    assert "モジュール設計書作成と MVP 技術方式の選定" in content
    assert "TECH_SELECTION_HARNESS.md" in content
    assert "MVP の比較結果" in content
    assert "MVP 技術方式の選定結果と見直し条件" in content


def test_sdd_sub_skills_explain_mock_and_mvp_split() -> None:
    from_scratch = read_text(FROM_SCRATCH_PATH)
    from_spec = read_text(FROM_SPEC_PATH)

    assert "仮選定した技術" in from_scratch
    assert "MVP 技術選定" in from_scratch
    assert "モジュール別技術方式の選定" in from_scratch
    assert "モックの技術は仮選定として扱い" in from_spec
    assert "本採用する言語・フレームワーク" in from_spec
