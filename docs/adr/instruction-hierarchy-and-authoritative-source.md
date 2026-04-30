# Instruction 階層と正本の定義

**日付**: 2026-04-07
**ステータス**: 承認

## Amendment 2026-04-30: Copilot CLI plugin split と MCP config 撤退

- reusable skills / agents の公開・共有向け primary distribution は `plugins/happy-core/` と `plugins/happy-coding/` の Copilot CLI plugin とする。
- `mcp-config.json` は user-owned live file であり、この母艦 repo は MCP config sample を配布・初期化する layer として扱わない。
- 外部ドキュメント lookup が必要な場合は、Context7 を外部 Copilot CLI plugin として install する。MCP Registry や `mcp-config.sample.json` は skills / agents / instructions / hooks の primary distribution path にしない。

---

## 背景

Copilot CLI のカスタマイズは、以下のレイヤーに分散している。

| レイヤー | ファイル | 適用範囲 |
|----------|---------|---------|
| home instructions | `~/.copilot/copilot-instructions.md` | 全プロジェクト共通 |
| repo instructions | `<repo>/.github/copilot-instructions.md` | repo 固有 |
| path-specific instructions | `<repo>/.github/instructions/*.instructions.md` | 言語・ファイル種別固有 |
| agent | `~/.copilot/agents/*.agent.md` | 専門判断・改善・実践 |
| skill | `~/.copilot/skills/*/SKILL.md` | 必要時だけ読む詳細手順 |
| plugin | `~/.copilot/installed-plugins/...` | 公開・共有向け skills / agents 配布 |
| MCP | `~/.copilot/mcp-config.json` | user-owned な外部ツール接続設定（母艦 repo からは配布しない） |

現状の課題:
- 哲学の全文が `docs/PHILOSOPHY.md` に 443 行あり、instructions や agent 本文に要約が分散
- home と repo の instructions に一般原則（品質、テスト、セキュリティ等）が重複
- agent 本文に静的ルール（品質基準、ツールチェイン推奨）と動的判断が混在
- 「どの情報をどこに書くか」の判断基準が暗黙的で、追加時に重複が生まれやすい

## 判断

### 1. 情報種別ごとの正本（Authoritative Source）

| 情報種別 | 正本 | 補足 |
|----------|------|------|
| 開発哲学（全文） | GitHub profile README または個人管理文書 | repo 内に全文を複製しない |
| 個人の横断原則 | `~/.copilot/copilot-instructions.md` | 6 つの Value を行動原則に圧縮 |
| repo 固有の事実 | `<repo>/.github/copilot-instructions.md` | architecture, build/test, dispatch |
| 言語固有の規約 | `<repo>/.github/instructions/*.instructions.md` | 言語に閉じた局所ルール |
| 専門家の動的判断 | `~/.copilot/agents/*.agent.md` | 改善提案、レビュー、型の提示 |
| 詳細手順 | `~/.copilot/skills/*/SKILL.md` | 必要時だけ読み込む |
| 公開・共有向け reusable assets | `plugins/happy-core/`、`plugins/happy-coding/` | Copilot CLI plugin の curated package |
| 外部ツール接続 | live `~/.copilot/mcp-config.json` | user-owned。母艦 repo では sample を配布しない |
| 同期元テンプレート | `home-template/.copilot/`、`repo-template/.github/` | 母艦 repo が authoring source |

### 2. 競合時の優先順位（Precedence）

情報種別が競合した場合、以下の原則で解決する。

**原則: 責務を重ねず、競合しないように分離する。**

やむを得ず重なった場合の解決順:

