from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASK_HAPPY = ROOT / "plugins" / "happy-core" / "skills" / "ask-happy" / "SKILL.md"
FURIKAERI = ROOT / "plugins" / "happy-core" / "skills" / "furikaeri" / "SKILL.md"


def test_no_dead_session_handoff_routes_remain() -> None:
    ask_happy = ASK_HAPPY.read_text(encoding="utf-8")
    furikaeri = FURIKAERI.read_text(encoding="utf-8")

    assert "session-handoff" not in ask_happy
    assert "session-handoff" not in furikaeri
    assert "/resume" in ask_happy
    assert "/resume" in furikaeri
    assert "/share file session" not in ask_happy
    assert "/share file session" not in furikaeri
    assert "/share file [PATH]" in ask_happy
    assert "/share file [PATH]" in furikaeri
