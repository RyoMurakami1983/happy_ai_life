from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
README_PATH = ROOT_DIR / "README.md"
GETTING_STARTED_PATH = ROOT_DIR / "docs" / "GETTING_STARTED.md"
DEVELOPMENT_PATH = ROOT_DIR / "docs" / "DEVELOPMENT.md"
TROUBLESHOOTING_PATH = ROOT_DIR / "docs" / "TROUBLESHOOTING.md"
SECURITY_PATH = ROOT_DIR / "SECURITY.md"
ARCHIVE_DOCS = ROOT_DIR / "archive" / "enterprise-hardening" / "docs"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, phrases: tuple[str, ...]) -> None:
    for phrase in phrases:
        assert phrase in text


def test_readme_keeps_only_daily_use_docs_in_active_entry() -> None:
    content = read_text(README_PATH)

    assert_contains_all(
        content,
        (
            "[はじめに](docs/GETTING_STARTED.md)",
            "[開発ガイド](docs/DEVELOPMENT.md)",
            "[品質ゲート](docs/QUALITY_GATES.md)",
            "[作成ガイド](docs/AUTHORING.md)",
            "[FAQ](docs/FAQ.md)",
            "[トラブルシューティング](docs/TROUBLESHOOTING.md)",
        ),
    )
    for archived_doc in (
        "ENTERPRISE_SECURITY",
        "ENTERPRISE_SECURITY_REVIEW",
        "ISSUE_ROADMAP_ENTERPRISE_SECURITY",
        "AI_REPRO_SECURITY_ROADMAP",
        "COPILOT_CLI_HANDOFF_AI_REPRO_SECURITY",
        "PHILOSOPHY.md",
    ):
        assert archived_doc not in content


def test_daily_docs_avoid_enterprise_and_reference_sprawl() -> None:
    combined = "\n".join(
        read_text(path)
        for path in (
            GETTING_STARTED_PATH,
            DEVELOPMENT_PATH,
            TROUBLESHOOTING_PATH,
        )
    )

    for phrase in (
        "Enterprise Security",
        "ENTERPRISE_SECURITY",
        "Trust Boundary",
        "HOOKS_GOVERNANCE",
        "REPO_BOOTSTRAP.md",
    ):
        assert phrase not in combined


def test_enterprise_docs_are_archived() -> None:
    expected_archived_docs = (
        "ENTERPRISE_SECURITY.md",
        "ENTERPRISE_SECURITY_REVIEW.md",
        "ISSUE_ROADMAP_ENTERPRISE_SECURITY.md",
        "AI_REPRO_SECURITY_ROADMAP.md",
        "COPILOT_CLI_HANDOFF_AI_REPRO_SECURITY.md",
        "HOOKS_GOVERNANCE.md",
        "TRUST_BOUNDARY.md",
        "REPO_BOOTSTRAP.md",
        "HOME_SYNC.full.md",
        "copilot-prompts/resolve-enterprise-security-issue.md",
        "copilot-prompts/resolve-ai-repro-security-issue.md",
        "issue-templates/enterprise-security-atomic-issue.md",
        "issue-templates/ai-repro-security-atomic-issue.md",
    )

    for relative_path in expected_archived_docs:
        assert (ARCHIVE_DOCS / relative_path).is_file()


def test_security_doc_defines_secret_incident_response() -> None:
    content = read_text(SECURITY_PATH)

    assert_contains_all(
        content,
        (
            "非公開チャネルで連絡",
            "まだ push されていないから安全",
            "rotation",
            "revoke",
            "gitleaks",
            "GitHub Secrets",
            "やってはいけないこと",
            "`.gitleaks.toml` の allowlist で incident を隠す",
        ),
    )
