# Development: Contributing to happy_ai_life

<!-- TODO: 詳細な開発ガイドを記述
構成：
- このリポジトリの構成
- Skill / Agent / Instructions の作成ガイド
- Build / Test / Quality コマンド
- PR / Commit 作成プロセス
- Secret protection の 5 層
- Session continuity と furikaeri

参考: 現在の README の「Development」セクション（149-213行）
-->

## Repository Overview

This repository contains:
- `plugins/happy-core/` — Core Copilot CLI plugin (workflow, authoring, GitHub ops)
- `plugins/happy-coding/` — Coding Copilot CLI plugin (spec, design, impl, review)
- `scripts/` — Sync and bootstrap scripts
- `home-template/` — Local author bootstrap template
- `repo-template/` — Target repo bootstrap template

## Development Workflow

### Design

Use `/design-workshop` or the design-workshop skill.

### Plan

Use PLAN mode for implementation breakdown.

### Test

Run quality checks before submitting PR:

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

## Build and Test Commands

<!-- TODO: 詳細な build/test コマンド -->

## Quality Gates

<!-- TODO: 品質ゲートの詳細 -->

## Creating Skills, Agents, and Instructions

<!-- TODO: Authoring Guide へのリンク -->

See [Authoring Guide](AUTHORING.md) for details.

## Git Workflow

<!-- TODO: Commit / PR 作成プロセス -->

## Security

<!-- TODO: 5 層セキュリティ戦略 -->

## Session Continuity

<!-- TODO: furikaeri スキルについて -->

## See also

- [Authoring Guide](AUTHORING.md)
- [README](../README.md)
