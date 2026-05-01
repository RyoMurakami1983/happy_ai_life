# Frequently Asked Questions (FAQ)

## Installation and Setup

### Q: Do I need to install Copilot CLI first?

**A:** Yes. Copilot CLI is the runtime that executes all skills and agents. Install it from https://github.com/github/copilot-cli or use your package manager:

**macOS (Homebrew):**
```bash
brew install github/gh-copilot/gh-copilot
```

**Windows (Winget):**
```powershell
winget install GitHub.Copilot
```

### Q: Which installation path should I choose?

**A:** Choose based on your use case:

| Path | Best for | Complexity |
|------|----------|-----------|
| **Marketplace Plugin** | Using skills in your own projects | Easiest |
| **Local Development** | Contributing to this repo or customizing skills | Intermediate |
| **Repo Bootstrap** | Adding structure to your team's repository | Intermediate |

See [Getting Started](GETTING_STARTED.md) for detailed comparison.

### Q: Can I use multiple installation paths?

**A:** Yes! You can:
- Install via marketplace for public/shared use
- Install locally in home for personal customization
- Bootstrap into your project repo for team-wide standards

All three can work together.

## Distribution

### Q: What is the difference between marketplace install and direct install?

**A:** 

- **Marketplace Install** (recommended): Plugin installed from Copilot CLI marketplace. Updates through `copilot plugin install`. Default path for public/shared use.
- **Direct Install** (deprecated): Plugin installed directly from repository URL. No marketplace intermediary. Deprecated in newer Copilot CLI versions.

Use marketplace install for new setups.

### Q: Can I use both marketplace and direct install?

**A:** Not recommended. If you do, you'll see duplicate plugins. Uninstall the old version first:

```powershell
copilot plugin uninstall happy-ai-life
copilot plugin install happy-core@happy-ai-life-marketplace
```

## Home Sync vs Repo Bootstrap

### Q: What is home sync?

**A:** Home sync synchronizes your `$HOME/.copilot/` directory with the repository's `home-template/`. It's designed for trusted local author bootstrap—not for team sharing.

**Use it when:**
- You want to reproduce the author's personal setup
- You're contributing to the repository
- You want to customize skills for your personal use

See [Home Sync](HOME_SYNC.md) for details.

### Q: What is repo bootstrap?

**A:** Repo bootstrap adds Copilot guidance, Git hooks, and quality checks to a target repository. All changes are committed so the entire team uses the same setup.

**Use it when:**
- You want to enable Copilot guidance across your team
- You want to enforce quality checks (gitleaks, etc.)
- You want all developers to use consistent Git hooks

See [Repo Bootstrap](REPO_BOOTSTRAP.md) for details.

### Q: When should I use home sync vs repo bootstrap?

**A:**

| Scenario | Use |
|----------|-----|
| Personal environment setup | Home Sync |
| Contributing to happy_ai_life | Home Sync |
| Adding Copilot to your team project | Repo Bootstrap |
| Customizing skills for personal use | Home Sync |
| Enforcing team standards | Repo Bootstrap |

## Context7

### Q: Is Context7 included in happy_ai_life?

**A:** No. Context7 is an external plugin from Upstash. This repository does not include or distribute Context7.

### Q: How do I install Context7?

**A:** If you need Context7 for documentation lookups, install it as a separate Copilot CLI plugin:

```powershell
copilot plugin marketplace add upstash/context7
copilot plugin install context7-plugin@context7-marketplace
```

Get your API key from https://context7.com.

## Customization

### Q: Can I create custom skills?

**A:** Yes! See [Authoring Guide](AUTHORING.md) for step-by-step instructions on creating custom skills, agents, and instructions.

### Q: How do I customize instructions for my project?

**A:** Edit `.github/copilot-instructions.md` in your repository after bootstrap. Add your team's specific conventions, patterns, and guidance.

You can also add language-specific instructions in `.github/instructions/<language>.instructions.md`.

### Q: Can I share custom skills with others?

**A:** Yes. Follow the skill structure and package your skill as a Copilot CLI plugin. See [Authoring Guide](AUTHORING.md) for packaging details.

## Troubleshooting

### Q: My skills are not showing up in `/skill list`

**A:** Check:
1. Plugins are installed: `copilot plugin list`
2. Skills are available in the plugin: `copilot skill list <plugin-name>`
3. For local home sync, verify sync was applied: `uv run app.py home --dry-run`

See [Troubleshooting](TROUBLESHOOTING.md) for more solutions.

### Q: Git hooks are blocking my commits. How do I bypass them?

**A:** Don't bypass hooks—they're protecting your repository from secret leaks. Instead:

1. Find the secret flagged by gitleaks
2. Remove or obscure it
3. Retry the commit

If you absolutely must commit, you can temporarily disable hooks:

```powershell
git commit --no-verify  # NOT RECOMMENDED
```

But then run a manual scan:

```powershell
gitleaks detect --source . --verbose
```

## Support

### Q: Where can I report issues?

**A:** Report issues on GitHub: https://github.com/RyoMurakami1983/happy_ai_life/issues

Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Operating system and versions

### Q: How can I contribute?

**A:** See [Development](DEVELOPMENT.md) for contribution guidelines.

### Q: How do I stay updated?

**A:** Watch the repository for releases and updates. New skills and features are published to the marketplace regularly.

## See also

- [Getting Started](GETTING_STARTED.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Development](DEVELOPMENT.md)
