from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_DOC = ROOT / "CONTEXT.md"
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
ADR_DOC = ROOT / "docs" / "adr" / "skill-single-responsibility-and-orchestration.md"
SKILL_MAP_DOC = ROOT / "docs" / "SKILL_MAP.md"
ASK_HAPPY_DOC = ROOT / "plugins" / "happy-core" / "skills" / "ask-happy" / "SKILL.md"
DOTNET_ROUTER_DOC = ROOT / "plugins" / "happy-coding" / "skills" / "dotnet" / "SKILL.md"


def assert_contains_terms(text: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        assert term in text


def test_naming_policy_is_documented() -> None:
    authoring = AUTHORING_DOC.read_text(encoding="utf-8")
    conventions = CONVENTIONS_DOC.read_text(encoding="utf-8")
    adr = ADR_DOC.read_text(encoding="utf-8")

    shared_terms = (
        "短さより誤解しにくさ",
        "plugin slug",
        "top-level / evaluation / safety / entrypoint skill",
        "文脈で一意な child / leaf skill",
        "`ts`, `py`, `cs`, `perf`",
        "`eval`, `author`, `plan`",
    )
    assert_contains_terms(authoring, shared_terms)
    assert_contains_terms(conventions, shared_terms)
    assert_contains_terms(adr, ("plugin slug は維持", "文脈で一意な child / leaf skill", "初見ユーザーが役割を推測できるか"))


def test_disable_model_invocation_policy_is_documented() -> None:
    context = CONTEXT_DOC.read_text(encoding="utf-8")
    authoring = AUTHORING_DOC.read_text(encoding="utf-8")
    conventions = CONVENTIONS_DOC.read_text(encoding="utf-8")
    adr = ADR_DOC.read_text(encoding="utf-8")

    expected = (
        "orchestration",
        "route / handoff",
        "可視性制御",
        "manual-only",
    )
    assert_contains_terms(context, ("disable-model-invocation", "route / handoff", "manual-only"))
    assert_contains_terms(authoring, expected)
    assert_contains_terms(conventions, expected)
    assert_contains_terms(adr, ("disable-model-invocation: true", "可視性制御", "manual-only"))


def test_first_batch_renames_are_reflected_in_public_docs() -> None:
    skill_map = SKILL_MAP_DOC.read_text(encoding="utf-8")
    ask_happy = ASK_HAPPY_DOC.read_text(encoding="utf-8")
    dotnet = DOTNET_ROUTER_DOC.read_text(encoding="utf-8")

    assert_contains_terms(
        skill_map,
        (
            "`py-setup`",
            "`ts-setup`",
            "`ts-tauri`",
            "`dotnet-cs-concurrency`",
            "`dotnet-modern-cs`",
            "`dotnet-type-perf`",
        ),
    )
    assert "python-setup-dev-environment" not in skill_map
    assert "typescript-setup-dev-environment" not in skill_map
    assert "typescript-tauri-setup" not in ask_happy
    assert_contains_terms(
        dotnet,
        ("`dotnet-modern-cs`", "`dotnet-type-perf`", "`dotnet-cs-concurrency`"),
    )
