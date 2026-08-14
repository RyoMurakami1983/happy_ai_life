from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_EVAL = ROOT / "plugins" / "happy-core" / "skills" / "skill-eval" / "SKILL.md"
PRIVATE_EVAL_REF = (
    ROOT / "plugins" / "happy-core" / "skills" / "skill-eval" / "references" / "private-eval.md"
)
EMPIRICAL_POINTER = (
    ROOT / "plugins" / "happy-core" / "skills" / "skill-eval" / "sub_skills" / "empirical" / "SKILL.md"
)
PRIVATE_EVAL_DOC = ROOT / "docs" / "PRIVATE_EVAL.md"
CONTEXT_DOC = ROOT / "CONTEXT.md"
LOOP_EVAL_REF = (
    ROOT / "plugins" / "happy-coding" / "skills" / "loop-engineering" / "references" / "private-eval.md"
)


def assert_contains_terms(text: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        assert term in text


def test_skill_eval_routes_private_eval_without_top_level_skill() -> None:
    skill = SKILL_EVAL.read_text(encoding="utf-8")

    assert_contains_terms(
        skill,
        (
            "references/private-eval.md",
            "評価ケースの設計・保管・昇格判断",
            "sub_skills/benchmark/",
            "empirical-prompt-tuning",
            "独立 skill",
        ),
    )
    assert "sub_skills/empirical/" not in skill
    assert not EMPIRICAL_POINTER.exists()


def test_private_eval_definition_is_consistent() -> None:
    private_eval = PRIVATE_EVAL_REF.read_text(encoding="utf-8")
    doc = PRIVATE_EVAL_DOC.read_text(encoding="utf-8")
    context = CONTEXT_DOC.read_text(encoding="utf-8")

    expected_terms = (
        "secret を含まない評価ケース",
        "設計・保管・昇格判断",
        "評価の実行そのもの",
        "evals/<skill-id>/",
    )
    assert_contains_terms(private_eval, expected_terms)
    assert_contains_terms(doc, expected_terms)
    assert_contains_terms(context, ("secret を含まない評価ケース", "設計・保管・昇格判断"))


def test_loop_engineering_consumes_private_eval_but_does_not_own_it() -> None:
    loop_ref = LOOP_EVAL_REF.read_text(encoding="utf-8")

    assert_contains_terms(
        loop_ref,
        (
            "Loop Engineering",
            "consumer",
            "評価ケース資産そのものの owner ではありません",
            "`skill-eval` 側の reference を正本",
        ),
    )
