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


def test_git_commit_skill_requires_default_branch_and_commit_confirmation() -> None:
    skill = GIT_COMMIT_SKILL.read_text(encoding="utf-8")

    required_terms = (
        "毎回",
        "branch 名候補",
        "commit message 候補",
        "承認後",
    )
    for term in required_terms:
        assert term in skill


def test_git_commit_examples_show_confirmation_format() -> None:
    examples = GIT_COMMIT_EXAMPLES.read_text(encoding="utf-8")

    assert "branch 名候補" in examples
    assert "commit message 候補" in examples
    assert "承認を取ってから commit" in examples


def test_gh_pr_create_skill_inherits_same_confirmation_rule() -> None:
    skill = GH_PR_CREATE_SKILL.read_text(encoding="utf-8")

    assert "毎回 branch 名候補" in skill
    assert "未コミットなら **commit message 候補** を含む `git-commit` の確認ルールを使う" in skill
    assert (
        "branch 名候補と commit message 候補を提示し、承認後に commit する"
        in skill
    )


def test_development_doc_explains_default_git_write_confirmation() -> None:
    development = DEVELOPMENT_DOC.read_text(encoding="utf-8")

    assert (
        "`git-commit` を使う場合は、**branch 名候補** と **commit message 候補** を毎回提示し、承認後に commit するのを既定にします。"
        in development
    )
    assert (
        "`gh-pr-create` を使う場合も、PR 作成前に branch 名候補を確認します。未コミット変更がある場合は `git-commit` の既定を引き継ぎ、branch 名候補と commit message 候補を提示してから進めます。"
        in development
    )


def test_skill_map_describes_conditional_pr_commit_confirmation() -> None:
    skill_map = SKILL_MAP_DOC.read_text(encoding="utf-8")

    assert (
        "| `gh-pr-create` | branch 名候補を確認し、未コミットなら commit message 候補確認も引き継いで PR を作る | `deep-review-preflight` |"
        in skill_map
    )
