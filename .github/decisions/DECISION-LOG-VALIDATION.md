# Decision Log Validation

This document describes the Decision Log validation feature integrated into session hooks.

## Purpose

The Decision Log validation system prevents unintended technology switches by comparing technology recommendations in the current session against prior decision records. This implements **A-2 countermeasure** from Issue #79: post-decision validation to detect out-of-bounds technology changes.

## How It Works

### 1. Session End Hook Integration

When a Copilot session ends, the `session-end.js` hook automatically:

1. **Extracts technologies** from the session summary (e.g., mentions of "Node.js", "C#", "Python", etc.)
2. **Searches for prior decisions** in `.github/decisions/tech-selection/` directory
3. **Compares** current session technologies against prior decisions
4. **Appends warnings** to the session file if mismatches are detected

### 2. Technology Detection

The validation automatically detects mentions of:

- **Languages**: Node.js, Python, C#/.NET, Go, Rust, Java, TypeScript
- **Frameworks**: React, Vue, Angular, Express, Python Framework (FastAPI, Django, Flask)

Detection is case-insensitive and works with common variations (e.g., "nodejs", "Node.js", "node.js").

### 3. Decision Log File Format

Decision Log files are stored in `.github/decisions/tech-selection/` directory.

**Naming**: `YYYY-MM-DD-project-name.md`

**Example Decision Log**:

```markdown
# Decision Log: JIS Handbook Checker

**Date**: 2026-04-22  
**Project**: JIS Handbook Checker  
**Status**: Approved

## Decision

### Technology Selected: C#

**Rationale**:
- Strong typing for domain-specific validation
- Cross-platform via .NET
- Good Kintone API support

### Trade-off Analysis

| Aspect | C# | Node.js | Python |
|--------|-----|---------|--------|
| Setup Time | 15 min | 5 min | 10 min |
| Implementation Lines | 300-400 | 500+ | 250-300 |
| Maintainability | High | Medium | High |
| Team Familiarity | High | Medium | Medium |

### Implementation Cost

- Initial setup: 15 minutes (install .NET SDK)
- Development time: ~2 hours for full feature set
- Testing time: ~30 minutes

## Why Not Node.js?

While Node.js has faster setup, the JSON manipulation and type safety benefits of C# outweigh the extra setup time given the project scope.

---

**Approver**: [name]  
**Link to Discussion**: [issue/PR link]
```

### 4. Validation Output

When a mismatch is detected, the session file includes a warning section:

```markdown
---

## Validation Warnings

### Technology Consistency

⚠️  Technology Consistency Warning
  Prior decision recorded (2026-04-20-jis.md): C#
  Current session mentions: Node.js
  Please review if this is an intentional change.
```

## Usage Guidelines

### Creating a Decision Log

1. **When**: After a technology selection decision is made and approved
2. **Where**: Create file in `.github/decisions/tech-selection/`
3. **Format**: Include "Technology Selected: [technology name]" line
4. **Content**: Document rationale, trade-offs, and implementation costs

### Reviewing Warnings

When a session ends with technology warnings:

1. **Evaluate**: Is the technology change intentional?
2. **Approve**: If intentional, update or create a new Decision Log
3. **Document**: Add notes to the session file explaining the change
4. **Commit**: Include decision rationale in the commit message

### Updating Decisions

To change a previously decided technology:

1. Create a **new** Decision Log file (don't modify the old one)
2. Include "Revised Decision:" section explaining the change
3. Document what changed and why
4. Update session file with the new decision reference

## Technical Details

### Validation Functions

- **`extractTechnologies(content)`**: Extracts technology names from text
- **`parseTechnologyFromDecisionLog(content)`**: Parses technology from Decision Log file
- **`findDecisionLogFiles(repoRoot)`**: Finds all Decision Log files in the repo
- **`validateTechnologyConsistency(content, repoRoot)`**: Main validation function

### Non-Blocking Design

- Validation is **soft** (warnings only, never blocks)
- Missing Decision Log directories are handled gracefully
- Malformed Decision Log entries are skipped (logged, not errored)
- Always exits with code 0

### Symlink Security

Decision Log files are checked for symlinks to prevent malicious redirects:

- Regular files are read normally
- Symlinks are skipped silently
- Absolute paths are used for all file operations

## Integration with Issue #79

This validation is part of addressing Issue #79: "Enhancement: copilot-instructions.md に技術選定フレームワークを追加"

The validation enables:

1. **Framework Compliance**: Ensures technology decisions follow documented tradeoff analysis
2. **Change Detection**: Alerts users to unintended technology switches
3. **Audit Trail**: Maintains records of technology decisions for future reference
4. **Learning**: Captures rationale for past decisions to guide future choices

## Related Files

- `.github/hooks/scripts/lib/decision-validation.js` - Validation logic
- `.github/hooks/scripts/session-end.js` - Hook integration
- `scripts/validate-session-hooks.js` - Test cases
- `.github/decisions/tech-selection/` - Decision Log directory (user-created)

## Examples

### Example 1: Decision with No Mismatch

**Prior Decision**: "Technology Selected: Node.js"  
**Session Mentions**: "Implemented Node.js endpoints"  
**Result**: ✅ No warning

### Example 2: Decision with Mismatch

**Prior Decision**: "Technology Selected: C#"  
**Session Mentions**: "Switched to Python for prototyping"  
**Result**: ⚠️ Warning appended to session file

### Example 3: Multiple Decision Files

**File 1** (2026-04-20): C# selected for backend  
**File 2** (2026-04-22): Python selected for data processing  
**Session Mentions**: Python (matches File 2)  
**Result**: ✅ No warning

## Troubleshooting

### Warning Not Appearing

1. Check if Decision Log directory exists: `.github/decisions/tech-selection/`
2. Verify Decision Log file contains "Technology" line
3. Ensure technology name matches detection patterns (case-insensitive)

### False Positive Warnings

If you're getting warnings for unrelated technology mentions (e.g., "research" mentions Python but session doesn't use it), you can:

1. Document the decision more clearly (be specific about what was chosen)
2. Use comments to clarify unrelated mentions
3. Update the session file manually to note intentional changes

### Adding New Technology

To detect a new technology:

1. Edit `.github/hooks/scripts/lib/decision-validation.js`
2. Add pattern to the `patterns` array in `extractTechnologies()`
3. Add test case to `scripts/validate-session-hooks.js`
4. Run tests to verify
