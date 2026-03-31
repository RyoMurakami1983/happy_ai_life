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

---

## 補遺: ディスパッチ強化（2026-03-31）

### 公式ドキュメントの発見

GitHub 公式ドキュメント（[Invoking custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli-agents/invoke-custom-agents)）に以下の記述を確認：

> "The AI model being used by the CLI can choose to delegate a task to a subsidiary subagent process, that operates using a custom agent with specific expertise, if it judges that this would result in the work being completed more effectively."

つまり **モデルが description を見て自律的に agent を選択する機構は公式に存在する**。ただし以下の条件が揃わないと発動しない。

### なぜ発動しなかったか（根本原因分析）

| # | 原因 | 影響度 | 解決可能性 |
|---|------|--------|-----------|
| 1 | Agent に Skills 同等のシステムレベル自動ディスパッチ指示（`IMMEDIATELY invoke`）がない | 最大 | ❌ CLI 仕様 |
| 2 | description が「スタイル」を説明し「能力差」を示していない — モデルが「自分でもできる」と判断 | 大 | ✅ description 改善 |
| 3 | `[[PLAN]]` モード等の system prompt 指示が copilot-instructions.md より優先される | 大 | △ 回避策のみ |
| 4 | ディスパッチルールが「〜したら呼び出す」の提案レベルで、禁止句がない | 中 | ✅ instructions 改善 |
| 5 | 日本語のみの description が英語 system prompt 内で認知精度が落ちる可能性 | 小〜中 | ✅ バイリンガル化 |

### 実施した改善

**copilot-instructions.md ディスパッチルール強化**（3箇所すべて）:

1. セクションタイトルに「（必須）」を付加
2. 冒頭で「なぜ agent に委譲するのか」の理由を明記
3. 各条件に「自分で〜しない」の禁止句を追加
4. 「自分でもできそう」は呼ばない理由にならない、という明示的な判断基準
5. planner を最初のルールに配置し、キーワードを拡張（「計画」「プラン」「plan」「ステップを整理」）

### 構造的限界（現時点で解決不可能）

| 問題 | 理由 | 現実的な対応 |
|------|------|------------|
| system prompt > instructions の優先度 | CLI の仕様。外部から変更不可 | instructions 内で最大限の強度を出す |
| `[[PLAN]]` モードとの競合 | system prompt レベルで計画生成を指示される | 禁止句で回避を試みる。最悪は `@planner` 明示指定 |
| Agent に Skills 同等の自動ディスパッチがない | CLI 組み込み機構の差異 | GitHub への Feature Request 余地あり |
| モデルの self-confidence | LLM の一般傾向 | 「agent のほうが優れている」シグナルを最大化する |

### 検証シナリオ

改善効果は以下のシナリオで定性的に確認する：

1. 「実装計画を考えて」→ planner が呼ばれるか
2. 「このコードの構造をどうすべきか」→ architect が呼ばれるか
3. 「ビルドが通らない」→ build-resolver が呼ばれるか
4. 「デッドコードを整理したい」→ refactor が呼ばれるか
5. 暗黙的なケース: 大きな機能依頼の中で計画フェーズが先に走るか

### 今後のアクション

- description のバイリンガル化（根本原因 #2, #5 への対応）は効果検証後に検討
- VS Code Copilot Chat と CLI でのディスパッチ挙動差異は継続調査
- GitHub に Agent 自動ディスパッチの Feature Request を検討
