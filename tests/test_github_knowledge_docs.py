from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
AGENTS_DOC = ROOT / "AGENTS.md"
README_DOC = ROOT / "README.md"
REPO_INSTRUCTIONS = ROOT / ".github" / "copilot-instructions.md"
CONTEXT_DOC = ROOT / "CONTEXT.md"
DOCS_INDEX = ROOT / "docs" / "README.md"
KNOWLEDGE_INDEX = ROOT / "docs" / "knowledge" / "README.md"
GRILL_INDEX = ROOT / "docs" / "grill_results" / "README.md"
DESIGN_INDEX = ROOT / "docs" / "design" / "README.md"
PLAN_INDEX = ROOT / "docs" / "plan" / "README.md"
ADR_INDEX = ROOT / "docs" / "adr" / "README.md"
KNOWLEDGE_ADR = ROOT / "docs" / "adr" / "github-first-knowledge-storage-and-agent-entrypoints.md"
DEVELOPMENT_DOC = ROOT / "docs" / "DEVELOPMENT.md"
AUTHORING_DOC = ROOT / "docs" / "AUTHORING.md"
HAPPY_ADD_ISSUE = ROOT / "plugins" / "happy-core" / "skills" / "happy-add-issue" / "SKILL.md"


def assert_contains_terms(text: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        assert term in text


def extract_markdown_links(text: str) -> dict[str, str]:
    return {label: target for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)}


def test_agents_entrypoint_is_present() -> None:
    agents = AGENTS_DOC.read_text(encoding="utf-8")
    agent_links = extract_markdown_links(agents)

    assert "# AGENTS.md" in agents
    assert "## この repo での役割" in agents
    assert "## Source of truth" in agents
    assert "## 基本コマンド" in agents
    assert "## Boundaries" in agents
    for required_target in (
        "README.md",
        ".github/copilot-instructions.md",
        "CONTEXT.md",
        "docs/README.md",
        "docs/knowledge/README.md",
        "docs/adr/README.md",
    ):
        assert required_target in agent_links.values()


def test_context_and_adr_define_new_terms_and_policy() -> None:
    context = CONTEXT_DOC.read_text(encoding="utf-8")
    adr = KNOWLEDGE_ADR.read_text(encoding="utf-8")
    adr_index = ADR_INDEX.read_text(encoding="utf-8")

    assert_contains_terms(
        context,
        (
            "**AGENTS.md**:",
            "**learnings**:",
        ),
    )
    assert_contains_terms(
        adr,
        (
            "GitHub-first knowledge storage",
            "AGENTS.md",
            "gist",
            "docs/knowledge/",
        ),
    )
    assert "github-first-knowledge-storage-and-agent-entrypoints.md" in adr_index


def test_docs_indexes_make_knowledge_path_discoverable() -> None:
    readme = README_DOC.read_text(encoding="utf-8")
    repo_instructions = REPO_INSTRUCTIONS.read_text(encoding="utf-8")
    docs_index = DOCS_INDEX.read_text(encoding="utf-8")
    knowledge_index = KNOWLEDGE_INDEX.read_text(encoding="utf-8")
    grill_index = GRILL_INDEX.read_text(encoding="utf-8")
    design_index = DESIGN_INDEX.read_text(encoding="utf-8")
    plan_index = PLAN_INDEX.read_text(encoding="utf-8")
    development = DEVELOPMENT_DOC.read_text(encoding="utf-8")
    authoring = AUTHORING_DOC.read_text(encoding="utf-8")

    readme_links = extract_markdown_links(readme)
    docs_links = extract_markdown_links(docs_index)
    knowledge_links = extract_markdown_links(knowledge_index)
    grill_links = extract_markdown_links(grill_index)
    design_links = extract_markdown_links(design_index)
    plan_links = extract_markdown_links(plan_index)

    assert "docs/README.md" in readme_links.values()
    assert "AGENTS.md" in readme_links.values()
    assert "tests/test_github_knowledge_docs.py" in readme
    assert "tests/test_evals_policy.py" in readme
    assert "AGENTS.md" in repo_instructions
    assert "docs/README.md" in repo_instructions
    assert "knowledge/README.md" in docs_links.values()
    assert "adr/README.md" in docs_links.values()
    assert "design/README.md" in docs_links.values()
    assert "plan/README.md" in docs_links.values()
    assert "local session state" in knowledge_index
    assert "gist" in knowledge_index
    for required_target in (
        "context/index.md",
        "playbooks/index.md",
        "troubleshooting/index.md",
        "lessons/index.md",
        "references/index.md",
    ):
        assert required_target in knowledge_links.values()
    assert "../../README.md" in knowledge_links.values()
    assert "../README.md" in knowledge_links.values()
    assert "../adr/README.md" in knowledge_links.values()
    for required_target in (
        "001_GRILL_WITH_DOCS_RESULT.md",
        "002_GRILL_WITH_DOCS_RESULT.md",
        "003_GRILL_WITH_DOCS_RESULT.md",
        "005_GRILL_WITH_DOCS_RESULT.md",
        "006_GRILL_WITH_DOCS_RESULT.md",
        "007_GRILL_WITH_DOCS_RESULT.md",
        "008_GRILL_WITH_DOCS_RESULT.md",
    ):
        assert required_target in grill_links.values()
    assert "../design/008_TECHNICAL_DESIGN.md" in grill_links.values()
    assert "../plan/008_PLAN_DONE.md" in grill_links.values()
    assert "008_TECHNICAL_DESIGN.md" in design_links.values()
    assert "008_PLAN_DONE.md" in plan_links.values()
    assert_contains_terms(
        development,
        (
            "AGENTS.md",
            "docs/README.md",
            "docs/knowledge/",
        ),
    )
    assert "tests/test_github_knowledge_docs.py" in development
    assert "tests/test_evals_policy.py" in development
    assert "CONTEXT.md" in development
    assert "docs/adr/" in development
    assert_contains_terms(
        authoring,
        (
            "AGENTS.md",
            "learnings",
            "docs/knowledge/",
        ),
    )


def test_happy_add_issue_stops_using_gist_as_detail_escape_hatch() -> None:
    skill = HAPPY_ADD_ISSUE.read_text(encoding="utf-8")

    assert "gist" in skill
    assert "Issue を分割する" in skill
    assert "follow-up Issue" in skill
    assert "docs / ADR" in skill
    assert "gh gist create" not in skill
    assert "secret gist" not in skill
    assert "長い失敗ログ、再現メモ、切り分け経緯がある" not in skill
