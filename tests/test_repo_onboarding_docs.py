from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ONBOARDING = ROOT / "plugins" / "happy-coding" / "skills" / "repo-onboarding" / "SKILL.md"
TEAM_REPO_SETUP = ROOT / "docs" / "advanced" / "TEAM_REPO_SETUP.md"
GETTING_STARTED = ROOT / "docs" / "GETTING_STARTED.md"
REFERENCE_DOC = ROOT / "docs" / "REFERENCE.md"
ADR_DOC = ROOT / "docs" / "adr" / "bootstrap-minimal-onboarding-and-check-severity.md"
CONTEXT_DOC = ROOT / "CONTEXT.md"


def test_repo_onboarding_docs_explain_bootstrapminimal_flow() -> None:
    repo_onboarding = REPO_ONBOARDING.read_text(encoding="utf-8")
    team_repo_setup = TEAM_REPO_SETUP.read_text(encoding="utf-8")
    getting_started = GETTING_STARTED.read_text(encoding="utf-8")
    reference_doc = REFERENCE_DOC.read_text(encoding="utf-8")
    adr = ADR_DOC.read_text(encoding="utf-8")
    context = CONTEXT_DOC.read_text(encoding="utf-8")

    assert "BootstrapMinimal" in repo_onboarding
    assert "repoInstructions" in repo_onboarding
    assert "copilotHooks" in repo_onboarding
    assert "guardPolicyFiles" in repo_onboarding
    assert "gitHooksDirectory" in repo_onboarding
    assert "gitHookLineEndings" in repo_onboarding
    assert "coreHooksPath" in repo_onboarding
    assert "toolDependencies" in repo_onboarding
    assert "advisory" in repo_onboarding
    assert "PolicyProfile BootstrapMinimal" in team_repo_setup
    assert "PolicyProfile HappyDefault" in team_repo_setup
    assert "PolicyProfile BootstrapMinimal" in getting_started
    assert "PolicyProfile HappyDefault" in getting_started
    assert "PolicyProfile BootstrapMinimal" in reference_doc
    assert "PolicyProfile HappyDefault" in reference_doc
    assert "BootstrapMinimal" in adr
    assert "**BootstrapMinimal**:" in context
