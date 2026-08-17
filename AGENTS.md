# AGENTS.md

## この repo での役割

この repo は、Copilot CLI plugin、skills / agents、repo bootstrap 資産を育てる母艦です。  
人間向けの README や docs と、AI 向けの instructions / skill / agent を同じ GitHub repo 上で保守します。

## Source of truth

- repo 全体の入口: [README.md](README.md)
- repo-wide の現在ルール: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- 用語の正本: [CONTEXT.md](CONTEXT.md)
- docs 全体の入口: [docs/README.md](docs/README.md)
- durable knowledge の入口: [docs/knowledge/README.md](docs/knowledge/README.md)
- 設計判断の理由: [docs/adr/README.md](docs/adr/README.md)
- 配布物の正本: `plugins/happy-core/`, `plugins/happy-coding/`

## 基本コマンド

```powershell
uv run python -m pytest -q
uv run ruff check .
uv run ty check .
```

変更範囲が局所なら、まず focused test を優先します。

## Boundaries

- `AGENTS.md` は cross-agent brief です。詳細 workflow は skill 側へ戻します。
- durable knowledge は GitHub artifact に残し、local session state や gist を正本にしません。
- gist は個人用の cheat sheet や小さな snippet 共有に限定し、repo 固有の issue detail や設計理由の保管先にはしません。
- `docs/knowledge/` は再利用する reference を置く場所であり、思考メモ置き場ではありません。
- skill は単一責務を保ち、複数工程を束ねる場合だけ薄い orchestration を使います。

## 迷ったとき

1. まず `.github/copilot-instructions.md` と `CONTEXT.md` を見る  
2. durable knowledge の置き場を迷ったら [docs/README.md](docs/README.md) と [docs/knowledge/README.md](docs/knowledge/README.md) を見る  
3. 理由を残すべき判断なら `docs/adr/` を検討する  
4. いまの差分に閉じた detail か、長期に再利用する knowledge かを分ける
