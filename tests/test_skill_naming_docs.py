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
