from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SECURITY_PATH = ROOT_DIR / "SECURITY.md"
HOME_SYNC_PATH = ROOT_DIR / "docs" / "HOME_SYNC.md"
HOOKS_GOVERNANCE_PATH = ROOT_DIR / "docs" / "HOOKS_GOVERNANCE.md"
TRUST_BOUNDARY_PATH = ROOT_DIR / "docs" / "TRUST_BOUNDARY.md"
GETTING_STARTED_PATH = ROOT_DIR / "docs" / "GETTING_STARTED.md"
ENTERPRISE_SECURITY_PATH = ROOT_DIR / "docs" / "ENTERPRISE_SECURITY.md"
ENTERPRISE_SECURITY_REVIEW_PATH = ROOT_DIR / "docs" / "ENTERPRISE_SECURITY_REVIEW.md"
ROADMAP_PATH = ROOT_DIR / "docs" / "ISSUE_ROADMAP_ENTERPRISE_SECURITY.md"
ADR_PATH = ROOT_DIR / "docs" / "adr" / "2026-05-08-enterprise-global-guard-policy.md"
README_PATH = ROOT_DIR / "README.md"
REFERENCE_PATH = ROOT_DIR / "docs" / "REFERENCE.md"
REPO_BOOTSTRAP_PATH = ROOT_DIR / "docs" / "REPO_BOOTSTRAP.md"


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
            'env.HAPPY_AI_LIFE_HOOK_EVENT',
            "user-owned な他の hook entry",
            "`config.json` の他設定は保持します",
            "既存の managed entry に `-ExecutionPolicy Bypass` が入っている場合",
            "HAPPY_ENV_ALLOW_POLICY_BYPASS",
            "`preToolUse` と `permissionRequest`",
            "`$HOME/.copilot/managed-manifest.json`",
            "managed file / managed directory / managed entry / user-owned surface",
        ),
    )


def test_repo_bootstrap_docs_define_policy_profile_enterprise() -> None:
    content = read_text(REPO_BOOTSTRAP_PATH)

    assert_contains_all(
        content,
        (
            "-PolicyProfile Enterprise",
            "PolicyProfile の違い",
            "`Default`",
            "`Enterprise`",
            "enterprise.instructions.md",
            "enterprise 向けの追加 guidance を明示 opt-in で入れる",
            "organization policy や GitHub Rulesets を自動設定するものではありません",
            "以前 `Enterprise` で配った `.github/instructions/enterprise.instructions.md` も取り除かれます",
        ),
    )


