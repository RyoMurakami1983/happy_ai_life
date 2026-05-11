from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_LOCAL_SKILL_ROOTS = (
    ROOT_DIR / ".github" / "skills",
    ROOT_DIR / ".agents" / "skills",
    ROOT_DIR / ".claude" / "skills",
    ROOT_DIR / "repo-template" / ".github" / "skills",
)


def iter_repo_local_skill_files() -> list[Path]:
    skill_files: list[Path] = []
    for root in REPO_LOCAL_SKILL_ROOTS:
        if root.exists():
            skill_files.extend(sorted(root.glob("**/SKILL.md")))
    return skill_files


def extract_frontmatter(content: str) -> dict[str, object]:
    match = re.search(r"^\ufeff?[\r\n\s]*---\s*\n(.*?)\n---\s*(?:\n|$)", content, re.DOTALL)
    if not match:
        return {}

    loaded = yaml.safe_load(match.group(1))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise AssertionError("repo-local skill の frontmatter は YAML mapping である必要があります")
    return loaded


def parse_allowed_tools(raw_value: object) -> list[str]:
    if raw_value is None:
        return []

    if isinstance(raw_value, str):
        values = [raw_value]
    elif isinstance(raw_value, list):
        values = raw_value
    else:
        raise AssertionError("repo-local skill の `allowed-tools` は string または list である必要があります")

    return [str(item).strip() for item in values if str(item).strip()]


def test_repo_local_skills_do_not_use_wildcard_allowed_tools() -> None:
    offenders: list[str] = []
    parse_failures: list[str] = []

    for skill_path in iter_repo_local_skill_files():
        content = skill_path.read_text(encoding="utf-8")
        try:
            frontmatter = extract_frontmatter(content)
            allowed_tools = parse_allowed_tools(frontmatter.get("allowed-tools"))
        except (yaml.YAMLError, AssertionError) as exc:
            parse_failures.append(f"{skill_path.relative_to(ROOT_DIR)}: {exc}")
            continue
        if "*" in allowed_tools:
            offenders.append(str(skill_path.relative_to(ROOT_DIR)))

    assert not parse_failures, (
        "repo-local skill frontmatter の解析に失敗しました: "
        + ", ".join(parse_failures)
    )
    assert not offenders, (
        "repo-local skill で `allowed-tools: \"*\"` は禁止です: "
        + ", ".join(offenders)
    )
