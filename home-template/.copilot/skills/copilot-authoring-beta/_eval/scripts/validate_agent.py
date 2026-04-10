#!/usr/bin/env python3
"""Custom agent markdown を Critical / Recommended check で検証する。"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TRIGGER_PATTERNS = (
    r"Use\s+when:",
    r"こんな\s*ときに\s*使う",
    r"次のような\s*ときに\s*使います",
    r"次のような\s*ときに\s*使用します",
)
ROLE_HEADINGS = ("Role", "役割")
NON_RESPONSIBILITY_HEADINGS = ("Non-Responsibilities", "非責務")
OUTPUT_HEADINGS = ("Output Shape", "出力の型")
PITFALL_HEADINGS = ("Pitfalls", "注意点")
COMPLETION_HEADINGS = ("Completion Criteria", "完了条件")
LEGACY_BOUNDARY_HEADINGS = ("権限境界",)
LEGACY_QUALITY_HEADINGS = ("品質基準",)
LEGACY_OUTPUT_HEADINGS = ("出力テンプレート",)
LEGACY_PROHIBITION_HEADINGS = ("禁止事項",)
LEGACY_MODE_HEADING_PATTERNS = (
    r"既定モード.*",
    r"求道者モード",
    r"先生モード",
)
RELATED_RESOURCE_MARKERS = ("Related Skills", "Shared Resources", "関連スキル", "共通リソース")
PRINCIPLES_HEADING_PATTERNS = (
    r"Principles",
    r".+\s+Principles",
    r"原則",
    r".+原則",
)
PROCESS_HEADING_PATTERNS = (
    r"Process",
    r".+\s+Process",
    r"プロセス",
    r".+プロセス",
)


@dataclass
class CheckResult:
    id: str
    label: str
    passed: bool
    details: str = ""


@dataclass
class ValidationReport:
    file_path: str
    level: str
    critical: list[CheckResult]
    recommended: list[CheckResult]
    critical_passed: bool
    recommended_pass_count: int
    recommended_total: int


def extract_frontmatter(content: str) -> dict[str, str]:
    """Markdown 文字列から frontmatter を抽出する。"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}

    lines = match.group(1).splitlines()
    data: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        plain = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not plain:
            i += 1
            continue

        key = plain.group(1)
        value = plain.group(2).strip()
        if value in {">", "|", ">-", "|-"}:
            folded: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                folded.append(lines[i].strip())
                i += 1
            data[key] = " ".join(part for part in folded if part).strip()
            continue

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


def get_section(content: str, headings: str | Iterable[str]) -> str | None:
    """候補見出しのいずれかに一致する H2 セクション本文を返す。"""
    heading_list = (headings,) if isinstance(headings, str) else tuple(headings)
    matches = [
        match
        for heading in heading_list
        if (
            match := re.search(
                rf"^##\s+(?:\d+\.\s+)?{re.escape(heading)}\s*$",
                content,
                re.MULTILINE,
            )
        )
    ]
    if not matches:
        return None

    match = min(matches, key=lambda item: item.start())
    start = match.end()
    next_heading = re.search(r"^##\s+.+$", content[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end].strip()


def get_section_by_patterns(content: str, patterns: Iterable[str]) -> str | None:
    """正規表現パターンのいずれかに一致する H2 セクション本文を返す。"""
    matches = [
        match
        for pattern in patterns
        if (
            match := re.search(
                rf"^##\s+(?:\d+\.\s+)?(?:{pattern})\s*$",
                content,
                re.IGNORECASE | re.MULTILINE,
            )
        )
    ]
    if not matches:
        return None

    match = min(matches, key=lambda item: item.start())
    start = match.end()
    next_heading = re.search(r"^##\s+.+$", content[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end].strip()


def bullet_lines(section: str | None) -> list[str]:
    """セクション本文から bullet 行だけを取り出す。"""
    if not section:
        return []

    bullets: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "+ ")):
            bullets.append(re.sub(r"^[-*+]\s+", "", stripped))
    return bullets


