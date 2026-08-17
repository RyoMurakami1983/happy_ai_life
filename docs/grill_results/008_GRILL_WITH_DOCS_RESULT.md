# 008 GRILL WITH DOCS RESULT: GitHub-first knowledge storage へ寄せる

## 対象の目的

この repo の知識保存と AI 向け参照導線を、Notion / gist / local session 依存ではなく、GitHub 上の durable artifact を正本にする運用へ寄せる。

## 重要な判断軸

- **共有しやすさ**: 個人 PC / 会社 PC をまたいでも同じ knowledge を参照できること
- **責務分離**: Issue / PR / ADR / docs / instructions / AGENTS の役割を混ぜないこと
- **再現性**: 人間だけでなく AI agent も同じ導線で判断できること
- **保守性**: 入口を増やしすぎず、更新箇所が分かりやすいこと
- **安全性**: gist や session log に durable knowledge や private detail を逃がさないこと

## 役割と責任

- repo docs / ADR: durable knowledge と理由の正本
- `.github/copilot-instructions.md`: repo-wide の現在ルール
- `AGENTS.md`: 別 agent 向けの入口と境界
- skill docs: 単一責務の workflow 定義
- Issue / PR: 作業と差分のトレーサビリティ

## 例外・異常系

- gist は durable knowledge の保管先ではなく、小さな個人用 shared reference / snippet に限定する
- long log / detail を public issue の外へ逃がす既定は採らない
- Copilot Memory や local session state は補助であり、source of truth にしない

## 成功条件

- repo root に `AGENTS.md` が追加される
- `docs/README.md` と `docs/knowledge/` の入口ができる
- GitHub-first knowledge storage の判断理由が docs / ADR / instructions に反映される
- `happy-add-issue` から gist を durable detail の逃がし先として案内しない
- 関連 docs / tests が新方針を固定する

## 失敗条件

- AGENTS / docs / skills で役割が重複する
- durable knowledge の正本が gist や会話ログのまま残る
- `docs/knowledge/` を作っても README / instructions から辿れない
- 既存の単一責務方針と矛盾する

## 事実 / 解釈 / 未確認

### 事実

- 既存 repo には `.github/copilot-instructions.md`、`CONTEXT.md`、複数の ADR がある
- `AGENTS.md` はまだ存在しない
- gist 併用の案内は `happy-add-issue` に存在する
- `docs/` の全体 index はまだ存在しない

### 解釈

- この repo はすでに GitHub-first 運用へかなり寄っており、最後の運用導線を固める段階にある
- 追加すべき最小セットは `AGENTS.md`、`docs/README.md`、`docs/knowledge/`、issue skill wording fix で足りる

### 未確認

- `docs/knowledge/` の初期ノードをどこまで作るか
- GitHub-first knowledge policy を新規 ADR にするか、既存 ADR 追記で済ませるか

## 次工程への引き継ぎ

- [design: 008_TECHNICAL_DESIGN.md](../design/008_TECHNICAL_DESIGN.md)
- [plan: 008_PLAN_DONE.md](../plan/008_PLAN_DONE.md)
- [grill index](README.md)
