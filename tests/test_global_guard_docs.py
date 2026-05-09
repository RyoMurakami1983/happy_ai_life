from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
HOME_SYNC_PATH = ROOT_DIR / "docs" / "HOME_SYNC.md"
HOOKS_GOVERNANCE_PATH = ROOT_DIR / "docs" / "HOOKS_GOVERNANCE.md"
TRUST_BOUNDARY_PATH = ROOT_DIR / "docs" / "TRUST_BOUNDARY.md"
GETTING_STARTED_PATH = ROOT_DIR / "docs" / "GETTING_STARTED.md"
ENTERPRISE_SECURITY_REVIEW_PATH = ROOT_DIR / "docs" / "ENTERPRISE_SECURITY_REVIEW.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_home_sync_docs_formalize_managed_global_guard() -> None:
    content = read_text(HOME_SYNC_PATH)

    assert "managed な user-level safety hook entry（正式な enterprise/global guard）" in content
    assert "全 repository 共通の enterprise/global guard" in content
    assert 'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"' in content
    assert "user-owned な他の hook entry や `config.json` の他設定は保持します" in content


def test_hooks_governance_docs_define_managed_entry_boundary() -> None:
    content = read_text(HOOKS_GOVERNANCE_PATH)

    assert "managed enterprise/global guard" in content
    assert "正式な enterprise/global guard" in content
    assert 'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"' in content
    assert "user-owned な他の `config.json` 設定や hook entry は保持する" in content


def test_related_docs_use_global_guard_naming() -> None:
    trust_boundary = read_text(TRUST_BOUNDARY_PATH)
    getting_started = read_text(GETTING_STARTED_PATH)
    security_review = read_text(ENTERPRISE_SECURITY_REVIEW_PATH)

    assert "managed enterprise/global guard" in trust_boundary
    assert 'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"' in trust_boundary
    assert "managed な user-level safety hook entry（enterprise/global guard）" in getting_started
    assert "managed な enterprise/global guard entry" in security_review