def has_trigger_phrase(text: str) -> bool:
    """description に trigger phrase が含まれるか判定する。"""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in TRIGGER_PATTERNS)


def has_title_heading(content: str) -> bool:
    """H1 タイトルが存在するか判定する。"""
    return re.search(r"^#\s+\S.+$", content, re.MULTILINE) is not None


def has_step_structure(section: str | None) -> bool:
    """プロセス section に step 構造があるか判定する。"""
    if section is None:
        return False
    return bool(
        re.search(r"^###\s+Step\s+\d+", section, re.IGNORECASE | re.MULTILINE)
        or re.search(r"^###\s*ステップ\s*\d+", section, re.MULTILINE)
    )


def has_legacy_mode_structure(content: str) -> bool:
    """師範 agent 系の mode-based 構成がそろっているか判定する。"""
    return all(
        get_section_by_patterns(content, (pattern,)) is not None
        for pattern in LEGACY_MODE_HEADING_PATTERNS
    )


def parse_tools(raw_value: str) -> list[str]:
    """tools frontmatter を緩やかに list 化する。"""
    if not raw_value:
        return []

    if "\n" in raw_value:
        tools = [re.sub(r"^-\s*", "", line.strip()) for line in raw_value.splitlines() if line.strip()]
        return [tool for tool in tools if tool]

    return [part.strip() for part in raw_value.split(",") if part.strip()]


def agent_file_stem(path: Path) -> str:
    """`*.agent.md` から agent 名部分を取り出す。"""
    suffix = ".agent.md"
    if path.name.endswith(suffix):
        return path.name[: -len(suffix)]
    return path.stem


