# Reference

日常で使うコマンドだけを置く索引です。

## plugin

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
copilot plugin list
```

## home sync

```powershell
uv run app.py home --dry-run
uv run app.py home
```

## team repo setup

```powershell
& $HOME\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath <path> -PolicyProfile HappyDefault -DryRun
& $HOME\.copilot\scripts\sync-to-repo.ps1 -TargetRepoPath <path> -PolicyProfile HappyDefault
& $HOME\.copilot\scripts\install-git-hooks.ps1 -TargetRepoPath <path>
```

## check

```powershell
uv run python -m pytest -q tests/test_app_smoke.py tests/test_plugin_manifest.py tests/test_secret_guard_minimal.py
uv run ruff check .
```

## 困ったとき

- [トラブルシューティング](TROUBLESHOOTING.md)
- [FAQ](FAQ.md)
