from __future__ import annotations

import re
from pathlib import Path


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


def extract_frontmatter(content: str) -> dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}

    lines = match.group(1).splitlines()
    data: dict[str, str] = {}
    i = 0
    while i < len(lines):
        plain = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", lines[i])
        if not plain:
            i += 1
            continue

        key = plain.group(1)
        value = plain.group(2).strip()
        if value == "":
            block: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                block.append(lines[i].strip())
                i += 1
            data[key] = "\n".join(part for part in block if part).strip()
            continue

        data[key] = value.strip('"\'')
        i += 1

    return data


def parse_allowed_tools(raw_value: str) -> list[str]:
    if not raw_value:
        return []

    if "\n" in raw_value:
        values = [re.sub(r"^-\s*", "", line.strip()) for line in raw_value.splitlines() if line.strip()]
    else:
        value = raw_value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
        values = [part.strip() for part in value.split(",") if part.strip()]

    return [item.strip('"\'') for item in values if item]


def test_repo_local_skills_do_not_use_wildcard_allowed_tools() -> None:
    offenders: list[str] = []

    for skill_path in iter_repo_local_skill_files():
        content = skill_path.read_text(encoding="utf-8")
        frontmatter = extract_frontmatter(content)
        allowed_tools = parse_allowed_tools(frontmatter.get("allowed-tools", ""))
        if "*" in allowed_tools:
            offenders.append(str(skill_path.relative_to(ROOT_DIR)))

    assert not offenders, (
        "repo-local skill で `allowed-tools: \"*\"` は禁止です: "
        + ", ".join(offenders)
    )
