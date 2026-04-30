---
name: copilot-authoring
description: >
  Copilot の custom skill / agent / repository instructions の作成・改善・検証を
  1 つの入口にまとめる。Use when: skill / agent / repo-wide instructions /
  path-specific instructions を新規作成したいとき、既存定義を育てたいとき、公開前に品質を確かめたいとき。
compatibility: "skill, create-agents, _eval/scripts/validate_agent.py"
---

# Copilot authoring を進める

Skill と Agent はどちらも「Copilot に何をどう任せるか」を定義する資産ですが、設計の単位と検証観点は同じではありません。この skill は入口だけを 1 本化し、対象に応じて適切な authoring ルートへ分けるための router です。入口を 1 つにする理由は、会話の途中で「新規作成 → 改善 → 検証」へ自然に遷移しても、同じ文脈のまま扱えるようにするためです。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## 共通の改善型: 抽象 -> review -> 発展

skill / agent / hooks の改善では、いきなり具体実装へ入らず、まず変更の型を 3〜6 行で抽象化します。次にその抽象を review へ渡し、責務境界、入力、失敗時の扱い、共有先を見直してから具体へ降ろします。途中で閉じない改善種は、その時点で Issue 化して次回に回します。

### hooks を題材にした最小例

- `pre-commit` に secret guard を足したい、ではなく「Git client hooks で staged diff の secret 検査を前段に置く」と抽象化する。
- review では、hook の責務、同期先、失敗時の挙動、README との整合を先に確認する。
- 実装具体に入るのは、抽象化と review で形がそろった後だけにする。

## こんなときに使う

- 新しい custom skill を `plugins/happy-core/skills/` または `plugins/happy-coding/skills/` に追加したいとき
- 新しい custom agent を `plugins/happy-coding/agents/` に追加したいとき
- `.github/copilot-instructions.md` や `.github/instructions/*.instructions.md` を作りたいとき
- 既存の skill / agent / instructions の説明、境界、検証導線を改善したいとき
- 公開や sync の前に authoring 資産の品質を確かめたいとき
- skill / agent / hooks 改善の共通型を先に整えたいとき

## 判断表

| やりたいこと | ルート | 次にやること |
| --- | --- | --- |
| 新しい skill を作る | `sub_skills/new-skill/` | scope、trigger、構造を決め、既存 template と validator を使って立ち上げる。 |
| 新しい agent を作る | `sub_skills/new-agent/` | 役割境界、model、tools を決め、agent template から起こす。 |
| repo-wide / path-specific instructions を作る・直す | `sub_skills/instructions-authoring/` | repo-wide と path-specific の責務を分け、最小の rule と review checklist を整える。 |
| 既存の skill / agent を改善する | `sub_skills/improve-existing/` | evidence を読み、説明・境界・関連資料を同期して磨き直す。 |
| 変更を出荷前に検証する | `sub_skills/validate-authoring/` | skill は既存 validator、agent は同梱 validator で構造確認する。 |

## ワークフロー: authoring を進める

### ステップ 1 — 対象と変更の種類を切り分ける

まず対象が skill か agent か instructions か、新規作成か改善か、構造確認かを分けます。ここを混ぜると、skill に必要な routing 設計と、agent に必要な責務境界、instructions に必要な常駐 rule の設計がぶつかりやすくなるためです。

### ステップ 1.5 — 変更の型を抽象化する

改善なら、まず「何を変えるか」ではなく「どんな型の改善か」を短く書きます。たとえば hooks 追加なら、対象、責務、失敗時の扱い、共有先の 4 点を 3〜6 行で並べるだけで十分です。

### ステップ 2 — 既存資産を再利用する

skill では `skill` の template / validator、agent では `create-agents` の template、instructions では既存の `.github/copilot-instructions.md` と `.github/instructions/*.instructions.md` の責務分離を優先して使います。理由は、新しい入口を作っても下位の型まで独自化すると、将来の修正箇所が増えてメンテナンスが難しくなるからです。

### ステップ 3 — create / improve / validate の順で進める

新規作成でも改善でも、最後は検証に戻します。authoring 資産は prose が中心なので、書けたかどうかより「発見できるか」「境界が明確か」「次の利用者が迷わないか」を確かめることが重要です。

### ステップ 4 — その場で閉じるか Issue 化するかを決める

- その場で閉じる: 抽象化と review の時点で、既存資産の書き換えだけで済む
- Issue 化する: 変更先が複数にまたがる、別の review が必要、次回以降に再利用したい
- 迷うとき: まず小さく issue 化し、具体実装は次の着手点に残す

## 共通リソース

- `../skill/` — skill authoring の既存 router と sub-skill 群
- `../skill-eval/` — skill の behavioral eval（benchmark / empirical の 2 ルート）
- `../skill/_foundation/CONVENTIONS.md` — naming / frontmatter / writing style
- `../create-agents/` — agent authoring の既存 workflow
- `../create-agents/references/agent-template.md` — agent 定義の雛形
- `./_eval/scripts/validate_agent.py` — agent markdown の構造 validator
- `./sub_skills/instructions-authoring/` — repo-wide / path-specific instructions の authoring ルート
- `./sub_skills/improve-existing/` — 既存資産の改善ルート

## 注意点

- **built-in と競合する名前を新設しない**: `/plan` `/review` `/research` `/session` と紛らわしい 1 語名は、到達性より混乱を増やします。
- **router を重くしすぎない**: 実行手順を親に詰め込むと、sub-skill の役割が消えて入口の価値が落ちます。
- **Skill と Agent を同じ観点で採点しない**: skill は workflow と routing、agent は責務と権限が主眼なので、同じ checklist を無理に当てないほうが保守しやすいです。
- **instructions に手順を書き込みすぎない**: 常時読み込まれる rule には短い guidance だけを置き、詳細 workflow は skill へ逃がします。
