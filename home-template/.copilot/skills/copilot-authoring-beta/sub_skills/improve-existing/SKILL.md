---
name: improve-existing
description: >
  既存の skill または agent を evidence ベースで改善する。Use when:
  wording、責務境界、関連資料、検証導線の弱さを直したいとき。
compatibility: "../../../skill/sub_skills/improve/SKILL.md, ../../../create-agents/SKILL.md"
---

# 既存の authoring 資産を改善する

この sub-skill は、すでに存在する skill / agent を実使用の違和感や review 結果に基づいて磨き直すための入口です。改善で重視するのはルールの追加ではなく、なぜその guidance が効くかを保ったまま余分な摩擦を減らすことです。

## こんなときに使う

- 既存 skill の trigger や router が弱く、起動精度を上げたいとき
- 既存 agent の責務や非責務が曖昧で、境界を明確にしたいとき
- 参考資料や bundled asset が本体とずれてきたとき
- 検証導線や README の説明を更新して利用しやすくしたいとき

## ワークフロー: 既存資産を改善する

### ステップ 1 — 対象と変更種別を分類する

対象が skill か agent か、変更が wording か behavior か、境界修正かを分けます。ここを分ける理由は、関連して直すべき面が対象ごとに異なるからです。

### ステップ 2 — 根拠を読む

review comment、利用 transcript、validation 結果、周辺 docs のずれを読みます。単発の違和感より、複数回再発している friction を優先して直すほうが効果的です。

### ステップ 3 — いちばん近い正本を直す

skill なら `description`、workflow、references、router を見直し、agent なら frontmatter、役割、非責務、プロセスを見直します。なぜ正本を先に直すかというと、派生資料だけ直すと次回の変更で再び崩れるためです。

### ステップ 4 — 周辺の dispatch と説明を同期する

境界や入口名が変わる場合は README や関連 skill の導線も合わせます。入口だけ直って周辺が古いままだと、利用者体験は改善しません。

### ステップ 5 — 検証ルートへ戻す

改善後は `../validate-authoring/` に戻し、skill / agent それぞれの validator で骨格を再確認します。改善は「書き換えたこと」ではなく「再び使っても迷わないこと」で完了です。

## 早見表

| 対象 | 主に見るもの |
| --- | --- |
| Skill | trigger、workflow、route、references |
| Agent | 役割、非責務、model、tools、出力の型 |
| 共通 | README、関連 docs、validation 導線 |

## 共通リソース

- `../../../skill/sub_skills/improve/` — skill 改善の既存導線
- `../../../create-agents/` — agent 側の元 workflow
- `../validate-authoring/` — 改善後の再検証

## 注意点

- **1 件の失敗に過剰適合しない**: 単発の transcript だけで決めると、全体の再利用性を落としやすいです。
- **周辺導線の同期を忘れない**: README や router が古いと、本体だけ直しても利用者は迷います。
- **責務の重なりを放置しない**: skill / agent の overlap は、時間が経つほど直しにくくなります。
