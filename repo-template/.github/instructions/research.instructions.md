---
description: Research 向けの追加ルール
applyTo: "**"
---

# Research instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは調査タスクだけに効く追加ルールを定義する。
- 調査は `deep-research-preflight` を入口にして `deep-researcher` に寄せる。
- 根拠の優先順位は `repo 内 source of truth` → `GitHub official docs` → `Context7` → `その他の公開資料` とする。
- GitHub / Copilot / MCP / Actions のように仕様が変わりやすい領域は official docs を優先し、Context7 は補助情報として使う。
- 結論は `事実` / `推論` / `未確認事項` に分け、曖昧さを埋めない。
- `architect` は技術中立の構造判断に集中させ、研究で得た個別 API の詳細に引きずらない。
