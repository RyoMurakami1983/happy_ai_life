from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
HOME_SYNC_PATH = ROOT_DIR / "docs" / "HOME_SYNC.md"
HOOKS_GOVERNANCE_PATH = ROOT_DIR / "docs" / "HOOKS_GOVERNANCE.md"
TRUST_BOUNDARY_PATH = ROOT_DIR / "docs" / "TRUST_BOUNDARY.md"
GETTING_STARTED_PATH = ROOT_DIR / "docs" / "GETTING_STARTED.md"
ENTERPRISE_SECURITY_REVIEW_PATH = ROOT_DIR / "docs" / "ENTERPRISE_SECURITY_REVIEW.md"
ROADMAP_PATH = ROOT_DIR / "docs" / "ISSUE_ROADMAP_ENTERPRISE_SECURITY.md"
ADR_PATH = ROOT_DIR / "docs" / "adr" / "2026-05-08-enterprise-global-guard-policy.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, phrases: tuple[str, ...]) -> None:
    for phrase in phrases:
        assert phrase in text


def test_home_sync_docs_formalize_managed_global_guard() -> None:
    content = read_text(HOME_SYNC_PATH)

    assert_contains_all(
        content,
        (
            "managed な user-level safety hook entry",
            "enterprise/global guard",
            "enterprise managed policy / device policy を上書きするものではなく",
            'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"',
            "user-owned な他の hook entry",
            "`config.json` の他設定は保持します",
            "既存の managed entry に `-ExecutionPolicy Bypass` が入っている場合",
            "HAPPY_ENV_ALLOW_POLICY_BYPASS",
        ),
    )


def test_hooks_governance_docs_define_managed_entry_boundary() -> None:
    content = read_text(HOOKS_GOVERNANCE_PATH)

    assert_contains_all(
        content,
        (
            "managed enterprise/global guard",
            "正式な enterprise/global guard",
            'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"',
            "user-owned な他の `config.json` 設定や hook entry は保持する",
            "create / edit による protected path 変更",
            "protected path に一致した場合は `ask` を返す",
            "既存の managed home hook entry に `-ExecutionPolicy Bypass` が残っている場合",
            "repo-scoped `safety-guard.json` も既定では `-ExecutionPolicy Bypass` を付けない",
        ),
    )


def test_related_docs_use_global_guard_naming() -> None:
    trust_boundary = read_text(TRUST_BOUNDARY_PATH)
    getting_started = read_text(GETTING_STARTED_PATH)
    security_review = read_text(ENTERPRISE_SECURITY_REVIEW_PATH)
    roadmap = read_text(ROADMAP_PATH)
    adr = read_text(ADR_PATH)

    assert_contains_all(
        trust_boundary,
        (
            "managed enterprise/global guard",
            'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"',
            "repo-relative path:",
            "home-managed path:",
            "create` / `edit` 判定では",
        ),
    )
    assert_contains_all(
        getting_started,
        (
            "managed な user-level safety hook entry",
            "enterprise/global guard",
        ),
    )
    assert "managed な enterprise/global guard entry" in security_review
    assert_contains_all(
        roadmap,
        (
            "managed な enterprise/global guard entry",
            "正式名称",
        ),
    )
    assert_contains_all(
        adr,
        (
            "managed な enterprise/global guard entry",
            "managed entry を正式な global guard にする",
        ),
    )
