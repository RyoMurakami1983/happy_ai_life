from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOTNET_ROUTER = ROOT / "plugins" / "happy-coding" / "skills" / "dotnet" / "SKILL.md"
SLOPWATCH = (
    ROOT / "plugins" / "happy-coding" / "skills" / "dotnet" / "sub_skills" / "slopwatch" / "SKILL.md"
)
SKILL_MAP = ROOT / "docs" / "SKILL_MAP.md"


def assert_contains_terms(text: str, terms: tuple[str, ...]) -> None:
    for term in terms:
        assert term in text


def test_dotnet_router_is_thin_family_router() -> None:
    skill = DOTNET_ROUTER.read_text(encoding="utf-8")

    assert_contains_terms(
        skill,
        (
            "disable-model-invocation: true",
            "family router",
            "sub_skills/framework-bridge/",
            "sub_skills/setup/",
            "sub_skills/modern-cs/",
            "sub_skills/type-perf/",
            "sub_skills/cs-concurrency/",
            "sub_skills/wpf-mvvm/",
            "sub_skills/wpf-secure-config/",
            "sub_skills/slopwatch/",
            "sub_skills/nuget-local/",
            "secure storage を先に固定",
        ),
    )


def test_skill_map_treats_dotnet_as_single_public_entry() -> None:
    skill_map = SKILL_MAP.read_text(encoding="utf-8")

    assert "| `dotnet` |" in skill_map
    for removed in (
        "| `dotnet-framework-netstandard-bridge` |",
        "| `dotnet-setup-dev-environment` |",
        "| `dotnet-modern-cs` |",
        "| `dotnet-type-perf` |",
        "| `dotnet-cs-concurrency` |",
        "| `dotnet-wpf-mvvm-patterns` |",
        "| `dotnet-wpf-secure-config` |",
        "| `dotnet-slopwatch` |",
        "| `nuget-local` |",
    ):
        assert removed not in skill_map


def test_slopwatch_links_back_to_repo_docs() -> None:
    slopwatch = SLOPWATCH.read_text(encoding="utf-8")

    assert "../../../../../../docs/PHILOSOPHY.md" in slopwatch
