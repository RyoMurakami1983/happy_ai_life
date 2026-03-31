# Agent ディスパッチルールの導入

**日付**: 2026-03-31
**ステータス**: 承認
**Issue**: #13

---

## 背景

`home-template/.copilot/agents/` に 4 つの custom agent（planner, architect, deep-review, performance-optimizer）が存在するが、LLM が自動的に呼び出す場面が確認できていなかった。

### 調査で判明したこと

Copilot CLI のディスパッチメカニズムには以下の非対称性がある。

| 対象 | メカニズム | 自動ディスパッチ |
|------|-----------|-----------------|
| **Skill** | `<available_skills>` としてシステムプロンプトに一覧が注入される。「When a skill is relevant, you must invoke this tool IMMEDIATELY」という強い指示が組み込み済み | ✅ あり |
| **Agent** | `task` tool の `agent_type` 一覧に表示される。しかし「proactively invoke」のような自動ディスパッチ指示はシステムプロンプトに存在しない | ❌ なし |

Skills は自動ディスパッチ機構が組み込まれているため、description の `Use when:` が効く。
Agents はこの機構がないため、description だけでは LLM が自発的に呼び出さない。

## 判断

`copilot-instructions.md` に Agent ディスパッチルールを明示的に追加する。

### 対象ファイル

| ファイル | 役割 | 変更内容 |
|---------|------|---------|
| `home-template/.copilot/copilot-instructions.md` | 個人設定（全リポジトリに適用） | Agent ディスパッチセクション追加 |
| `.github/copilot-instructions.md` | 母艦リポジトリ固有 | 同上 |
| `repo-template/.github/copilot-instructions.md` | 配布テンプレート | 同上（agent 配置先の注記付き） |

### ルールの設計方針

- Skill の既存ディスパッチルール（「ふりかえり」→ furikaeri-practice、「DeepReview」→ deep-review-preflight）と同じ文体・粒度で統一する
- Agent は `task` tool の `agent_type` で呼び出す方式を明記する
- 「ユーザーの明示的な依頼がなくても条件合致で活用する」ことを指示する
- built-in agent より custom agent を優先する旨を明記する

## 根拠

- **既存パターンの踏襲**: Skills のディスパッチルール（キーワードトリガー方式）が実績あり。同じパターンを Agents にも適用する
- **最小変更**: 新しいファイル形式やメカニズムを導入せず、既存の instructions に追記するだけ
- **Skills との一貫性**: description の `Use when:` フィールドは Skills では自動ディスパッチに効くが、Agents では効かない。この差を instructions で補完する

## トレードオフ

- **得るもの**: LLM が状況に応じて適切な Agent を自動的に活用するようになる
- **失うもの**: instructions のトークン消費が微増する（約 200 トークン）
- **検討した代替案**:
  - (A) description の改善のみ → Agent にはシステムレベルの自動ディスパッチ機構がないため不十分
  - (B) 専用 `.instructions.md` 新設 → 管理ファイルが増え、既存パターンから逸脱する
  - (C) hooks で制御 → preToolUse 以外 output が Ignored のため技術的に不可能

## 余白

- 新しい Agent の追加（tdd-guide, security-reviewer 等）は別 issue で検討する
- `task` tool による並列 agent 実行のガイダンスは、基本ルールの効果確認後に追加を検討する
- VS Code Copilot Chat と CLI でのディスパッチ挙動の差異は継続調査とする
