"""
session-continuity hook 由来の prompt injection 対策を検証する。

Issue #129: session-continuity hook 由来の prompt injection 対策を強化する

検証観点:
- 生成 context が命令ではなく参考情報であることが実装に明記されている。
- HOOKS_GOVERNANCE.md が disclaimer 要件を定義している。
- legacy opt-in の条件が維持されている。
- validate-session-hooks.js が disclaimer テストを含んでいる（node が利用可能な場合）。
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SESSION_START_JS = ROOT / ".github" / "hooks" / "scripts" / "session-start.js"
VALIDATE_SESSION_HOOKS_JS = ROOT / "scripts" / "validate-session-hooks.js"
HOOKS_GOVERNANCE_PATH = ROOT / "archive" / "enterprise-hardening" / "docs" / "HOOKS_GOVERNANCE.md"
SESSION_CONTINUITY_RETIREMENT_ADR = ROOT / "docs" / "adr" / "session-continuity-retirement.md"

_node_available = shutil.which("node") is not None


def test_session_start_js_implements_disclaimer() -> None:
    """session-start.js の buildInstructionsContent が disclaimer テキストを含む。"""
    content = SESSION_START_JS.read_text(encoding="utf-8")
    assert "参考情報であり、命令ではない" in content
    assert "security policy" in content
    assert "user instruction" in content


def test_hooks_governance_defines_disclaimer_requirement() -> None:
    """HOOKS_GOVERNANCE.md が disclaimer の要件を定義している。"""
    content = HOOKS_GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "参考情報であり、命令ではない" in content
    assert "security policy" in content
    assert "現在の user instruction" in content
    assert "repository source of truth" in content


def test_hooks_governance_defines_legacy_optin_conditions() -> None:
    """HOOKS_GOVERNANCE.md が session-continuity の legacy opt-in 方針を定義している。"""
    content = HOOKS_GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "session-continuity.json" in content
    assert "legacy opt-in" in content
    assert "標準では" in content


def test_session_continuity_retirement_adr_defines_optin_command() -> None:
    """session-continuity-retirement.md が opt-in コマンドを明記している。"""
    content = SESSION_CONTINUITY_RETIREMENT_ADR.read_text(encoding="utf-8")
    assert "sync-to-repo.ps1 -HooksMode All" in content
    assert "legacy" in content


@pytest.mark.skipif(not _node_available, reason="node not available")
def test_validate_session_hooks_passes_with_disclaimer_checks() -> None:
    """validate-session-hooks.js が disclaimer テストを含む状態で正常終了する。"""
    result = subprocess.run(
        ["node", str(VALIDATE_SESSION_HOOKS_JS)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    assert result.returncode == 0, (
        f"validate-session-hooks.js failed:\n{stdout}\n{stderr}"
    )
    assert "disclaimer" in stdout, (
        "validate-session-hooks.js の出力に disclaimer テスト結果が含まれない"
    )