def validate(path: Path, level: str) -> ValidationReport:
    """1 本の agent.md を検証して report を返す。"""
    content = path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(content)
    role = get_section(content, ROLE_HEADINGS)
    non_responsibility = get_section(content, NON_RESPONSIBILITY_HEADINGS)
    principles = get_section_by_patterns(content, PRINCIPLES_HEADING_PATTERNS)
    process = get_section_by_patterns(content, PROCESS_HEADING_PATTERNS)
    output_shape = get_section(content, OUTPUT_HEADINGS)
    pitfalls = get_section(content, PITFALL_HEADINGS)
    completion = get_section(content, COMPLETION_HEADINGS)
    legacy_boundary = get_section(content, LEGACY_BOUNDARY_HEADINGS)
    legacy_quality = get_section(content, LEGACY_QUALITY_HEADINGS)
    legacy_output = get_section(content, LEGACY_OUTPUT_HEADINGS)
    legacy_prohibitions = get_section(content, LEGACY_PROHIBITION_HEADINGS)
    tools = parse_tools(frontmatter.get("tools", ""))

    missing_standard_sections = [
        label
        for label, section in (
            ("役割", role),
            ("非責務", non_responsibility),
            ("原則", principles),
            ("プロセス", process),
            ("出力の型", output_shape),
            ("注意点", pitfalls),
            ("完了条件", completion),
        )
        if section is None
    ]
    has_legacy_modes = has_legacy_mode_structure(content)
    missing_legacy_sections = [
        label
        for label, section in (
            ("役割", role),
            ("mode 構成", "ok" if has_legacy_modes else None),
            ("権限境界", legacy_boundary),
            ("品質基準", legacy_quality),
            ("出力テンプレート", legacy_output),
            ("禁止事項", legacy_prohibitions),
        )
        if section is None
    ]
    has_supported_structure = (
        not missing_standard_sections or not missing_legacy_sections
    )
    structure_details = ""
    if not has_supported_structure:
        standard_details = ", ".join(missing_standard_sections)
        legacy_details = ", ".join(missing_legacy_sections)
        structure_details = (
            f"standard missing: {standard_details}; legacy missing: {legacy_details}"
        )

    critical = [
        CheckResult(
            "C1",
            "Frontmatter に必須項目がある",
            {
                "name",
                "description",
                "tools",
                "model",
                "disable-model-invocation",
                "user-invocable",
            }
            <= frontmatter.keys(),
        ),
        CheckResult(
            "C2",
            "name がファイル名と一致する",
            frontmatter.get("name") == agent_file_stem(path),
            f"file={agent_file_stem(path)}",
        ),
        CheckResult("C3", "description に trigger phrase が入っている", has_trigger_phrase(frontmatter.get("description", ""))),
        CheckResult("C4", "必須 section がそろっている", has_supported_structure, structure_details),
        CheckResult(
            "C5",
            "プロセスまたは legacy mode 構造がある",
            has_step_structure(process) or has_legacy_modes,
        ),
    ]

    recommended = [
        CheckResult("R1", "役割が 2-6 個の bullet で書かれている", 2 <= len(bullet_lines(role)) <= 6, f"count={len(bullet_lines(role))}"),
        CheckResult(
            "R2",
            "非責務が 1-5 個の bullet で書かれている",
            1 <= len(bullet_lines(non_responsibility)) <= 5,
            f"count={len(bullet_lines(non_responsibility))}",
        ),
        CheckResult("R3", "tools が空でない", bool(tools), f"tools={tools!r}"),
        CheckResult(
            "R4",
            "なぜ効くかの説明がある",
            any(term in content.lower() for term in ("why", "because")) or any(term in content for term in ("なぜ", "理由")),
        ),
        CheckResult("R5", "注意点に bullet がある", bool(bullet_lines(pitfalls))),
        CheckResult("R6", "完了条件に bullet がある", bool(bullet_lines(completion))),
        CheckResult("R7", "関連リソースへの導線がある", any(marker in content for marker in RELATED_RESOURCE_MARKERS)),
        CheckResult("R8", "H1 タイトルがある", has_title_heading(content)),
        CheckResult("R9", "agent.md がコンパクトに保たれている", len(content.splitlines()) <= 220, f"lines={len(content.splitlines())}"),
    ]

    critical_passed = all(check.passed for check in critical)
    if level.upper() == "L1":
        recommended = []

    return ValidationReport(
        file_path=str(path),
        level=level.upper(),
        critical=critical,
        recommended=recommended,
        critical_passed=critical_passed,
        recommended_pass_count=sum(1 for check in recommended if check.passed),
        recommended_total=len(recommended),
    )


def parse_args() -> argparse.Namespace:
    """CLI 引数を定義して返す。"""
    parser = argparse.ArgumentParser(description="custom agent markdown を検証する")
    parser.add_argument("path", help="*.agent.md のパス")
    parser.add_argument("--level", choices=["L1", "L2"], default="L2")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON 形式で出力する")
    return parser.parse_args()


def print_text(report: ValidationReport) -> None:
    """検証結果を人間向けのテキスト形式で表示する。"""
    print(f"Validation: {report.file_path}")
    print(f"Level: {report.level}")
    print(f"Critical: {'PASS' if report.critical_passed else 'FAIL'}")

    print("\nCritical checks:")
    for check in report.critical:
        marker = "PASS" if check.passed else "FAIL"
        suffix = f" ({check.details})" if check.details else ""
        print(f"  - [{marker}] {check.id} {check.label}{suffix}")

    if report.recommended:
        print(f"\nRecommended: {report.recommended_pass_count}/{report.recommended_total}")
        for check in report.recommended:
            marker = "PASS" if check.passed else "WARN"
            suffix = f" ({check.details})" if check.details else ""
            print(f"  - [{marker}] {check.id} {check.label}{suffix}")


def main() -> int:
    """CLI entry point。"""
    args = parse_args()
    report = validate(Path(args.path), args.level)
    if args.json_output:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0 if report.critical_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
