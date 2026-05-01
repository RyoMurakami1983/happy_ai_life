# Authoring Guide: Creating Skills, Agents, and Instructions

This guide helps you create custom skills, agents, and instructions for Copilot CLI.

## Concepts

### Skills

Skills are reusable, self-contained tools that Copilot CLI can invoke:

- **Scope**: Single responsibility (perform one task well)
- **Distribution**: Packaged in plugins
- **Invocation**: `/skill run <skill-name>`
- **Example**: `initial-setup-happy-env`, `gh-pr-create`, `sdd`

**When to create:** You have a repeatable workflow that other developers need.

### Agents

Agents are autonomous systems that use multiple skills and maintain context:

- **Scope**: Multi-step problem solving
- **Invocation**: Launched as background or sync processes
- **State**: Can access conversation history
- **Example**: `explore` (code investigation), `code-review` (PR analysis), `tdd-coder` (Red-Green-Refactor)

**When to create:** You need a specialized task runner that reasons about complex problems.

### Instructions

Instructions provide persistent guidance to Copilot:

- **Repo-scoped**: `.github/copilot-instructions.md` (entire repo)
- **Path-scoped**: `.github/instructions/<language>.instructions.md` (specific files)
- **User-scoped**: `$HOME/.copilot/config.json` (personal environment)

**When to create:** You have coding standards, patterns, or conventions to enforce.

## Authoring Workflow

### 1. Design Phase

Use `/design-workshop` to explore your solution:

```powershell
copilot /design-workshop
```

This helps you:
- Define the problem clearly
- Explore multiple approaches
- Identify coupling and dependencies

### 2. Plan Phase

Use PLAN mode to break down implementation:

```powershell
copilot /plan
```

Create a structured plan with:
- Problem statement
- Approach overview
- Task breakdown
- Success criteria

### 3. Implement Phase

For complex tasks, use specialized agents:

```powershell
copilot /skill run tdd-coder  # For test-driven implementation
copilot /task agent-type tdd-coder  # For multi-turn implementation
```

### 4. Validate Phase

Use the `copilot-authoring` skill to validate your creation:

```powershell
copilot /skill run copilot-authoring
```

This checks:
- SKILL.md structure and completeness
- Configuration consistency
- Documentation clarity

### 5. Submit Phase

Create a PR with your new skill/agent/instructions:

```powershell
git add .
git commit -m "feat: add new <skill|agent|instructions>"
gh pr create
```

## Best Practices

### Skills

- **Clear scope**: One responsibility per skill
- **SKILL.md**: Document the "When to use" section clearly (this helps Copilot decide when to invoke it)
- **Testing**: Include test cases in `_eval/tests/` directory
- **Naming**: Use kebab-case and keep names short (e.g., `gh-pr-create`, not `github_pull_request_create`)
- **Versioning**: Follow semantic versioning in manifest

### Agents

- **Specialization**: Build narrow specialists, not general-purpose agents
- **Context limit**: Consider token budget and conversation history limits
- **Error handling**: Implement graceful fallbacks for API failures
- **Logging**: Log key decisions for debugging

### Instructions

- **Target audience**: Be explicit ("For this repository" vs "For Python developers" vs "For all users")
- **Specificity**: Provide concrete examples and commands
- **Maintenance**: Keep instructions up-to-date with code changes
- **Clarity**: Use clear language and avoid jargon

## Structure Template

### Skill structure

```
skills/your-skill/
├── SKILL.md               # Documentation & metadata
├── manifest.json          # Configuration
├── scripts/
│   └── main.py            # Skill logic
├── _eval/
│   ├── scripts/
│   │   └── validator.py   # Validation logic
│   └── tests/
│       └── test_*.py      # Test cases
```

### Agent structure

```
agents/your-agent/
├── AGENT.md               # Documentation
├── manifest.json          # Configuration
├── scripts/
│   └── main.py            # Agent logic
├── requirements.txt       # Python dependencies
└── tests/
    └── test_*.py          # Test cases
```

## See also

- [Development](DEVELOPMENT.md)
- [Reference](REFERENCE.md)
- [Quality Gates](QUALITY_GATES.md)
