# Knowledge Index

このディレクトリは、**GitHub-first knowledge storage** の入口です。  
local session state や gist ではなく、GitHub 上で長く再利用する knowledge をここへ整理します。

## 置くもの

- 何度も参照する運用知識
- durable な playbook
- troubleshooting の蓄積
- lessons を一般化した再発防止ルール
- 外部調査をこの repo 向けに圧縮した reference

## 置かないもの

- 一時的な会話ログ
- private detail を含む生ログ
- repo 固有の差分理由だけで完結する PR コメントの写し
- gist 前提の補助メモ

## ディレクトリ

- [context/](context/index.md) — durable knowledge で使う文脈と参照境界
- [playbooks/](playbooks/index.md) — 反復する運用手順
- [troubleshooting/](troubleshooting/index.md) — よくある詰まりどころと対処
- [lessons/](lessons/index.md) — learnings を再利用可能な形にした記録
- [references/](references/index.md) — 外部調査や比較結果の圧縮版

## 関連

- repo 全体の入口: [../../README.md](../../README.md)
- docs 全体の入口: [../README.md](../README.md)
- 設計判断の理由: [../adr/README.md](../adr/README.md)
- repo-specific rule: [../../.github/copilot-instructions.md](../../.github/copilot-instructions.md)
- cross-agent brief: [../../AGENTS.md](../../AGENTS.md)