| 競合パターン | 優先されるもの | 理由 |
|-------------|---------------|------|
| home vs repo（repo 固有の事実） | repo | repo が自分の事実を知っている |
| home vs repo（一般原則） | home に書き、repo は上書きしない | 一般原則は home に一元化 |
| repo-wide vs path-specific（言語規約） | path-specific が追加する | path-specific は repo-wide を前提に局所ルールを足す |
| instructions vs agent（静的ルール） | instructions | agent は動的判断に集中 |
| instructions vs skill（詳細手順） | skill | 常時読み込みの instructions には要約だけ |
| repo dispatch vs agent 本文の自己定義 | repo dispatch | 入口条件は repo が管理する |

### 3. 各レイヤーの責務（書くもの / 書かないもの）

#### home instructions（`~/.copilot/copilot-instructions.md`）

| 書くもの | 書かないもの |
|---------|------------|
| 出力言語・学習方針・優先言語 | 哲学全文 |
| 横断的な行動原則（Value 圧縮版） | repo 固有の architecture |
| agent 委譲の一般原則 | repo 固有の build/test コマンド |
| hooks の正本位置 | repo 固有の skills 名一覧 |
| | 言語別詳細ルール |
| | 外部 tool/plugin 接続設定 |

#### repo instructions（`<repo>/.github/copilot-instructions.md`）

| 書くもの | 書かないもの |
|---------|------------|
| repo の architecture | 哲学全文 |
| build/test/validation | 6 つの Value の長文説明 |
| skill/agent dispatch（実在する名前のみ） | C#/Python/TS の詳細 style |
| 完了条件 | home agent 専用の内輪メモ |
| .NET guardrail（該当 repo のみ） | 外部 tool/plugin の接続 JSON 本文 |
| docs 更新条件 | |
| コミット・PR 方針 | |

#### path-specific instructions（`*.instructions.md`）

| 書くもの | 書かないもの |
|---------|------------|
| 言語固有の style / type / async 方針 | dispatch ルール（`planner を呼べ`等） |
| テスト方針（言語固有部分） | agent/skill 名一覧 |
| エラーハンドリング（言語固有部分） | repo-wide と同じ一般原則 |
| | 外部 tool/plugin 名一覧 |

#### agent（`*.agent.md`）

| 書くもの | 書かないもの |
|---------|------------|
| 専門分野の判断基準 | 長い静的規約一覧 |
| 改善時の優先順位 | 外部 tool/plugin 接続 JSON |
| 出力テンプレート | 導入候補・将来拡張の棚卸し |
| 権限境界 | 哲学全文の転載 |
| 検証方針 | |

#### skill（`*/SKILL.md`）

| 書くもの | 書かないもの |
|---------|------------|
| 詳細手順（状況依存） | 常時必要な短いルール |
| ワークフロー | repo の architecture の事実 |
| チェックリスト | 最終出力言語 |
| トラブルシューティング | |

#### plugin（`plugins/happy-core/`、`plugins/happy-coding/` / installed plugin）

| 書くもの | 書かないもの |
|---------|------------|
| 公開・共有向け reusable skills / agents | repo-local instructions / hooks |
| plugin package の制約と install guidance | user-owned live config |

#### MCP（live `mcp-config.json`）

| 書くもの | 書かないもの |
|---------|------------|
| user-owned なサーバー接続設定 | 母艦 repo の配布テンプレート |
| ツール定義 | agent/skill の手順 |

## 根拠

- **Architect レビュー（2026-04-07）**: 「責務表だけでなく precedence 表が必要」「何をどこに書かないかをもっと強く定義しないと再び混線する」と指摘
- **既存パターンの延長**: 現在の分離は概ね正しいが、判断基準が暗黙的で重複が生まれやすい
- **トークン効率**: 常時読み込まれる instructions をスリムに保ち、詳細は必要時のみ skill で読み込む

## トレードオフ

- **利点**: 追加・変更時に「どこに書くか」を迷わない。重複検出が容易になる
- **リスク**: 厳格に分離しすぎると、文脈が分散して全体像が見えにくくなる
- **緩和策**: repo instructions に「いつどの skill/agent を使うか」のルーティング情報を集約し、ナビゲーションの中心とする
