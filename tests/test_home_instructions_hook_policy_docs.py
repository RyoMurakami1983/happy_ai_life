from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
HOME_TEMPLATE_INSTRUCTIONS_PATH = (
    ROOT_DIR / "home-template" / ".copilot" / "copilot-instructions.md"
)
HOME_SYNC_DOC_PATH = ROOT_DIR / "docs" / "HOME_SYNC.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_home_instructions_prioritize_user_level_guard() -> None:
    content = read_text(HOME_TEMPLATE_INSTRUCTIONS_PATH)

    assert "repository 事実に限ってそちらを優先する" in content
    assert "user-level guard を正とする" in content
    assert "信頼の根にしない" in content
    assert "repository-scoped の `.github/hooks/` を正とし" not in content


def test_home_sync_doc_matches_user_level_guard_policy() -> None:
    content = read_text(HOME_SYNC_DOC_PATH)

    assert "managed な user-level safety hook entry" in content
    assert "安全弁の優先順位は user-level guard を最上位" in content
