from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COPILOT_AUTHORING_SKILL = ROOT / "plugins" / "happy-core" / "skills" / "copilot-authoring" / "SKILL.md"
AUTHORING_DOC = ROOT / "docs" / "AUTHORING.md"
CONVENTIONS_DOC = (
    ROOT
    / "plugins"
    / "happy-core"
    / "skills"
    / "copilot-authoring"
    / "_skill"
    / "_foundation"
    / "CONVENTIONS.md"
)
ROUTER_TEMPLATE = (
    ROOT
    / "plugins"
    / "happy-core"
    / "skills"
    / "copilot-authoring"
    / "_skill"
    / "_foundation"
    / "ROUTER_TEMPLATE.md"
)
ADR_DOC = ROOT / "docs" / "adr" / "skill-single-responsibility-and-orchestration.md"


def assert_contains_terms(text: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        assert term in text


def test_copilot_authoring_is_thin_orchestrator() -> None:
    skill = COPILOT_AUTHORING_SKILL.read_text(encoding="utf-8")

    assert_contains_terms(
        skill,
        (
            "disable-model-invocation: true",
            "## 役割の境界",
            "## 実行ルール",
            "sub_skills/new-skill/",
            "sub_skills/instructions/",
            "sub_skills/improve/",
            "sub_skills/validate/",
            "happy-core@skill-eval",
            "happy-core@empirical-prompt-tuning",
            "interview-with-docs",
            "1 つの primary purpose",
            "新しい custom agent は標準 authoring route では作りません",
        ),
    )
    assert "sub_skills/new-agent/" not in skill


def test_authoring_policy_documents_single_responsibility() -> None:
    authoring = AUTHORING_DOC.read_text(encoding="utf-8")
    conventions = CONVENTIONS_DOC.read_text(encoding="utf-8")
    router_template = ROUTER_TEMPLATE.read_text(encoding="utf-8")
    adr = ADR_DOC.read_text(encoding="utf-8")

    assert_contains_terms(
        authoring,
        (
            "1 skill = 1 primary purpose",
            "interview-with-docs",
            "disable-model-invocation: true",
            "copilot-authoring",
        ),
    )
    assert_contains_terms(
        conventions,
        (
            "1 skill = 1 primary purpose",
            "disable-model-invocation: true",
            "interview-with-docs",
        ),
    )
    assert_contains_terms(
        router_template,
        (
            "disable-model-invocation: true",
            "1 skill = 1 primary purpose",
            "役割の境界",
            "実行ルール",
        ),
    )
    assert_contains_terms(
        adr,
        (
            "1 skill = 1 primary purpose",
            "interview-with-docs",
            "copilot-authoring",
        ),
    )
