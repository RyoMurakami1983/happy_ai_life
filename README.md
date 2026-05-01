# happy_ai_life

> 楽しく AI と続ける仕事・学習・コーディングの型を、いつでもどこでも再現できるようにする。

Copilot CLI の reusable skills、agents、repo bootstrap 資産を管理する母艦リポジトリです。
詳細な背景は [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) を参照してください。

## 🚀 Quick Start

### Installation

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

✅ Setup complete. See [Getting Started](docs/GETTING_STARTED.md) for next steps.

## 📚 Documentation

| Purpose | Document |
|---------|----------|
| Full setup guide (3 paths) | [Getting Started](docs/GETTING_STARTED.md) |
| Local development environment | [Home Sync](docs/HOME_SYNC.md) |
| Add Copilot to your project | [Repo Bootstrap](docs/REPO_BOOTSTRAP.md) |
| Development workflow | [Development](docs/DEVELOPMENT.md) |
| Create skills & agents | [Authoring Guide](docs/AUTHORING.md) |
| Commands, skills, ADR index | [Reference](docs/REFERENCE.md) |
| Common issues & solutions | [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Frequently asked questions | [FAQ](docs/FAQ.md) |
| Design philosophy & values | [Philosophy](docs/PHILOSOPHY.md) |

## 🔧 For This Repository

This repository contains Copilot CLI plugin packages, bootstrap scripts, and quality tools.

To modify this repository:

1. **Design** — Use `/design-workshop` or design-workshop skill
2. **Plan** — Use PLAN mode for implementation breakdown
3. **Test** — Run quality checks before submitting PR

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

See [Development](docs/DEVELOPMENT.md) for full workflow details.

## ✅ Quality Gates

This repository uses GitHub Actions quality checks on every PR:

| Check | Tool |
|-------|------|
| Secret detection | gitleaks (always on) |
| Markdown lint | textlint (optional) |

See [Quality Gates](docs/QUALITY_GATES.md) for configuration and troubleshooting.

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