def test_hooks_governance_docs_define_managed_entry_boundary() -> None:
    content = read_text(HOOKS_GOVERNANCE_PATH)

    assert_contains_all(
        content,
        (
            "managed enterprise/global guard",
            "正式な enterprise/global guard",
            "cross-repo の最低 security baseline",
            'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"',
            "`env.HAPPY_AI_LIFE_HOOK_EVENT`",
            "user-owned な他の `config.json` 設定や hook entry は保持する",
            "`permissionRequest` による deny 系の早期ブロック",
            "`preToolUse` による protected path の `ask`",
            "`safety-guard.json`",
            "`session-continuity.json` は legacy opt-in",
            "責務境界",
            "local developer machine での `git commit` / `git push` 安全弁",
            "create / edit による protected path 変更",
            "`path` / `filePath` / `file_path` / `targetPath` / `target_path`",
            "protected path に一致した場合は `ask` を返す",
            "`permissionRequest` では `ask` を返せない",
            "fallback behavior",
            "agent へ deny message を返し",
            "現在の host で実際に使う variant",
            "`gh` は標準運用の baseline ではなく",
            "docs/ENTERPRISE_SECURITY_REVIEW.md の変更",
            ".github/mcp.json / .mcp.json / ~/.copilot/mcp-config.json の MCP 設定変更",
            "server entry の新規追加、削除、有効化 / 無効化",
            "command / args / env / working directory の変更",
            "remote endpoint / host / URL / transport の変更",
            "credential、auth method、渡す token / header / secret の変更",
            "公開する tool / capability 範囲の変更",
            "user-owned live config を壊さないこと",
            "`~/.copilot/mcp-config.json` は user-owned live config",
            "repo-local skill（`.github/skills/**`、`.agents/skills/**`、`.claude/skills/**`）",
            "`allowed-tools: \"*\"` や `*` を含む同等の全許可を既定で禁止する",
            "least privilege で代替できない理由",
            "tests/test_repo_local_skill_policy.py",
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
            "enterprise / user-level security policy",
            "managed enterprise/global guard",
            'env.HAPPY_AI_LIFE_HOOK_ID = "happy-ai-life-safety-guard"',
            "同レイヤー内では policy を上位に扱う",
            "installed plugin / approved skill",
            "repo-local MCP",
            "repo-relative path:",
            "home-managed path:",
            "create` / `edit` 判定では",
            "`permissionRequest` による deny 系の早期ブロック",
            "MCP server は外部 tool surface と外部接続先を増やす",
            "`~/.copilot/mcp-config.json` に設定される",
            "user-owned file であり、home sync やこの repository の配布物で上書きしない",
            "`.github/mcp.json`、`.mcp.json`、`~/.copilot/mcp-config.json` の server 定義追加・変更",
            "MCP server 追加・変更時の review 観点",
            "command / args / env / endpoint / auth の変更も同等に扱う",
            "repo-local skill（`.github/skills/**`、`.agents/skills/**`、`.claude/skills/**`）",
            "`allowed-tools: \"*\"` や `*` を含む同等の全許可は、企業利用では既定で禁止する",
            "least privilege な個別列挙で代替できない",
            "owner と reviewer",
            "rollback 方法、見直し時期",
            "docs/ENTERPRISE_SECURITY_REVIEW.md",
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


def test_enterprise_security_doc_defines_server_side_requirements() -> None:
    content = read_text(ENTERPRISE_SECURITY_PATH)

    assert_contains_all(
        content,
        (
            "Rulesets を優先",
            "Direct push を禁止",
            "Pull request 必須",
            "Required status checks",
            "`gitleaks`",
            "CODEOWNERS review",
            "force push 禁止",
            "branch deletion 禁止",
            "GitHub UI での目視確認を source of truth",
            "導入順序",
            "repo bootstrap を入れる",
            "sync-to-repo.ps1 -PolicyProfile Enterprise",
            "`repo-secure-check.ps1` は不足を埋めるためのスクリプトではなく",
            "& $HOME\\.copilot\\scripts\\repo-secure-check.ps1 -TargetRepoPath .",
            "& $HOME\\.copilot\\scripts\\repo-secure-check.ps1 -TargetRepoPath . -Strict",
            "human review が必要な領域",
            "security policy を弱める変更",
            "Rulesets / Branch Protection / Required checks の変更",
            "Repo Bootstrap（repo 初期導入）",
        ),
    )


def test_readme_and_reference_link_enterprise_security_doc() -> None:
    readme = read_text(README_PATH)
    reference = read_text(REFERENCE_PATH)

    assert "[Enterprise Security（企業向け保護設定）](docs/ENTERPRISE_SECURITY.md)" in readme
    assert "[Enterprise Security（企業向け保護設定）](ENTERPRISE_SECURITY.md)" in reference
    assert "[Trust Boundary](docs/TRUST_BOUNDARY.md)" in readme
    assert "[Trust Boundary](TRUST_BOUNDARY.md)" in reference


def test_security_doc_defines_secret_incident_response() -> None:
    content = read_text(SECURITY_PATH)

    assert_contains_all(
        content,
        (
            "非公開チャネルで連絡",
            "private vulnerability reporting / Security Advisory",
            "gitleaks",
            "無効化 / rotation",
            "commit 履歴",
            "GitHub Actions logs",
            "やってはいけないこと",
            "`.gitleaks.toml` の allowlist で incident を隠す",
        ),
    )


def test_readme_and_reference_link_security_doc() -> None:
    readme = read_text(README_PATH)
    reference = read_text(REFERENCE_PATH)

    assert "[Security Policy](SECURITY.md)" in readme
    assert "[Security Policy](../SECURITY.md)" in reference


def test_trust_boundary_precedence_keeps_security_policy_above_user_instruction() -> None:
    content = read_text(TRUST_BOUNDARY_PATH)
    precedence_section = content.split("## 優先順位", maxsplit=1)[1].split(
        "## repo-scoped hooks の扱い",
        maxsplit=1,
    )[0]

    assert "enterprise / user-level security policy" in content
    assert "明示された user instruction" in content
    assert "repo-scoped hooks / Git hooks" in content

    assert precedence_section.index("enterprise / user-level security policy") < precedence_section.index(
        "明示された user instruction"
    )
