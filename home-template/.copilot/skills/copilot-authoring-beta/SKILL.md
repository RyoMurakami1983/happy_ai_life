---
name: copilot-authoring-beta
description: >
  Copilot の custom skill と agent の作成・改善・検証を 1 つの入口にまとめる。
  Use when: skill / agent を新規作成したいとき、既存定義を育てたいとき、公開前に品質を確かめたいとき。
compatibility: "skill, create-agents, _eval/scripts/validate_agent.py"
---

# Copilot authoring を進める

Skill と Agent はどちらも「Copilot に何をどう任せるか」を定義する資産ですが、設計の単位と検証観点は同じではありません。この skill は入口だけを 1 本化し、対象に応じて適切な authoring ルートへ分けるための router です。入口を 1 つにする理由は、会話の途中で「新規作成 → 改善 → 検証」へ自然に遷移しても、同じ文脈のまま扱えるようにするためです。

## こんなときに使う

- 新しい custom skill を `home-template/.copilot/skills/` に追加したいとき
- 新しい custom agent を `home-template/.copilot/agents/` に追加したいとき
- 既存の skill / agent の説明、境界、検証導線を改善したいとき
- 公開や sync の前に authoring 資産の品質を確かめたいとき

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| 新しい skill を作る | `sub_skills/new-skill/` | scope、trigger、構造を決め、既存 template と validator を使って立ち上げる。 |
| 新しい agent を作る | `sub_skills/new-agent/` | 役割境界、model、tools を決め、agent template から起こす。 |
| 既存の skill / agent を改善する | `sub_skills/improve-existing/` | evidence を読み、説明・境界・関連資料を同期して磨き直す。 |
| 変更を出荷前に検証する | `sub_skills/validate-authoring/` | skill は既存 validator、agent は同梱 validator で構造確認する。 |

## ワークフロー: authoring を進める

### ステップ 1 — 対象と変更の種類を切り分ける

まず対象が skill か agent か、新規作成か改善か、構造確認かを分けます。ここを混ぜると、skill に必要な routing 設計と、agent に必要な責務境界の議論がぶつかりやすくなるためです。

### ステップ 2 — 既存資産を再利用する

skill では `skill` の template / validator、agent では `create-agents` の template を優先して使います。理由は、新しい入口を作っても下位の型まで独自化すると、将来の修正箇所が増えてメンテナンスが難しくなるからです。

### ステップ 3 — create / improve / validate の順で進める

新規作成でも改善でも、最後は検証に戻します。authoring 資産は prose が中心なので、書けたかどうかより「発見できるか」「境界が明確か」「次の利用者が迷わないか」を確かめることが重要です。

## 共通リソース

- `../skill/` — skill authoring の既存 router と sub-skill 群
- `../skill/_foundation/CONVENTIONS.md` — naming / frontmatter / writing style
- `../create-agents/` — agent authoring の既存 workflow
- `../create-agents/references/agent-template.md` — agent 定義の雛形
- `./_eval/scripts/validate_agent.py` — agent markdown の構造 validator

## 注意点

- **built-in と競合する名前を新設しない**: `/plan` `/review` `/research` `/session` と紛らわしい 1 語名は、到達性より混乱を増やします。
- **router を重くしすぎない**: 実行手順を親に詰め込むと、sub-skill の役割が消えて入口の価値が落ちます。
- **Skill と Agent を同じ観点で採点しない**: skill は workflow と routing、agent は責務と権限が主眼なので、同じ checklist を無理に当てないほうが保守しやすいです。
