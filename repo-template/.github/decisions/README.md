# Technology Selection Decisions

This directory stores technology selection decisions and related architectural decisions.

## Structure

- `tech-selection/`: Technology (language, framework) selection records

## Format

Technology selection decisions should be recorded as Markdown files with naming:
- `YYYY-MM-DD-[project-name].md` (e.g., `2026-04-26-jis-handbook-checker.md`)

See `.copilot/copilot-instructions.md` for the complete template and process.

## Usage

1. When evaluating technology candidates, use the comparison template from `.copilot/copilot-instructions.md` > 「言語・フレームワーク選定」セクション
2. Document decision with signed approval (AI proposal + user confirmation)
3. Save to `tech-selection/` with date and project name
4. Reference in commits: "fix: Migrate to Node.js - see .github/decisions/tech-selection/2026-04-26-jis-handbook.md"

## Benefits

- **Traceability**: Decision history is auditable and traceable
- **Out-of-bounds detection**: If a similar project is proposed with different technology, alert user to review prior decision
- **Organizational learning**: Technology selection rationale is documented for future teams
