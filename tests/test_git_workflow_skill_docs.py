from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GIT_COMMIT_SKILL = ROOT / "plugins" / "happy-core" / "skills" / "git-commit" / "SKILL.md"
GIT_COMMIT_EXAMPLES = (
    ROOT / "plugins" / "happy-core" / "skills" / "git-commit" / "references" / "examples.md"
)
GH_PR_CREATE_SKILL = ROOT / "plugins" / "happy-core" / "skills" / "gh-pr-create" / "SKILL.md"
DEVELOPMENT_DOC = ROOT / "docs" / "DEVELOPMENT.md"
SKILL_MAP_DOC = ROOT / "docs" / "SKILL_MAP.md"


def assert_contains_terms(text: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        assert term in text


def find_line(text: str, anchor: str) -> str:
    return next(line for line in text.splitlines() if anchor in line)


def find_line_starting(text: str, prefix: str) -> str:
    return next(line for line in text.splitlines() if line.startswith(prefix))


def test_git_commit_skill_requires_default_branch_and_commit_confirmation() -> None:
    skill = GIT_COMMIT_SKILL.read_text(encoding="utf-8")

    assert_contains_terms(
        skill,
        (
            "毎回",
            "branch 名候補",
            "commit message 候補",
            "承認後",
        ),
    )


def test_git_commit_examples_show_confirmation_format() -> None:
    examples = GIT_COMMIT_EXAMPLES.read_text(encoding="utf-8")

    assert "branch 名候補" in examples
    assert "commit message 候補" in examples
    assert "承認を取ってから commit" in examples


def test_gh_pr_create_skill_inherits_same_confirmation_rule() -> None:
    skill = GH_PR_CREATE_SKILL.read_text(encoding="utf-8")

    assert_contains_terms(skill, ("毎回 branch 名候補", "承認後"))
    workflow_line = find_line(skill, "2. 必要なら commit / push する。")
    assert_contains_terms(
        workflow_line,
        ("未コミット", "commit message 候補", "`git-commit`", "確認ルール"),
    )
    handoff_line = find_line(skill, "変更が未コミットなら、まず `git-commit`")
    assert_contains_terms(
        handoff_line,
        ("branch 名候補", "commit message 候補", "承認後", "commit"),
    )


def test_development_doc_explains_default_git_write_confirmation() -> None:
    development = DEVELOPMENT_DOC.read_text(encoding="utf-8")

    git_commit_line = find_line(development, "`git-commit` を使う場合は")
    assert_contains_terms(
        git_commit_line,
        ("`git-commit`", "branch 名候補", "commit message 候補", "毎回", "承認後"),
    )
    gh_pr_create_line = find_line(development, "`gh-pr-create` を使う場合も")
    assert_contains_terms(
        gh_pr_create_line,
        (
            "`gh-pr-create`",
            "PR 作成前",
            "branch 名候補",
            "未コミット変更",
            "`git-commit`",
            "commit message 候補",
        ),
    )


def test_skill_map_describes_conditional_pr_commit_confirmation() -> None:
    skill_map = SKILL_MAP_DOC.read_text(encoding="utf-8")

    gh_pr_create_row = find_line_starting(skill_map, "| `gh-pr-create` |")
    assert_contains_terms(
        gh_pr_create_row,
        (
            "`gh-pr-create`",
            "branch 名候補",
            "未コミット",
            "commit message 候補確認",
            "`deep-review-preflight`",
        ),
    )
