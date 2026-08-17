# GitHub-first knowledge storage と agent entrypoint を採用する

**ステータス**: 承認

## 背景

この repo では、個人 PC と会社 PC をまたいだ継続利用、Copilot / agent の cross-session 利用、plugin / skill / docs の配布保守を同時に扱う。

既存方針として、local session continuity は標準運用から外し、repo 固有の事実は GitHub repo 内の docs / ADR / instructions に寄せる方向を取ってきた。  
一方で、docs 全体の入口、cross-agent 向けの `AGENTS.md`、GitHub-first knowledge の保存先がまだ明文化されていなかった。

加えて `happy-add-issue` では、公開 Issue の detail を gist に逃がす導線を一時的に許していた。  
これは「gist は個人用の cheat sheet や小さな snippet 共有であり、repo 固有の durable knowledge の正本ではない」という判断と衝突し始めた。

## 判断

- durable knowledge の正本は **GitHub repo 内の artifact** に置く
- repo 固有の再利用知識は `docs/knowledge/` に集約する
- 設計判断の理由は引き続き `docs/adr/` に残す
- repo-wide の現在ルールは `.github/copilot-instructions.md`、cross-agent brief は repo root の `AGENTS.md` に分ける
- `learnings` は会話ログではなく、短く一般化した再発防止ルールとして docs / instructions に書き戻す
- gist は個人用の cheat sheet や小さな snippet 共有に限定し、Issue の詳細メモや長い失敗ログの標準置き場にはしない
- 長い detail が必要な場合は、Issue を分割するか、`docs / ADR / follow-up Issue` のいずれかへ切り出す

## 根拠

- GitHub 公式は `copilot-instructions.md`、`AGENTS.md`、Issue、PR、repo docs をそれぞれ別責務で運用する方向を明示している
- Microsoft / GitHub の公開実践では、durable knowledge は ADR、repo docs、reviewable Markdown に寄っている
- gist は GitHub 上の共有手段ではあるが、repo の durable knowledge や設計理由の正本には向かない
- この repo の既存方針である instruction hierarchy、single responsibility、session continuity retirement と整合する

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| gist へ detail を逃がす | 一時的には軽い | durable knowledge が repo 外へ散る |
| Notion 等を正本にする | UI は見やすい | repo と AI の参照導線が分離する |
| **GitHub-first knowledge storage** | reviewable、versioned、cross-device に強い | docs の入口設計を自前で整える必要がある |

## 運用

- README は repo の入口、`docs/README.md` は docs の入口、`docs/knowledge/README.md` は durable knowledge の入口とする
- `AGENTS.md` は cross-agent brief とし、詳細 workflow を複製しない
- 新しい durable knowledge は、まず `docs/knowledge/` / `docs/adr/` / Issue / PR のどれに置くべきかを判断する
- `happy-add-issue` のような公開 Issue 導線では、gist を標準の detail escape hatch にしない

